"""
Rate Limiting for AI Automation Features

Prevents abuse of expensive LLM operations.
"""

import logging
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API endpoints"""

    def __init__(self):
        """Initialize rate limiter"""
        self.requests: Dict[str, list] = defaultdict(list)
        self.cleanup_interval = 3600  # Clean up old entries every hour

    def is_allowed(
        self,
        user_id: str,
        endpoint: str,
        max_requests: int = 10,
        window_seconds: int = 3600,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if request is allowed under rate limit.

        Args:
            user_id: User identifier
            endpoint: API endpoint
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            Tuple of (is_allowed, error_message)
        """
        key = f"{user_id}:{endpoint}"
        now = time.time()
        window_start = now - window_seconds

        # Clean up old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]

        # Check if limit exceeded
        if len(self.requests[key]) >= max_requests:
            oldest_request = min(self.requests[key])
            retry_after = int(oldest_request + window_seconds - now) + 1
            error_msg = f"Rate limit exceeded. Retry after {retry_after} seconds"
            logger.warning(f"Rate limit exceeded for {key}: {error_msg}")
            return False, error_msg

        # Record this request
        self.requests[key].append(now)
        return True, None

    def get_remaining_requests(
        self,
        user_id: str,
        endpoint: str,
        max_requests: int = 10,
        window_seconds: int = 3600,
    ) -> int:
        """
        Get remaining requests for user.

        Args:
            user_id: User identifier
            endpoint: API endpoint
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            Number of remaining requests
        """
        key = f"{user_id}:{endpoint}"
        now = time.time()
        window_start = now - window_seconds

        # Clean up old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]

        return max(0, max_requests - len(self.requests[key]))


class AIAutomationRateLimiter:
    """Specialized rate limiter for AI automation features"""

    # Rate limits for different features
    LIMITS = {
        "gap_analysis": {"max_requests": 5, "window_seconds": 3600},  # 5 per hour
        "remediation_plan": {"max_requests": 5, "window_seconds": 3600},  # 5 per hour
        "policy_generation": {"max_requests": 10, "window_seconds": 3600},  # 10 per hour
        "compliance_qa": {"max_requests": 20, "window_seconds": 3600},  # 20 per hour
        "risk_prediction": {"max_requests": 5, "window_seconds": 3600},  # 5 per hour
    }

    def __init__(self):
        """Initialize AI automation rate limiter"""
        self.limiter = RateLimiter()

    def check_limit(
        self,
        user_id: str,
        feature: str,
    ) -> tuple[bool, Optional[str], int]:
        """
        Check if AI automation request is allowed.

        Args:
            user_id: User identifier
            feature: Feature name (gap_analysis, policy_generation, etc.)

        Returns:
            Tuple of (is_allowed, error_message, remaining_requests)
        """
        if feature not in self.LIMITS:
            logger.warning(f"Unknown feature for rate limiting: {feature}")
            return True, None, -1

        limit_config = self.LIMITS[feature]
        is_allowed, error_msg = self.limiter.is_allowed(
            user_id,
            feature,
            max_requests=limit_config["max_requests"],
            window_seconds=limit_config["window_seconds"],
        )

        remaining = self.limiter.get_remaining_requests(
            user_id,
            feature,
            max_requests=limit_config["max_requests"],
            window_seconds=limit_config["window_seconds"],
        )

        return is_allowed, error_msg, remaining

    def get_limits_info(self, user_id: str) -> Dict[str, Dict]:
        """
        Get rate limit information for all features.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with limit info for each feature
        """
        info = {}

        for feature, config in self.LIMITS.items():
            remaining = self.limiter.get_remaining_requests(
                user_id,
                feature,
                max_requests=config["max_requests"],
                window_seconds=config["window_seconds"],
            )

            info[feature] = {
                "max_requests": config["max_requests"],
                "window_seconds": config["window_seconds"],
                "remaining_requests": remaining,
                "reset_in_seconds": config["window_seconds"],
            }

        return info


# Global rate limiter instance
ai_automation_rate_limiter = AIAutomationRateLimiter()
