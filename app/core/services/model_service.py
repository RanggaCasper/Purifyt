import os
from typing import Optional
from functools import lru_cache

from app.config.logging_config import get_logger
from app.config.settings import get_settings
from app.utils.text_cleaner import clean_comment

logger = get_logger(__name__)
settings = get_settings()

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "model")
MODEL_DIR = os.path.normpath(MODEL_DIR)

_tokenizer = None
_model = None

def _load_model():
    global _tokenizer, _model
    if _tokenizer is not None and _model is not None:
        return

    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
    except ImportError:
        raise RuntimeError("transformers is not installed. Run: pip install transformers")

    try:
        import torch
    except ImportError:
        raise RuntimeError("torch is not installed. Run: pip install torch")

    if not os.path.isdir(MODEL_DIR):
        raise FileNotFoundError(
            f"Model directory not found at '{MODEL_DIR}'. "
            "Place your model files (config.json, model.safetensors, tokenizer, etc.) in the 'model/' folder."
        )

    logger.info("[MODEL] Loading ML model from %s...", MODEL_DIR)
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    _model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
    _model.eval()
    logger.info("[MODEL] ML model loaded successfully")

def predict(text: str) -> dict:
    """
    Predict whether a comment is 'normal' or 'judi'.

    Returns: {
        "label": 0 (non judi) | 1 (judi online),
        "clean_comment": str,
        "normal": float,
        "judi": float,
    }
    """
    import torch

    _load_model()

    cleaned = clean_comment(text)
    if not cleaned:
        return {"label": 0, "clean_comment": "", "normal": 1.0, "judi": 0.0}

    inputs = _tokenizer(cleaned, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = _model(**inputs)
    probs = torch.softmax(outputs.logits, dim=1)[0]

    normal_prob = float(probs[0])
    judi_prob = float(probs[1])
    label = 1 if judi_prob > normal_prob else 0  # 0 = non judi, 1 = judi online

    logger.debug("[MODEL] predict — label=%d judi=%.3f normal=%.3f text=%.60s", label, judi_prob, normal_prob, text)
    return {"label": label, "clean_comment": cleaned, "normal": normal_prob, "judi": judi_prob}

def predict_batch(texts: list[str]) -> list[dict]:
    """Predict labels for a batch of texts."""
    import torch

    _load_model()
    logger.info("[MODEL] predict_batch — %d texts", len(texts))

    # Clean all texts first
    cleaned_texts = [clean_comment(t) for t in texts]

    results = []
    batch_size = 32
    for i in range(0, len(cleaned_texts), batch_size):
        batch = cleaned_texts[i:i + batch_size]
        # Handle empty strings
        batch_for_model = [t if t else " " for t in batch]
        inputs = _tokenizer(batch_for_model, return_tensors="pt", truncation=True, padding=True, max_length=512)
        with torch.no_grad():
            outputs = _model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)

        for j in range(len(batch)):
            normal_prob = float(probs[j][0])
            judi_prob = float(probs[j][1])
            label = 1 if judi_prob > normal_prob else 0  # 0 = non judi, 1 = judi online
            results.append({
                "label": label,
                "clean_comment": batch[j],
                "normal": normal_prob,
                "judi": judi_prob,
            })

    return results
