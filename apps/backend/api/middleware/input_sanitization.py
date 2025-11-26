"""
Input Sanitization Middleware

Provides protection against common injection attacks and malicious input.
"""

import re
import logging
from typing import Any, Dict
from html import escape

logger = logging.getLogger(__name__)


class InputSanitizer:
    """Sanitize user input to prevent injection attacks"""

    # Patterns for detecting potential injection attacks
    SQL_INJECTION_PATTERNS = [
        r"(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|;|\/\*|\*\/)",
        r"('|\")\s*(OR|AND)\s*('|\")",
    ]

    PROMPT_INJECTION_PATTERNS = [
        r"(ignore|forget|disregard).*previous",
        r"(system|admin|root).*prompt",
        r"(jailbreak|bypass|override)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 10000) -> str:
        """
        Sanitize a string input.

        Args:
            value: String to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return str(value)

        # Truncate if too long
        if len(value) > max_length:
            logger.warning(f"Input truncated from {len(value)} to {max_length} characters")
            value = value[:max_length]

        # Remove null bytes
        value = value.replace("\x00", "")

        # HTML escape
        value = escape(value)

        return value

    @classmethod
    def detect_injection_attempt(cls, value: str) -> bool:
        """
        Detect potential injection attacks.

        Args:
            value: String to check

        Returns:
            True if injection attempt detected
        """
        if not isinstance(value, str):
            return False

        value_upper = value.upper()

        # Check SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {value[:50]}")
                return True

        # Check prompt injection patterns
        for pattern in cls.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential prompt injection detected: {value[:50]}")
                return True

        # Check XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential XSS detected: {value[:50]}")
                return True

        return False

    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively sanitize dictionary values.

        Args:
            data: Dictionary to sanitize

        Returns:
            Sanitized dictionary
        """
        sanitized = {}

        for key, value in data.items():
            # Sanitize key
            if isinstance(key, str):
                key = cls.sanitize_string(key, max_length=255)

            # Sanitize value
            if isinstance(value, str):
                value = cls.sanitize_string(value)
            elif isinstance(value, dict):
                value = cls.sanitize_dict(value)
            elif isinstance(value, list):
                value = [
                    cls.sanitize_string(v) if isinstance(v, str) else v
                    for v in value
                ]

            sanitized[key] = value

        return sanitized

    @classmethod
    def validate_compliance_question(cls, question: str) -> tuple[bool, str]:
        """
        Validate compliance question for safety.

        Args:
            question: Question to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not question or len(question.strip()) == 0:
            return False, "Question cannot be empty"

        if len(question) > 5000:
            return False, "Question is too long (max 5000 characters)"

        if cls.detect_injection_attempt(question):
            return False, "Question contains potentially malicious content"

        return True, ""

    @classmethod
    def validate_system_data(cls, system_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate system data for safety.

        Args:
            system_data: System data to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(system_data, dict):
            return False, "System data must be a dictionary"

        # Check required fields
        required_fields = ["system_id", "system_name"]
        for field in required_fields:
            if field not in system_data:
                return False, f"Missing required field: {field}"

        # Validate field values
        for key, value in system_data.items():
            if isinstance(value, str):
                if cls.detect_injection_attempt(value):
                    return False, f"Field '{key}' contains potentially malicious content"

        return True, ""
