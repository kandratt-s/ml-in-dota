from __future__ import annotations

import logging
import pickle
from dataclasses import dataclass
from collections.abc import Sequence
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

import joblib

logger = logging.getLogger(__name__)


class Predictor(Protocol):
    backend_name: str

    def predict_proba(self, features: Sequence[dict[str, Any]]) -> list[float]:
        raise NotImplementedError


class ModelBackend(StrEnum):
    BOOSTING = "boosting"
    LOGREG = "logreg"


class SklearnPipelinePredictor:
    backend_name = ModelBackend.LOGREG

    def __init__(self, model: Any) -> None:
        self._model = model

    def predict_proba(self, features: Sequence[dict[str, Any]]) -> list[float]:
        try:
            import pandas as pd

            frame = pd.DataFrame(features)
            probabilities = self._model.predict_proba(frame)
            return [float(row[1]) for row in probabilities]
        except Exception as e:
            logger.exception("Error during logreg prediction with features: %s", features)
            raise RuntimeError(f"Logreg prediction failed: {e}") from e


class CatBoostPredictor:
    backend_name = ModelBackend.BOOSTING

    def __init__(self, model: Any) -> None:
        self._model = model
        self._categorical_features = [
            "hero_id",
            "enemy_1_name",
            "enemy_2_name",
            "enemy_3_name",
            "enemy_4_name",
            "enemy_5_name",
        ]

    def predict_proba(self, features: Sequence[dict[str, Any]]) -> list[float]:
        """
        Predict probabilities using CatBoost model.
        
        Note: This assumes features have been properly preprocessed to match
        the model's training schema. Feature alignment must be ensured before
        calling this method.
        """
        try:
            import pandas as pd

            from catboost import Pool

            frame = pd.DataFrame(features)

            for column in self._categorical_features:
                if column in frame.columns:
                    frame[column] = frame[column].astype("string")

            pool = Pool(frame, cat_features=[column for column in self._categorical_features if column in frame.columns])
            probabilities = self._model.predict_proba(pool)
            return [float(row[1]) for row in probabilities]
        except Exception as e:
            logger.exception("Error during CatBoost prediction with features: %s", features)
            raise RuntimeError(f"CatBoost prediction failed: {e}") from e


class ModelFactory:
    def __init__(self, model_path: Path | None) -> None:
        self._model_path = model_path

    def build_predictor(self) -> Predictor | None:
        if self._model_path is None:
            logger.warning("Model path is not configured; inference will stay disabled")
            return None

        if not self._model_path.exists():
            logger.error("Model file does not exist: %s", self._model_path)
            return None

        if self._model_path.is_dir():
            logger.error("Model path points to a directory, not a file: %s", self._model_path)
            return None

        if self._model_path.suffix.lower() == ".cbm":
            try:
                from catboost import CatBoostClassifier  # type: ignore
            except ImportError:
                logger.error("CatBoost is not installed, cannot load model: %s", self._model_path)
                return None

            try:
                model = CatBoostClassifier()
                model.load_model(str(self._model_path))
            except Exception as e:
                logger.error("Failed to load CatBoost model from %s: %s", self._model_path, e)
                return None

            logger.info("Loaded CatBoost model from %s", self._model_path)
            return CatBoostPredictor(model)

        try:
            if self._model_path.suffix.lower() == ".joblib":
                loaded_model = joblib.load(self._model_path)
            else:
                with self._model_path.open("rb") as file_handle:
                    loaded_model = pickle.load(file_handle)
        except Exception as e:
            logger.error("Failed to load model from %s: %s", self._model_path, e)
            return None

        if hasattr(loaded_model, "predict_proba"):
            logger.info("Loaded logreg pipeline from %s", self._model_path)
            return SklearnPipelinePredictor(loaded_model)

        logger.error("Unsupported model type: %s (file: %s)", type(loaded_model).__name__, self._model_path)
        return None


@dataclass(slots=True)
class ModelRegistry:
    predictors: dict[tuple[str, int], Predictor]
    default_key: tuple[str, int] = ("boosting", 10)

    def resolve(self, model_name: str, time: int) -> Predictor | None:
        predictor = self.predictors.get((model_name, time))
        if predictor is not None:
            return predictor

        fallback = self.predictors.get(self.default_key)
        if fallback is not None:
            logger.warning("Falling back to default predictor for model=%s time=%s", model_name, time)
        return fallback


class ModelRegistryFactory:
    SUPPORTED_TIMES = (1, 5, 10, 15, 20)

    def __init__(self, boosting_models_dir: Path, logreg_models_dir: Path) -> None:
        self._boosting_models_dir = boosting_models_dir
        self._logreg_models_dir = logreg_models_dir

    def build_registry(self) -> ModelRegistry:
        predictors: dict[tuple[str, int], Predictor] = {}

        for prediction_time in self.SUPPORTED_TIMES:
            boosting_path = self._boosting_models_dir / f"catboost_dota_model_{prediction_time}s.cbm"
            logreg_path = self._logreg_models_dir / f"dota_logreg_pipeline_{prediction_time}s.joblib"

            boosting_predictor = ModelFactory(boosting_path).build_predictor()
            if boosting_predictor is not None:
                predictors[("boosting", prediction_time)] = boosting_predictor

            logreg_predictor = ModelFactory(logreg_path).build_predictor()
            if logreg_predictor is not None:
                predictors[("logreg", prediction_time)] = logreg_predictor

        return ModelRegistry(predictors=predictors)