#!/usr/bin/env python3
"""Check if dashboard API returns graph data."""
import urllib.request
import urllib.parse
import json
import http.cookiejar

# Create cookie jar
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
urllib.request.install_opener(opener)

# Login first to get session token
login_data = urllib.parse.urlencode({"username": "admin", "password": "SecureP@ssw0rd123!"}).encode()
req = urllib.request.Request("http://98.88.5.133:8080/dashboard/login", data=login_data)
resp = urllib.request.urlopen(req)
print(f"Login status: {resp.status}")

# Get metrics
resp = urllib.request.urlopen("http://98.88.5.133:8080/dashboard/api/metrics")
print(f"\n📊 Dashboard API Response ({resp.status}):")

data = json.loads(resp.read().decode())

# Check for required fields
print(f"\n✅ Scalar Metrics:")
print(f"  - total_requests: {data.get('total_requests')}")
print(f"  - blocked_requests: {data.get('blocked_requests')}")
print(f"  - block_rate: {data.get('block_rate')}%")

print(f"\n📈 Timeline Data (for graphs):")
timeline = data.get('traffic_timeline', [])
print(f"  - traffic_timeline: {len(timeline)} data points")
if timeline:
    print(f"    First point: {timeline[0]}")
    print(f"    Last point: {timeline[-1]}")

risk_dist = data.get('risk_distribution', {})
print(f"  - risk_distribution: {risk_dist}")

latency_trend = data.get('latency_trend', [])
print(f"  - latency_trend: {len(latency_trend)} data points")
if latency_trend:
    print(f"    Sample: {latency_trend[0]}")

if timeline and risk_dist and latency_trend:
    print(f"\n✅ All graph data fields present! Graphs should now populate.")
else:
    print(f"\n❌ Missing graph data fields")
