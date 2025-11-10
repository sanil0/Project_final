# Monitoring & Observability Guide

## Prometheus Metrics

The DDoS protection service exposes Prometheus metrics on the `/metrics` endpoint.

### Key Metrics

#### Request Metrics
- `ddos_requests_total` - Total requests processed
- `ddos_requests_allowed_total` - Requests allowed through
- `ddos_requests_blocked_total` - Requests blocked (by reason)
- `ddos_request_duration_seconds` - Request processing time (histogram)

#### Protection Metrics
- `ddos_blocked_ips_total` - Total unique IPs blocked
- `ddos_active_blocked_ips` - Currently active blocked IP count
- `ddos_rate_limit_hits_total` - Rate limit violations
- `ddos_risk_score` - Risk score distribution (histogram)

#### Performance Metrics
- `ddos_model_inference_seconds` - ML model inference time
- `ddos_feature_extraction_seconds` - Feature extraction time

## Local Monitoring Stack

Start the full stack with Prometheus and Grafana:

```bash
docker-compose up -d
```

Access:
- **Application**: http://localhost:8080
- **Prometheus**: http://localhost:9091
- **Grafana**: http://localhost:3000 (admin/admin)

## Grafana Dashboards

### Create a New Dashboard

1. Log in to Grafana (http://localhost:3000)
2. Click "+" → "Dashboard"
3. Add panels for:
   - Requests per minute
   - Blocked requests ratio
   - Risk score distribution
   - Top blocked IPs
   - Response times

### Query Examples

**Requests per second:**
```promql
rate(ddos_requests_total[1m])
```

**Block rate:**
```promql
rate(ddos_requests_blocked_total[5m]) / rate(ddos_requests_total[5m])
```

**Active blocked IPs:**
```promql
ddos_active_blocked_ips
```

**P95 Response Time:**
```promql
histogram_quantile(0.95, rate(ddos_request_duration_seconds_bucket[5m]))
```

## Alerting Rules

Create alerting rules in Prometheus (`monitoring/prometheus/rules.yml`):

```yaml
groups:
  - name: ddos_alerts
    rules:
      - alert: HighBlockRate
        expr: |
          (rate(ddos_requests_blocked_total[5m]) / 
           rate(ddos_requests_total[5m])) > 0.1
        for: 5m
        annotations:
          summary: "High DDoS block rate detected"
      
      - alert: SlowInference
        expr: histogram_quantile(0.95, rate(ddos_model_inference_seconds_bucket[5m])) > 1
        for: 5m
        annotations:
          summary: "Slow ML model inference"
```

## Logs

Application logs are written to `/app/logs/` in the container.

Access logs:
```bash
docker logs ddos-protection
```

Or view mounted logs:
```bash
tail -f ./logs/*.log
```

## Health Checks

Simple health endpoint:
```bash
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

## Performance Baseline

Run baseline benchmarks:
```bash
pytest tests/load/test_load.py::test_baseline -v
```

This establishes SLOs for:
- Request latency (p99 < 100ms)
- Throughput (>1000 req/sec)
- Memory usage (<500MB)
