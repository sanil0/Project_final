# Configuration Guide

## Overview
This document describes the configuration options for the DDoS Protection Service. All settings can be configured through environment variables or a `.env` file.

## Quick Start
1. Copy `.env.template` to `.env`
2. Modify settings as needed
3. Restart the service

## Configuration Categories

### Core Application Settings

| Setting | Description | Default | Required |
|---------|-------------|---------|----------|
| UPSTREAM_BASE_URL | URL of the upstream service to protect | None | Yes |
| ADMIN_API_KEY | API key for admin endpoints | None | Yes |

### DDoS Protection Settings

| Setting | Description | Default | Valid Options |
|---------|-------------|---------|---------------|
| TARGET_URL | Protected web application URL | None | Valid URL |
| SENSITIVITY_LEVEL | DDoS detection sensitivity | medium | low/medium/high |

### Rate Limiting

| Setting | Description | Default | Range |
|---------|-------------|---------|-------|
| BASE_RATE_LIMIT | Base requests per window | 120 | ≥1 |
| RATE_WINDOW_SECONDS | Time window for rate limiting | 60 | ≥1 |
| BURST_MULTIPLIER | Burst allowance multiplier | 1.5 | ≥1.0 |
| DYNAMIC_RATE_ADJUSTMENT | Enable ML-based adjustment | true | true/false |

### Blocking Rules

| Setting | Description | Default | Range |
|---------|-------------|---------|-------|
| BLOCK_DURATION_MINUTES | Initial block duration | 30 | ≥1 |
| BLOCK_THRESHOLD_VIOLATIONS | Violations before blocking | 3 | ≥1 |
| PROGRESSIVE_BLOCKING | Increase duration for repeats | true | true/false |
| MAX_BLOCK_DURATION_HOURS | Maximum block duration | 24 | ≥1 |

### ML Model Configuration

| Setting | Description | Default | Range |
|---------|-------------|---------|-------|
| MODEL_PATH | Path to model files | models | Valid path |
| MODEL_UPDATE_INTERVAL_HOURS | Update check interval | 24 | ≥1 |
| ENABLE_MODEL_CACHE | Enable prediction cache | true | true/false |
| MODEL_CACHE_TTL_SECONDS | Cache TTL | 300 | ≥1 |
| MODEL_CACHE_MAX_SIZE | Max cached predictions | 10000 | ≥100 |
| BATCH_PREDICTION_SIZE | Prediction batch size | 100 | ≥10 |

### Feature Extraction

| Setting | Description | Default | Range |
|---------|-------------|---------|-------|
| FEATURE_WINDOW_SECONDS | Feature extraction window | 300 | ≥60 |
| MIN_SAMPLES_REQUIRED | Min samples for prediction | 10 | ≥1 |

### IP Management

| Setting | Description | Format | Example |
|---------|-------------|--------|---------|
| BLOCKLIST_IPS | IPs to block | Comma-separated | 1.2.3.4,5.6.7.8 |
| WHITELIST_IPS | IPs to allow | Comma-separated | 10.0.0.1,10.0.0.2 |
| TRUSTED_PROXIES | Trusted proxy CIDRs | Comma-separated | 10.0.0.0/24 |
| COUNTRY_BLOCKLIST | Countries to block | Comma-separated | CN,RU |
| ASN_BLOCKLIST | ASNs to block | Comma-separated | AS12345,AS67890 |
| IP_REPUTATION_THRESHOLD | Min reputation score | 0.0-1.0 | 0.7 |

### Request Processing

| Setting | Description | Default | Valid Options |
|---------|-------------|---------|---------------|
| HONOR_X_FORWARDED_FOR | Trust X-Forwarded-For | false | true/false |
| MAX_REQUEST_SIZE_KB | Max request size | 1024 | ≥1 |
| ENABLE_REQUEST_VALIDATION | Validate requests | true | true/false |

## Best Practices

### Security
- Always change ADMIN_API_KEY in production
- Use HTTPS for UPSTREAM_BASE_URL and TARGET_URL
- Set appropriate rate limits based on your application
- Regularly update blocked IPs and countries

### Performance
- Adjust BATCH_PREDICTION_SIZE based on traffic patterns
- Configure MODEL_CACHE settings based on memory availability
- Set appropriate FEATURE_WINDOW_SECONDS for your use case

### Monitoring
- Monitor block rates and adjust thresholds as needed
- Review rate limits periodically
- Check model prediction accuracy regularly

## Examples

### High Security Configuration
```env
SENSITIVITY_LEVEL=high
BASE_RATE_LIMIT=60
BLOCK_THRESHOLD_VIOLATIONS=2
PROGRESSIVE_BLOCKING=true
IP_REPUTATION_THRESHOLD=0.8
```

### High Performance Configuration
```env
BATCH_PREDICTION_SIZE=200
MODEL_CACHE_MAX_SIZE=20000
FEATURE_WINDOW_SECONDS=180
ENABLE_MODEL_CACHE=true
```