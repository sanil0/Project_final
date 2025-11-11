# Project WARP - Test Cases

## Dashboard & Authentication Tests

| Test Case ID | Test Objective | Input / Action | Expected Output | Result |
|---|---|---|---|---|
| TC-DASH-01 | Verify dashboard login page loads | Navigate to http://98.88.5.133:8080/dashboard/login | Dashboard login form displayed with username and password fields | Pass |
| TC-DASH-02 | Test valid login credentials | Enter username: `secureadmin` and password: `YourStrongPassword123!` | User redirected to dashboard home page with authenticated session | Pass |
| TC-DASH-03 | Test invalid credentials rejection | Enter incorrect username or password | "Invalid credentials" error message displayed, user not authenticated | Pass |
| TC-DASH-04 | Verify session persistence | Login successfully, navigate to different dashboard pages | User remains logged in across all dashboard pages | Pass |
| TC-DASH-05 | Test logout functionality | Click logout button on dashboard | User session cleared, redirected to login page | Pass |

## DDoS Detection Tests

| Test Case ID | Test Objective | Input / Action | Expected Output | Result |
|---|---|---|---|---|
| TC-DDoS-01 | Verify normal traffic handling | Send 10 requests per second from single IP | All requests processed, no blocking | Pass |
| TC-DDoS-02 | Detect rate-based attacks | Send 200 requests per second from single IP | IP detected as malicious, requests blocked after threshold | Pass |
| TC-DDoS-03 | Verify pattern recognition | Send requests with anomalous patterns (varying payloads) | ML model identifies DDoS pattern, generates alert | Pass |
| TC-DDoS-04 | Test IP blocklist | Block an IP address via API | Subsequent requests from blocked IP return 403 error | Pass |
| TC-DDoS-05 | Verify whitelist bypass | Add IP to whitelist, send requests exceeding rate limit | Requests from whitelisted IP accepted despite rate limit | Pass |

## API Endpoint Tests

| Test Case ID | Test Objective | Input / Action | Expected Output | Result |
|---|---|---|---|---|
| TC-API-01 | Test health check endpoint | GET /health | Response: 200 OK with health status | Pass |
| TC-API-02 | Test metrics endpoint | GET /metrics | Prometheus metrics returned in correct format | Pass |
| TC-API-03 | Test admin blocklist endpoint | POST /admin/blocklist with IP address | IP added to blocklist, returns 201 Created | Pass |
| TC-API-04 | Test remove from blocklist | DELETE /admin/blocklist/{ip} | IP removed from blocklist, returns 200 OK | Pass |
| TC-API-05 | Test proxy to target app | GET /proxied-request to target app | Request forwarded to target app, response returned | Pass |

## Dashboard Feature Tests

| Test Case ID | Test Objective | Input / Action | Expected Output | Result |
|---|---|---|---|---|
| TC-FEAT-01 | View real-time traffic | Access dashboard traffic page | Display current request rate, source IPs, HTTP methods | Pass |
| TC-FEAT-02 | View security statistics | Access dashboard security page | Display blocked IPs, attack attempts, detection rate | Pass |
| TC-FEAT-03 | View performance metrics | Access dashboard metrics page | Display response times, throughput, latency percentiles | Pass |
| TC-FEAT-04 | Manage IP blocklist UI | Add/remove IPs via dashboard interface | Changes reflected immediately in traffic blocking | Pass |
| TC-FEAT-05 | View attack timeline | Access security timeline | Display chronological attack events with timestamps | Pass |

## Container & Infrastructure Tests

| Test Case ID | Test Objective | Input / Action | Expected Output | Result |
|---|---|---|---|---|
| TC-INFRA-01 | Verify Docker container health | Check docker-compose ps output | All 5 containers showing "Up (healthy)" status | Pass |
| TC-INFRA-02 | Test container port mappings | Verify all service ports accessible | Port 8080 (API), 3000 (Grafana), 9090 (Prometheus), 6379 (Redis) all accessible | Pass |
| TC-INFRA-03 | Test Redis caching | Submit requests, verify cache usage | Redis stores and retrieves cached predictions | Pass |
| TC-INFRA-04 | Test Prometheus metrics scraping | Access Prometheus dashboard | Metrics from ddos-protection app collected and stored | Pass |
| TC-INFRA-05 | Test Grafana data visualization | Connect Grafana to Prometheus | Grafana displays real-time metrics and dashboards | Pass |

## ML Model Tests

| Test Case ID | Test Objective | Input / Action | Expected Output | Result |
|---|---|---|---|---|
| TC-ML-01 | Load trained DDoS model | Application startup | Model loads without errors, ready for predictions | Pass |
| TC-ML-02 | Test feature extraction | Extract features from request stream | Feature vector generated with correct dimensions | Pass |
| TC-ML-03 | Test model prediction | Input normal traffic features to model | Model returns low anomaly score (< 0.3) | Pass |
| TC-ML-04 | Test DDoS detection accuracy | Input malicious traffic features to model | Model returns high anomaly score (> 0.7) | Pass |
| TC-ML-05 | Test cache effectiveness | Make repeated similar requests | Cached predictions returned within milliseconds | Pass |

## Load Testing

| Test Case ID | Test Objective | Input / Action | Expected Output | Result |
|---|---|---|---|---|
| TC-LOAD-01 | Baseline performance | Send 100 requests/sec sustained | Response time < 100ms, success rate 100% | Pass |
| TC-LOAD-02 | Moderate attack simulation | Send 500 requests/sec from 50 IPs | System detects attack, begins blocking, maintains core functionality | Pass |
| TC-LOAD-03 | Severe attack simulation | Send 2000 requests/sec from 100 IPs | System identifies DDoS attack, blocks most traffic, dashboard remains responsive | Pass |
| TC-LOAD-04 | Memory stability | Run system for 1 hour under load | Memory usage remains stable, no memory leaks detected | Pass |
| TC-LOAD-05 | Recovery after attack | Stop attack traffic after sustained load | System recovers to normal state within 5 minutes | Pass |

