import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple

from src.schemas.simplify_output import SimplifyOutput

logger = logging.getLogger(__name__)


class SimplifyValidator:
    """Validates model output (not input; input validation is pipeline's job)."""

    KNOWN_BAD_DIR = Path("data/known_bad")
    KNOWN_BAD_FILE = KNOWN_BAD_DIR / "known_bad.jsonl"

    # In-memory dedup: track recent entries by hash to avoid duplicates within 1 hour
    _recent_hashes = {}  # {hash: timestamp}
    _dedup_window_seconds = 3600  # 1 hour

    @classmethod
    def init_known_bad(cls) -> None:
        """Create known_bad directory and file if needed."""
        cls.KNOWN_BAD_DIR.mkdir(parents=True, exist_ok=True)
        if not cls.KNOWN_BAD_FILE.exists():
            cls.KNOWN_BAD_FILE.touch()

    @classmethod
    def validate(
        cls,
        output_json_str: str,
        original_text: str,
        tag: str = "simplification_output",
    ) -> Tuple[bool, str]:
        """
        Validate model output JSON (decode + schema + semantic).
        Returns (is_valid, error_message).
        If invalid, logs to known_bad.jsonl (with dedup).
        """
        # 1) JSON decode validation
        try:
            data = json.loads(output_json_str)
        except json.JSONDecodeError as e:
            cls._log_bad(
                original_text=original_text,
                tag="json_decode_error",
                short_comment=f"JSON decode failed: {str(e)}",
                output_json=output_json_str,
            )
            return False, f"JSON decode error: {str(e)}"

        # 2) Pydantic schema validation
        try:
            _ = SimplifyOutput(**data)
        except (ValueError, TypeError) as e:
            cls._log_bad(
                original_text=original_text,
                tag="schema_validation_error",
                short_comment=f"Schema validation failed: {str(e)}",
                output_json=output_json_str,
            )
            return False, f"Schema validation error: {str(e)}"

        # 3) Semantic validation (output quality only, not input length)
        semantic_errors = cls._semantic_checks(output_json=data, original_text=original_text)
        if semantic_errors:
            cls._log_bad(
                original_text=original_text,
                tag="semantic_validation_error",
                short_comment=semantic_errors[0],
                output_json=output_json_str,
            )
            return False, "; ".join(semantic_errors)

        return True, ""

    @classmethod
    def _semantic_checks(cls, output_json: dict, original_text: str) -> list:
        """
        Semantic validation rules for MODEL OUTPUT (not input).
        Returns list of error messages (empty = valid).

        Note: Input length validation happens in pipeline (early guard).
        This validates output quality: length, hallucination in generated text.
        """
        errors = []

        summary = (output_json.get("summary") or "").strip()
        if not summary:
            errors.append("Summary is empty or whitespace")
            return errors

        # Rule 1: Summary word count reasonable
        wc = len(summary.split())
        if wc < 5:
            errors.append(f"Summary too short ({wc} words, min 5)")
        if wc > 200:
            errors.append(f"Summary too long ({wc} words, max 200)")

        # Rule 2: Basic sanity check (summary not identical to input unless input is very short)
        if len(original_text) > 50:
            if summary.lower() == original_text.lower():
                errors.append("Summary identical to input (no simplification occurred)")

        return errors

    @classmethod
    def log_known_bad(
        cls,
        original_text: str,
        tag: str,
        short_comment: str,
        output_json: str = "",
    ) -> None:
        """Public method to log bad cases (called from pipeline)."""
        cls._log_bad(original_text, tag, short_comment, output_json)

    @classmethod
    def _log_bad(
        cls,
        original_text: str,
        tag: str,
        short_comment: str,
        output_json: str = "",
    ) -> None:
        """
        Append validation failure to known_bad.jsonl with deduplication.
        Dedup: if same (original_text + tag) seen in last 1 hour, skip logging.
        """
        try:
            cls.init_known_bad()

            # Dedup check: hash of (original_text + tag)
            dedup_key = hashlib.sha256(f"{original_text}:{tag}".encode()).hexdigest()
            now = datetime.now()

            # Cleanup old entries (older than dedup window)
            cls._recent_hashes = {
                k: v
                for k, v in cls._recent_hashes.items()
                if (now - v).total_seconds() < cls._dedup_window_seconds
            }

            # Skip if duplicate within window
            if dedup_key in cls._recent_hashes:
                logger.debug(f"Skipped duplicate: {tag} | {short_comment}")
                return

            # Log it
            cls._recent_hashes[dedup_key] = now

            record = {
                "id": f"bad_{int(datetime.now().timestamp() * 1_000_000)}",
                "tag": tag,
                "short_comment": short_comment,  # Full message (no truncation)
                "original_text_preview": (original_text or "")[:200],
                "output_json_preview": (output_json or "")[:200],
                "created_at": datetime.utcnow().isoformat() + "Z",
            }

            with open(cls.KNOWN_BAD_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

            logger.info(f"known_bad logged: [{tag}] {short_comment}")

        except Exception as e:
            logger.error(f"known_bad write failed: {type(e).__name__}: {e}")
