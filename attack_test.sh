#!/bin/bash
# Phase 2: DDoS Attack Simulation

echo "======================================"
echo "PHASE 2: DDoS ATTACK SIMULATION"
echo "======================================"
echo ""

echo "[1/4] Baseline Traffic (20 requests, 0.5s apart)"
for i in {1..20}; do
  curl -s http://localhost:8080/ > /dev/null
  sleep 0.5
done
echo "✓ Baseline complete"
echo ""

echo "[2/4] Attack Phase (150 concurrent requests)"
start_time=$(date +%s)
for i in {1..150}; do
  curl -s http://localhost:8080/ > /dev/null &
done
wait
end_time=$(date +%s)
attack_duration=$((end_time - start_time))
echo "✓ Attack complete (${attack_duration}s)"
echo ""

echo "[3/4] Waiting for metrics to update..."
sleep 5
echo ""

echo "[4/4] Results Summary"
echo "---"
echo "Checking Prometheus metrics..."
curl -s "http://localhost:9091/api/v1/query?query=ddos_events_total" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['data']['result']:
    metric = data['data']['result'][0]
    print(f\"Total DDoS Events: {metric['value'][1]}\")
    print(f\"Status: {metric['metric']['result']}\")
    print(f\"Severity: {metric['metric']['severity']}\")
else:
    print('No metrics found')
"

echo ""
echo "Checking blocked IPs..."
curl -s "http://localhost:9091/api/v1/query?query=ddos_active_blocked_ips" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['data']['result']:
    value = data['data']['result'][0]['value'][1]
    print(f\"Currently Blocked IPs: {value}\")
else:
    print('No blocked IPs')
"

echo ""
echo "======================================"
echo "Phase 2 Attack Simulation Complete!"
echo "======================================"