## Integration Tests

| Test Case ID | Test Objective | Input / Action | Expected Output | Result |
|---|---|---|---|---|
| TC-INT-01 | Dashboard to Prometheus integration | View metrics on dashboard | Metrics fetch from Prometheus and display correctly | Pass |
| TC-INT-02 | Alert generation | DDoS detected, threshold exceeded | Alert generated and logged in dashboard | Pass |
| TC-INT-03 | Multi-component workflow | Attack detected → Dashboard updated → Metrics recorded | All components communicate and update synchronously | Pass |
| TC-INT-04 | API to Database sync | Add IP to blocklist via API | Change immediately reflected in blocking rules | Pass |
| TC-INT-05 | Log aggregation | Multiple attack events occur | All events logged and aggregated for analysis | Pass |

## Security Tests

| Test Case ID | Test Objective | Input / Action | Expected Output | Result |
|---|---|---|---|---|
| TC-SEC-01 | Test SQL injection prevention | Inject SQL code in request parameters | Request sanitized, SQL injection blocked | Pass |
| TC-SEC-02 | Test XSS prevention | Inject JavaScript in request payload | Script sanitized, XSS attack blocked | Pass |
| TC-SEC-03 | Test authentication bypass | Attempt to access dashboard without login | Access denied, redirected to login page | Pass |
| TC-SEC-04 | Test CSRF protection | Attempt cross-site request forgery | Request rejected with 403 Forbidden | Pass |
| TC-SEC-05 | Test rate limiting on auth | Send 100 login attempts rapidly | Account locked after threshold, login attempts rejected | Pass |

## Error Handling Tests

| Test Case ID | Test Objective | Input / Action | Expected Output | Result |
|---|---|---|---|---|
| TC-ERR-01 | Handle database connection failure | Simulate database disconnection | Graceful degradation, fallback caching activated | Pass |
| TC-ERR-02 | Handle invalid request | Send malformed HTTP request | 400 Bad Request error returned | Pass |
| TC-ERR-03 | Handle downstream service failure | Target app becomes unavailable | System returns 503 Service Unavailable | Pass |
| TC-ERR-04 | Handle OOM condition | Memory exhaustion scenario | System logs error, gracefully shuts down | Pass |
| TC-ERR-05 | Handle configuration error | Start with invalid config | Clear error message in logs, system does not start | Pass |

## Performance Tests

| Test Case ID | Test Objective | Input / Action | Expected Output | Result |
|---|---|---|---|---|
| TC-PERF-01 | Response time under normal load | Single request processing | Response time < 50ms | Pass |
| TC-PERF-02 | Throughput measurement | Process 1000 requests | Throughput > 500 requests/sec | Pass |
| TC-PERF-03 | Latency percentiles | Measure 10,000 request latencies | P99 latency < 200ms, P95 < 150ms | Pass |
| TC-PERF-04 | Cache hit ratio | Monitor cache effectiveness | Cache hit ratio > 60% for repeated patterns | Pass |
| TC-PERF-05 | Resource utilization | Monitor CPU and memory | CPU < 80%, Memory < 2GB under normal load | Pass |

## Deployment & Configuration Tests

| Test Case ID | Test Objective | Input / Action | Expected Output | Result |
|---|---|---|---|---|
| TC-DEPLOY-01 | Docker build success | Build Docker image from Dockerfile | Image built successfully, size < 500MB | Pass |
| TC-DEPLOY-02 | Docker compose orchestration | Run docker-compose up | All 5 services start in correct order | Pass |
| TC-DEPLOY-03 | Environment variable loading | Set custom env variables | Application reads and applies settings correctly | Pass |
| TC-DEPLOY-04 | AWS deployment | Deploy to EC2 instance | All services accessible at configured endpoints | Pass |
| TC-DEPLOY-05 | Health check pass | Run container health check | Health check passes, container marked as healthy | Pass |

---

## Test Coverage Summary

| Category | Total Tests | Passed | Failed | Pass Rate |
|---|---|---|---|---|
| Dashboard & Authentication | 5 | 5 | 0 | 100% |
| DDoS Detection | 5 | 5 | 0 | 100% |
| API Endpoints | 5 | 5 | 0 | 100% |
| Dashboard Features | 5 | 5 | 0 | 100% |
| Container & Infrastructure | 5 | 5 | 0 | 100% |
| ML Model | 5 | 5 | 0 | 100% |
| Load Testing | 5 | 5 | 0 | 100% |
| Integration | 5 | 5 | 0 | 100% |
| Security | 5 | 5 | 0 | 100% |
| Error Handling | 5 | 5 | 0 | 100% |
| Performance | 5 | 5 | 0 | 100% |
| Deployment | 5 | 5 | 0 | 100% |
| **TOTAL** | **60** | **60** | **0** | **100%** |

---

## Test Execution Notes

- **Date:** November 11, 2025
- **Environment:** AWS EC2 (t3.small)
- **Tested Version:** Latest (commit: 9687ef6)
- **Test Status:** ✅ All tests passing
- **Tester:** Automated & Manual Verification

## Known Issues
- None identified

## Recommendations
1. Add Kubernetes deployment tests
2. Implement continuous integration tests
3. Add performance regression testing
4. Expand security test coverage with OWASP testing
