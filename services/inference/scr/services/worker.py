from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from scr.infra.redis import InferenceRedisRepository, PredictionConfigRepository
from scr.schemas.inference_request import InferenceBatchItem, InferenceResult, InferenceStreamMessage
from scr.schemas.inference_response import HealthResponse, ProcessBatchResponse
from scr.schemas.prediction_config import PredictionConfig
from scr.services.batch import BatchBuilder
from scr.services.model import ModelRegistry, Predictor
from scr.infra.config import settings
from math import hypot
from copy import deepcopy

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class WorkerSettings:
    batch_size: int = 32
    poll_interval_seconds: float = 1.0
    cells: int = 32
    heatmap_result_key: str = "heat_map"


class InferenceWorkerService:
    def __init__(
        self,
        redis_repository: InferenceRedisRepository,
        predictor: Predictor | None,
        batch_builder: BatchBuilder,
        worker_settings: WorkerSettings,
        config_repository: PredictionConfigRepository | None = None,
        model_registry: ModelRegistry | None = None,
    ) -> None:
        self._redis_repository = redis_repository
        self._predictor = predictor
        self._batch_builder = batch_builder
        self._worker_settings = worker_settings
        self._config_repository = config_repository
        self._model_registry = model_registry
        self._stop_event = asyncio.Event()

    async def health_check(self) -> HealthResponse:
        redis_ready = await self._redis_repository.health_check()
        model_ready = self._predictor is not None or self._model_registry is not None
        status = "ok" if redis_ready and model_ready else "degraded"
        return HealthResponse(
            status=status,
            redis_ready=redis_ready,
            model_ready=model_ready,
            details={
                "batch_size": self._worker_settings.batch_size,
                "poll_interval_seconds": self._worker_settings.poll_interval_seconds,
                "cells": self._worker_settings.cells,
                "heatmap_result_key": self._worker_settings.heatmap_result_key,
            },
        )

    async def process_once(self) -> ProcessBatchResponse:
        """
        Process one batch of inference requests.
        
        Returns:
            ProcessBatchResponse with statistics about the batch processing
        """
        if self._predictor is None and self._model_registry is None:
            return ProcessBatchResponse(
                processed_items=0,
                enqueued_results=0,
                details={"reason": "model is not configured"},
            )

        try:
            raw_records: list[InferenceStreamMessage] = await self._redis_repository.pop_raw_messages(self._worker_settings.batch_size)
            if not raw_records:
                return ProcessBatchResponse(
                    processed_items=0,
                    enqueued_results=0,
                    details={"reason": "no records in queue"},
                )

            logger.debug("Popped %d raw records from queue", len(raw_records))

            batch = self._batch_builder.build(raw_records)
            if not batch:
                logger.warning("No valid items in batch after building")
                return ProcessBatchResponse(
                    processed_items=0,
                    enqueued_results=0,
                    details={"reason": "no valid items after building"},
                )

            logger.debug("Built batch with %d items", len(batch))

            all_results: list[InferenceResult] = []
            try:
                for item in batch:
                    token = self._extract_token(item)
                    config = await self._get_prediction_config(token)
                    predictor = self._resolve_predictor(config)

                    try:
                        hero_pred = predictor.predict_proba([item.features])[0]
                    except Exception as e:
                        logger.error("Error during hero prediction for %s: %s", item.record_id, e)
                        hero_pred = 0.0

                    all_results.append(
                        InferenceResult(
                            record_id=item.record_id,
                            death_probability=hero_pred,
                            model_backend=str(predictor.backend_name),
                            metadata={
                                "square": item.features.get("square"),
                                "token": token,
                                "model": config.model,
                                "time": config.time,
                                "interval": config.interval,
                                "full_map": config.full_map,
                            },
                        )
                    )

                    cells = self._worker_settings.cells
                    xmin = getattr(settings, "XMIN", -9400)
                    xmax = getattr(settings, "XMAX", 8000)
                    ymin = getattr(settings, "YMIN", -8500)
                    ymax = getattr(settings, "YMAX", 8500)
                    meta = item.raw_payload.get("__meta__", {}) if isinstance(item.raw_payload, dict) else {}
                    tower_positions = meta.get("tower_positions", []) if isinstance(meta, dict) else []
                    is_radiant = bool(item.features.get("is_radiant", False))

                    def euclidean_distance(x1: float, y1: float, x2: float, y2: float) -> int:
                        return int(hypot(x1 - x2, y1 - y2))

                    def cell_center(col: int, row: int) -> tuple[float, float]:
                        cell_width = (xmax - xmin) / cells
                        cell_height = (ymax - ymin) / cells
                        cx = xmin + (col + 0.5) * cell_width
                        cy = ymin + (row + 0.5) * cell_height
                        return cx, cy

                    candidate_squares = self._get_candidate_squares(
                        square=item.features.get("square"),
                        cells=cells,
                        full_map=config.full_map,
                        interval=config.interval,
                    )

                    grid_features: list[dict[str, Any]] = []
                    grid_squares: list[int] = []
                    for square in candidate_squares:
                        row = square // cells
                        col = square % cells
                        cx, cy = cell_center(col, row)
                        grid_features.append(
                            self._recalculate_distance_features(
                                base_features=item.features,
                                x=cx,
                                y=cy,
                                square=square,
                                tower_positions=tower_positions,
                                is_radiant=is_radiant,
                                distance_fn=euclidean_distance,
                            )
                        )
                        grid_squares.append(square)

                    if grid_features:
                        try:
                            grid_preds = predictor.predict_proba(grid_features)
                        except Exception as e:
                            logger.exception("Grid prediction failed for %s: %s", item.record_id, e)
                            grid_preds = [0.0 for _ in grid_features]

                        heatmap_key = self._heatmap_key_for_token(token)
                        try:
                            # Rebuild the frame from scratch so squares that are not
                            # predicted in this tick are cleared instead of
                            # lingering from the previous heatmap.
                            heatmap = [[0.0 for _ in range(cells)] for _ in range(cells)]
                            for sq, pred in zip(grid_squares, grid_preds, strict=False):
                                if not isinstance(sq, int):
                                    continue
                                if sq < 0 or sq >= cells * cells:
                                    continue
                                r = sq // cells
                                c = sq % cells
                                heatmap[r][c] = float(pred)
                            await self._redis_repository.set_heatmap(heatmap_key, heatmap)
                        except Exception:
                            logger.exception("Failed updating heatmap for %s", item.record_id)

                # push single results (one per original record) to output stream
                await self._redis_repository.push_results(all_results)

                # Acknowledge processed stream messages
                try:
                    ids = [r.stream_id for r in raw_records]
                    await self._redis_repository.ack_messages(ids)
                except Exception:
                    logger.exception("Failed to ack stream messages")
            except Exception as e:
                logger.exception("Error during expanded grid processing: %s", e)
                return ProcessBatchResponse(
                    processed_items=len(batch),
                    enqueued_results=0,
                    details={"reason": f"grid processing failed: {str(e)}", "error": type(e).__name__},
                )

            logger.info("Processed %d items, enqueued %d results", len(batch), len(all_results))

            return ProcessBatchResponse(
                processed_items=len(batch),
                enqueued_results=len(all_results),
                details={
                    "backend": str(self._predictor.backend_name) if self._predictor is not None else "multi",
                    "batch_size": len(batch),
                },
            )
        except Exception as e:
            logger.exception("Unexpected error during process_once")
            return ProcessBatchResponse(
                processed_items=0,
                enqueued_results=0,
                details={"reason": "unexpected error", "error": type(e).__name__},
            )

    async def run_forever(self) -> None:
        """Run the inference worker loop indefinitely until stopped."""
        logger.info("Starting inference worker loop")
        iteration = 0
        
        while not self._stop_event.is_set():
            try:
                iteration += 1
                if iteration % 100 == 0:
                    logger.info("Inference worker running (iteration %d)", iteration)
                
                await self.process_once()
            except asyncio.CancelledError:
                logger.info("Worker loop cancelled")
                break
            except Exception:
                logger.exception("Unhandled exception during inference loop (iteration %d)", iteration)
            
            await asyncio.sleep(self._worker_settings.poll_interval_seconds)
        
        logger.info("Inference worker loop stopped after %d iterations", iteration)

    def stop(self) -> None:
        self._stop_event.set()

    async def _get_prediction_config(self, token: str) -> PredictionConfig:
        if self._config_repository is None:
            return PredictionConfig()
        return await self._config_repository.get_for_token(token)

    def _resolve_predictor(self, config: PredictionConfig) -> Predictor:
        if self._model_registry is not None:
            predictor = self._model_registry.resolve(config.model, config.time)
            if predictor is not None:
                return predictor

        if self._predictor is not None:
            return self._predictor

        raise RuntimeError("No predictor available")

    def _extract_token(self, item: InferenceBatchItem) -> str:
        raw_meta = item.raw_payload.get("__meta__", {}) if isinstance(item.raw_payload, dict) else {}
        if isinstance(raw_meta, dict):
            token = raw_meta.get("token")
            if isinstance(token, str) and token.strip():
                return token.strip()
        return "default"

    def _heatmap_key_for_token(self, token: str) -> str:
        if token == "default":
            return self._worker_settings.heatmap_result_key
        return f"{self._worker_settings.heatmap_result_key}:{token}"

    def _get_candidate_squares(self, square: int | None, cells: int, full_map: bool, interval: int) -> list[int]:
        if not isinstance(square, int) or square < 0 or square >= cells * cells:
            return list(range(cells * cells)) if full_map else []

        if full_map:
            return list(range(cells * cells))

        radius = max(0, (interval - 1) // 2)
        center_row = square // cells
        center_col = square % cells
        squares: list[int] = []
        for row in range(max(0, center_row - radius), min(cells, center_row + radius + 1)):
            for col in range(max(0, center_col - radius), min(cells, center_col + radius + 1)):
                squares.append(row * cells + col)
        return squares

    def _recalculate_distance_features(
        self,
        base_features: dict[str, Any],
        x: float,
        y: float,
        square: int,
        tower_positions: list[dict[str, Any]],
        is_radiant: bool,
        distance_fn: Any,
    ) -> dict[str, Any]:
        features = deepcopy(base_features)
        features["x"] = int(x)
        features["y"] = int(y)
        features["square"] = square

        for idx in range(1, 6):
            enemy_x = features.get(f"enemy_{idx}_last_seen_x")
            enemy_y = features.get(f"enemy_{idx}_last_seen_y")
            if isinstance(enemy_x, (int, float)) and isinstance(enemy_y, (int, float)):
                features[f"enemy_{idx}_last_seen_distance"] = distance_fn(x, y, float(enemy_x), float(enemy_y))
            else:
                features[f"enemy_{idx}_last_seen_distance"] = int(1_000_000)

        allied_towers: list[tuple[float, float]] = []
        enemy_towers: list[tuple[float, float]] = []
        for tower in tower_positions:
            tower_x = tower.get("x")
            tower_y = tower.get("y")
            tower_team = tower.get("team")
            if not isinstance(tower_x, (int, float)) or not isinstance(tower_y, (int, float)):
                continue

            if (is_radiant and tower_team == 2) or (not is_radiant and tower_team == 3):
                allied_towers.append((float(tower_x), float(tower_y)))
            else:
                enemy_towers.append((float(tower_x), float(tower_y)))

        if allied_towers:
            features["nearest_ally_tower_distance"] = min(distance_fn(x, y, tx, ty) for tx, ty in allied_towers)
        if enemy_towers:
            features["nearest_enemy_tower_distance"] = min(distance_fn(x, y, tx, ty) for tx, ty in enemy_towers)

        return features

    def _build_results(self, batch: list[InferenceBatchItem], predictions: list[float]) -> list[InferenceResult]:
        results: list[InferenceResult] = []
        for batch_item, prediction in zip(batch, predictions, strict=False):
            square = batch_item.features.get("square")
            results.append(
                InferenceResult(
                    record_id=batch_item.record_id,
                    death_probability=prediction,
                    model_backend=str(self._predictor.backend_name),
                    metadata={
                        "square": square,
                    },
                )
            )
        return results

    async def _update_heatmap(self, batch: list[InferenceBatchItem], predictions: list[float]) -> None:
        cells = self._worker_settings.cells
        heatmap = [[0.0 for _ in range(cells)] for _ in range(cells)]

        for batch_item, prediction in zip(batch, predictions, strict=False):
            square = batch_item.features.get("square")
            if not isinstance(square, int):
                continue
            if square < 0 or square >= cells * cells:
                continue

            row = square // cells
            col = square % cells
            heatmap[row][col] = float(prediction)

        await self._redis_repository.set_heatmap(self._worker_settings.heatmap_result_key, heatmap)