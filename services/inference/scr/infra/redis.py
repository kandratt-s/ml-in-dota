from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from redis.asyncio import Redis

from scr.schemas.inference_request import InferenceRecord, InferenceResult, InferenceStreamMessage
from scr.schemas.prediction_config import PredictionConfig

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RedisClient:
	client: Redis

	@classmethod
	def from_url(cls, redis_url: str) -> "RedisClient":
		return cls(client=Redis.from_url(redis_url, decode_responses=True))

	async def ping(self) -> bool:
		return bool(await self.client.ping())

	async def close(self) -> None:
		await self.client.close()
		await self.client.connection_pool.disconnect()


class InferenceRedisRepository:
	def __init__(
		self,
		client: RedisClient,
		input_queue_name: str,
		output_queue_name: str,
		consumer_name: str = "inference-worker",
	) -> None:
		self._client = client.client
		self._input_queue_name = input_queue_name
		self._output_queue_name = output_queue_name
		# Streams/group defaults
		self._group_name = f"{self._input_queue_name}:group"
		self._consumer_name = consumer_name

	async def health_check(self) -> bool:
		return bool(await self._client.ping())

	async def pop_raw_messages(self, batch_size: int) -> list[InferenceStreamMessage]:
		"""
		Pop raw messages from the input queue.
		
		Args:
			batch_size: Maximum number of messages to retrieve
			
		Returns:
			List of parsed JSON messages (dicts)
		"""
		# Ensure consumer group exists
		try:
			try:
				await self._client.xgroup_create(self._input_queue_name, self._group_name, id="0-0", mkstream=True)
			except Exception:
				# group may already exist
				pass

			entries = await self._client.xreadgroup(
				groupname=self._group_name,
				consumername=self._consumer_name,
				streams={self._input_queue_name: ">"},
				count=batch_size,
				block=1000,
			)
		except Exception as e:
			logger.error("Error reading from Redis stream: %s", e)
			return []

		# xreadgroup returns list of (stream, [(id, {k: v}), ...])
		messages: list[InferenceStreamMessage] = []
		for stream_name, items in entries:
			for item_id, fields in items:
				# messages were added with a single field 'data'
				raw = fields.get("data") or fields.get("message")
				if raw is None:
					logger.warning("Stream message without payload, skipping: %s", item_id)
					continue
				try:
					parsed = json.loads(raw)
				except json.JSONDecodeError:
					logger.warning("Invalid JSON in stream message %s, skipping", item_id)
					continue

				if isinstance(parsed, dict):
					try:
						record = InferenceRecord.model_validate(parsed)
					except Exception:
						logger.warning("Invalid inference record in stream message %s, skipping", item_id)
						continue
					messages.append(InferenceStreamMessage(stream_id=item_id, record=record))

		return messages

	async def push_results(self, results: Sequence[InferenceResult]) -> None:
		"""
		Push inference results to the output queue.
		
		Args:
			results: Sequence of InferenceResult objects to push
			
		Raises:
			RuntimeError: If unable to push results to Redis
		"""
		if not results:
			return

		try:
			# write each result as a stream entry (field 'data')
			for result in results:
				payload = result.model_dump_json()
				await self._client.xadd(self._output_queue_name, {"data": payload})
			logger.debug("Pushed %d results to output stream %s", len(results), self._output_queue_name)
		except Exception as e:
			logger.error("Error pushing results to Redis stream: %s", e)
			raise RuntimeError(f"Failed to push results to Redis: {e}") from e

	async def push_raw_results(self, results: Sequence[dict[str, Any]]) -> None:
		if not results:
			return

		for result in results:
			await self._client.xadd(self._output_queue_name, {"data": json.dumps(result, ensure_ascii=False)})

	async def ack_messages(self, ids: Iterable[str]) -> None:
		"""Acknowledge processed message ids in the input stream group."""
		try:
			ids_list = list(ids)
			if not ids_list:
				return
			# Acknowledge and delete entries to avoid re-processing and keep stream trimmed
			await self._client.xack(self._input_queue_name, self._group_name, *ids_list)
			try:
				await self._client.xdel(self._input_queue_name, *ids_list)
			except Exception:
				# if XDEL fails, it's non-fatal — entries will remain but are acked
				logger.debug("xdel failed for ids %s", ids_list)
		except Exception as e:
			logger.warning("Failed to ack messages %s: %s", ids, e)

	async def get_heatmap(self, heatmap_key: str) -> list[list[float]] | None:
		raw_heatmap = await self._client.get(heatmap_key)
		if not raw_heatmap:
			return None
		try:
			parsed_heatmap = json.loads(raw_heatmap)
		except json.JSONDecodeError:
			logger.warning("Invalid heatmap JSON in Redis key %s", heatmap_key)
			return None

		if not isinstance(parsed_heatmap, list):
			return None
		return parsed_heatmap

	async def set_heatmap(self, heatmap_key: str, heatmap: list[list[float]]) -> None:
		await self._client.set(heatmap_key, json.dumps(heatmap, ensure_ascii=False))


class PredictionConfigRepository:
	def __init__(self, client: RedisClient, key_prefix: str = "prediction-config:") -> None:
		self._client = client.client
		self._key_prefix = key_prefix

	def _key(self, token: str) -> str:
		return f"{self._key_prefix}{token}"

	async def get_for_token(self, token: str) -> PredictionConfig:
		raw_config = await self._client.get(self._key(token))
		if not raw_config:
			return PredictionConfig()

		try:
			return PredictionConfig.model_validate_json(raw_config)
		except Exception:
			logger.warning("Invalid prediction config for token %s, falling back to defaults", token)
			return PredictionConfig()

	async def set_for_token(self, token: str, config: PredictionConfig) -> None:
		await self._client.set(self._key(token), config.model_dump_json())

