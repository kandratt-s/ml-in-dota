from __future__ import annotations

import logging
import pickle
from collections.abc import Sequence
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger(__name__)


class Predictor(Protocol):
    backend_name: str

    def predict_proba(self, features: Sequence[dict[str, Any]]) -> list[float]:
        raise NotImplementedError


class ModelBackend(StrEnum):
    SKLEARN_LOGISTIC_REGRESSION = "sklearn_logistic_regression"
    CATBOOST = "catboost"


class SklearnLogisticRegressionPredictor:
    backend_name = ModelBackend.SKLEARN_LOGISTIC_REGRESSION

    def __init__(self, model: LogisticRegression, vectorizer: DictVectorizer) -> None:
        self._model = model
        self._vectorizer = vectorizer

    def predict_proba(self, features: Sequence[dict[str, Any]]) -> list[float]:
        """
        Predict probabilities using sklearn LogisticRegression model.
        
        Features are transformed using the trained DictVectorizer before prediction.
        """
        try:
            transformed_features = self._vectorizer.transform(features)
            probabilities = self._model.predict_proba(transformed_features)
            return [float(row[1]) for row in probabilities]
        except Exception as e:
            logger.exception("Error during sklearn prediction with features: %s", features)
            raise RuntimeError(f"Sklearn prediction failed: {e}") from e


class CatBoostPredictor:
    backend_name = ModelBackend.CATBOOST

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
            with self._model_path.open("rb") as file_handle:
                loaded_model = pickle.load(file_handle)
        except Exception as e:
            logger.error("Failed to load model from %s: %s", self._model_path, e)
            return None

        if isinstance(loaded_model, LogisticRegression):
            # Create a default vectorizer for sklearn model
            # Note: In production, load the saved vectorizer alongside the model
            logger.info("Loaded sklearn LogisticRegression model from %s", self._model_path)
            vectorizer = DictVectorizer(sparse=True)
            return SklearnLogisticRegressionPredictor(loaded_model, vectorizer)

        logger.error("Unsupported model type: %s (file: %s)", type(loaded_model).__name__, self._model_path)
        return None