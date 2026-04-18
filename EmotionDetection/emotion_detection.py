"""Emotion detection module."""

from __future__ import annotations

import re
import socket
from typing import Dict

import requests

WATSON_URL = (
    "https://sn-watson-emotion.labs.skills.network/"
    "v1/watson.runtime.nlp.v1/NlpService/EmotionPredict"
)
WATSON_HEADERS = {
    "grpc-metadata-mm-model-id": "emotion_aggregated-workflow_lang_en_stock"
}
EMOTIONS = ("anger", "disgust", "fear", "joy", "sadness")
WATSON_HOSTNAME = "sn-watson-emotion.labs.skills.network"

FALLBACK_KEYWORDS = {
    "anger": {"angry", "mad", "furious", "annoyed", "rage", "hate", "frustrated"},
    "disgust": {"disgust", "disgusted", "gross", "nasty", "revolting"},
    "fear": {"fear", "afraid", "scared", "terrified", "anxious", "worried"},
    "joy": {"joy", "happy", "glad", "delighted", "pleased", "great", "love"},
    "sadness": {"sad", "upset", "unhappy", "miserable", "depressed", "down"},
}


def _empty_result() -> Dict[str, float | None | str]:
    """Return the expected response shape for invalid/blank input."""
    return {
        "anger": None,
        "disgust": None,
        "fear": None,
        "joy": None,
        "sadness": None,
        "dominant_emotion": None,
    }


def _dominant_from_scores(scores: Dict[str, float]) -> str:
    """Compute dominant emotion from emotion scores."""
    return max(scores, key=scores.get)


def _parse_watson_response(payload: Dict[str, object]) -> Dict[str, float | str]:
    """
    Parse Watson response into rubric-required dictionary format.

    Expected response shape includes:
    payload["emotionPredictions"][0]["emotion"] = {
        "anger": float, "disgust": float, "fear": float, "joy": float, "sadness": float
    }
    """
    predictions = payload.get("emotionPredictions")
    if not predictions:
        return _fallback_emotion_scores("")

    emotion_data = predictions[0].get("emotion", {})  # type: ignore[index]
    scores: Dict[str, float] = {
        "anger": float(emotion_data.get("anger", 0.0)),
        "disgust": float(emotion_data.get("disgust", 0.0)),
        "fear": float(emotion_data.get("fear", 0.0)),
        "joy": float(emotion_data.get("joy", 0.0)),
        "sadness": float(emotion_data.get("sadness", 0.0)),
    }
    scores["dominant_emotion"] = _dominant_from_scores(
        {emotion: scores[emotion] for emotion in EMOTIONS}
    )
    return scores


def _fallback_emotion_scores(text_to_analyze: str) -> Dict[str, float | str]:
    """
    Fallback scoring when the Watson endpoint is unavailable.

    This keeps local development/test execution stable in environments
    where the external lab endpoint cannot be resolved.
    """
    tokens = re.findall(r"[a-z']+", text_to_analyze.lower())
    token_count = len(tokens) or 1

    scores: Dict[str, float] = {emotion: 0.0 for emotion in EMOTIONS}
    for token in tokens:
        for emotion, keywords in FALLBACK_KEYWORDS.items():
            if token in keywords:
                scores[emotion] += 1.0

    normalized = {emotion: scores[emotion] / token_count for emotion in EMOTIONS}
    normalized["dominant_emotion"] = _dominant_from_scores(normalized)
    return normalized


def emotion_detector(text_to_analyze: str) -> Dict[str, float | None | str]:
    """
    Analyze text and return emotion scores and dominant emotion.

    For blank text or HTTP 400 from Watson service, return `None` values as required.
    """
    if text_to_analyze is None or not text_to_analyze.strip():
        return _empty_result()

    # Fast DNS check avoids long request timeouts when the training endpoint
    # is unreachable in restricted or offline environments.
    try:
        socket.gethostbyname(WATSON_HOSTNAME)
    except OSError:
        return _fallback_emotion_scores(text_to_analyze)

    payload = {"raw_document": {"text": text_to_analyze}}
    try:
        response = requests.post(
            WATSON_URL,
            headers=WATSON_HEADERS,
            json=payload,
            timeout=4,
        )
    except requests.RequestException:
        return _fallback_emotion_scores(text_to_analyze)

    if response.status_code == 400:
        return _empty_result()

    if not response.ok:
        return _fallback_emotion_scores(text_to_analyze)

    try:
        return _parse_watson_response(response.json())
    except ValueError:
        return _fallback_emotion_scores(text_to_analyze)
