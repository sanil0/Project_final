# Performance SLOs and Tuning Guide

## Service Level Objectives (SLOs)

### Latency SLOs
- **P50 (Median)**: < 50ms
- **P95 (95th percentile)**: < 100ms  
- **P99 (99th percentile)**: < 200ms
- **Maximum**: < 500ms

### Throughput SLOs
- **Baseline**: 500-1000 requests/sec per instance
- **Peak Capacity**: 2000-3000 requests/sec per instance
- **Burst Handling**: 10,000 requests/sec (with rate limiting)

### Availability SLOs
- **Uptime**: 99.9% (allow < 43 minutes downtime per month)
- **Error Rate**: < 0.1% (4 nines)
- **Block Rate**: 1-10% (varies by attack intensity)

## Performance Baseline

Establish baseline on your infrastructure:

```bash
# Run baseline test
pytest tests/load/test_load.py::test_load_profiles -v

# Run locust for distributed load testing
locust -f tests/load/locustfile.py --host http://localhost:8080
```

### Expected Results (Single Instance)
| Metric | Value |
|--------|-------|
| Requests/sec | ~800 |
| Avg Latency | ~30ms |
| P99 Latency | ~150ms |
| Memory | ~250-300MB |
| CPU | 15-25% (4 cores) |

## Tuning Parameters

### Rate Limiting Configuration
```env
REQUEST_RATE_LIMIT=100          # Requests per window
SLIDING_WINDOW_SECONDS=60       # Time window
BURST_MULTIPLIER=1.5            # Allowed burst above limit
DYNAMIC_RATE_ADJUSTMENT=true    # ML-based tuning
```

### Model Configuration
```env
ENABLE_MODEL_CACHE=true         # Enable prediction caching
MODEL_CACHE_TTL_SECONDS=300     # 5-minute cache TTL
MODEL_CACHE_MAX_SIZE=10000      # Max cached predictions
BATCH_PREDICTION_SIZE=100       # Batch predictions for efficiency
```

### Feature Extraction
```env
FEATURE_WINDOW_SECONDS=300      # 5-minute window for features
MIN_SAMPLES_REQUIRED=10         # Minimum packets for prediction
```

## Performance Tuning Checklist

### Application Tuning
- [ ] Enable caching: `ENABLE_MODEL_CACHE=true`
- [ ] Set batch size: `BATCH_PREDICTION_SIZE=100`
- [ ] Tune window sizes based on traffic patterns
- [ ] Use connection pooling for upstream (default: enabled)

### Infrastructure Tuning
- [ ] Deploy on systems with 4+ CPU cores
- [ ] Allocate 2-4GB RAM minimum
- [ ] Use SSD for model files
- [ ] Enable TCP fast open if available

### Kubernetes Tuning
```yaml
resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 2000m
    memory: 2Gi

livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Load Balancing
- Use least-connections algorithm for DDoS guard
- Set connection draining timeout: 30s
- Health check frequency: 10s
- Health check timeout: 5s

## Monitoring for Performance

### Key Metrics to Track
```promql
# Request latency (p95)
histogram_quantile(0.95, rate(ddos_request_duration_seconds_bucket[5m]))

# Requests per second
rate(ddos_requests_total[1m])

# Cache hit rate
rate(cache_hits_total[5m]) / rate(cache_requests_total[5m])

# Memory usage (from process_resident_memory_bytes)
process_resident_memory_bytes / 1024 / 1024  # In MB
```

### Performance Dashboard Panels
1. **Latency Percentiles**: P50, P95, P99 over time
2. **Throughput**: Requests/sec, allowed vs blocked
3. **Resource Usage**: CPU, memory, network I/O
4. **Error Rates**: 4xx, 5xx responses
5. **Model Performance**: Inference time, accuracy

## Capacity Planning

### Vertical Scaling (per instance)
| CPU | Memory | Est. RPS | Cost/Month |
|-----|--------|----------|-----------|
| 2   | 2GB    | 500-800  | $10-20    |
| 4   | 4GB    | 1500-2000| $30-50    |
| 8   | 8GB    | 3000-5000| $70-100   |

### Horizontal Scaling
- Deploy 2+ instances behind load balancer for HA
- Add instance when: P95 latency > 100ms OR CPU > 70%
- Remove instance when: CPU < 20% for > 10 minutes

## Example Production Config

```env
# Performance tuning
ENABLE_MODEL_CACHE=true
MODEL_CACHE_TTL_SECONDS=300
MODEL_CACHE_MAX_SIZE=10000
BATCH_PREDICTION_SIZE=100

# Rate limiting
REQUEST_RATE_LIMIT=500
SLIDING_WINDOW_SECONDS=60
BURST_MULTIPLIER=2.0

# Feature extraction
FEATURE_WINDOW_SECONDS=300
MIN_SAMPLES_REQUIRED=10

# Logging (reduce verbosity)
LOG_LEVEL=INFO

# DDoS protection
SENSITIVITY_LEVEL=medium
BLOCK_DURATION_MINUTES=60
```

## Testing Performance Improvements

```bash
# Before optimization
pytest tests/load/test_load_simple.py -v

# After optimization
pytest tests/load/test_load_simple.py -v

# Compare results and record improvement %
```
