"""Security scanner configuration."""

# OWASP ZAP Configuration
zap_config = {
    "api_key": "change-me-9012",  # Change in production
    "target_url": "http://localhost:8000",
    "context_name": "ddos_protection",
    "scan_policy": "Default Policy",
    "spider_config": {
        "max_depth": 10,
        "thread_count": 5,
        "post_form": True
    },
    "active_scan": {
        "scan_headers": True,
        "scan_cookies": True,
        "scan_xml": True,
        "scan_json": True
    },
    "excludes": [
        ".*logout.*",
        ".*delete.*",
        ".*remove.*"
    ]
}

# Security Test Configuration
security_test_config = {
    "rate_limits": {
        "default": 100,  # requests per minute
        "authenticated": 300,
        "admin": 500
    },
    "timeouts": {
        "request": 30,  # seconds
        "scan": 3600,  # 1 hour
        "session": 1800  # 30 minutes
    },
    "thresholds": {
        "max_payload_size": 10 * 1024 * 1024,  # 10MB
        "max_request_headers": 100,
        "max_uri_length": 2048,
        "max_field_length": 8192
    },
    "patterns": {
        "ip_whitelist": [
            r"^127\.",
            r"^10\.",
            r"^172\.(1[6-9]|2[0-9]|3[0-1])\.",
            r"^192\.168\."
        ],
        "blocked_user_agents": [
            r".*[Cc]rawler.*",
            r".*[Bb]ot.*",
            r".*[Ss]craper.*"
        ]
    }
}

# Vulnerability Scan Configuration
vuln_scan_config = {
    "enabled_scanners": [
        "sql_injection",
        "xss",
        "path_traversal",
        "remote_code_execution",
        "csrf",
        "ssrf",
        "open_redirect"
    ],
    "risk_threshold": "MEDIUM",  # LOW, MEDIUM, HIGH, CRITICAL
    "confidence_threshold": "HIGH",
    "scan_frequency": 86400,  # Daily in seconds
    "report_format": "html",
    "notification": {
        "email": True,
        "slack": False,
        "threshold": "HIGH"
    }
}

# Authentication Test Configuration
auth_test_config = {
    "endpoints": {
        "login": "/api/auth/login",
        "logout": "/api/auth/logout",
        "refresh": "/api/auth/refresh",
        "register": "/api/auth/register"
    },
    "jwt": {
        "expiry": 3600,  # 1 hour
        "refresh_expiry": 86400,  # 24 hours
        "algorithm": "HS256"
    },
    "password_policy": {
        "min_length": 12,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_numbers": True,
        "require_special": True,
        "max_age": 90  # days
    }
}