from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from scr.schemas.inference_request import InferenceBatchItem, InferenceStreamMessage
from scr.services.features import flatten_mapping

logger = logging.getLogger(__name__)


class BatchBuilder:
    def build(
        self,
        raw_records: list[InferenceStreamMessage],
    ) -> list[InferenceBatchItem]:
        batch: list[InferenceBatchItem] = []
        for raw_record in raw_records:
            try:
                record_id = raw_record.record.record_id
                payload = raw_record.record.payload
                model_payload = {key: value for key, value in payload.items() if key != "__meta__"}
                batch.append(
                    InferenceBatchItem(
                        record_id=record_id,
                        features=flatten_mapping(model_payload),
                        raw_payload=payload,
                    )
                )
            except Exception as e:
                logger.exception("Error building batch item from record: %s", raw_record)
                continue

        return batch