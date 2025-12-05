from typing import List, Dict, Any
import re
from core.exceptions import ValidationError

class ConfigValidator:
    """Validator for application configuration."""
    
    @staticmethod
    def validate_production_security(settings: Any) -> List[str]:
        """
        Validate security settings for production environment.
        Returns a list of warning/error messages.
        """
        issues = []
        
        if not settings.is_production:
            return issues
            
        # Check secret keys
        if settings.secret_key == "changeme" or len(settings.secret_key) < 32:
            issues.append("Production secret_key is too weak or default")
            
        if settings.jwt_secret == "changeme" or len(settings.jwt_secret) < 32:
            issues.append("Production jwt_secret is too weak or default")
            
        # Check debug mode
        if settings.debug:
            issues.append("Debug mode is enabled in production")
            
        # Check database
        if settings.database_url.startswith("sqlite"):
            issues.append("SQLite is used in production (PostgreSQL recommended)")
            
        # Check CORS
        allowed_origins = settings.get_allowed_origins()
        if "*" in allowed_origins:
            issues.append("CORS allows all origins ('*') in production")
            
        return issues

    @staticmethod
    def validate_dependencies(settings: Any) -> List[str]:
        """
        Validate dependency configurations.
        """
        issues = []
        
        # Redis validation
        if settings.redis_url and not settings.redis_url.startswith(("redis://", "rediss://")):
            issues.append(f"Invalid Redis URL format: {settings.redis_url}")
            
        # AWS validation
        if settings.aws_s3_bucket and not (settings.aws_access_key_id and settings.aws_secret_access_key):
            issues.append("AWS S3 bucket configured but credentials missing")
            
        # SMTP validation
        if settings.smtp_host and not (settings.smtp_user and settings.smtp_password):
            issues.append("SMTP host configured but credentials missing")
            
        return issues

    @staticmethod
    def mask_sensitive_data(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mask sensitive data in configuration dictionary.
        """
        masked = config.copy()
        sensitive_keys = {
            "secret", "password", "key", "token", "dsn", "credential", "auth"
        }
        
        for key, value in masked.items():
            if not isinstance(value, str):
                continue
                
            # Check if key contains sensitive words
            if any(s in key.lower() for s in sensitive_keys):
                masked[key] = "***MASKED***"
                continue
                
            # Check for URL with credentials
            if "://" in value and "@" in value:
                # Mask password in URL (scheme://user:pass@host)
                masked[key] = re.sub(r":([^@]+)@", ":***@", value)
                
        return masked
