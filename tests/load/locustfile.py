"""Load test implementation using Locust."""

import random
import time
from locust import HttpUser, TaskSet, between, task
from .config import LoadTestProfile

class DDoSUser(HttpUser):
    """Base user class for DDoS simulation."""
    
    abstract = True
    wait_time = between(0.1, 1.0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session.trust_env = False
        
class NormalTrafficUser(DDoSUser):
    """Simulates normal user traffic patterns."""
    
    @task(70)
    def index(self):
        self.client.get("/")
        
    @task(20)
    def docs(self):
        self.client.get("/api/docs")
        
    @task(10)
    def health(self):
        self.client.get("/api/healthz")

class DDoSAttackUser(DDoSUser):
    """Simulates DDoS attack patterns."""
    
    wait_time = between(0.01, 0.1)  # Very short wait times
    
    @task(90)
    def flood_main(self):
        self.client.get("/")
        
    @task(10)
    def flood_api(self):
        self.client.post("/api/heavy", json={"data": "X" * 1000})

class SlowLorisUser(DDoSUser):
    """Simulates Slow Loris attack patterns."""
    
    wait_time = between(5, 15)  # Long wait times
    
    @task
    def slow_request(self):
        headers = {"X-Test": "A" * 100}
        with self.client.get("/", headers=headers, stream=True, catch_response=True) as response:
            for _ in range(10):  # Simulate slow reading
                time.sleep(1)
                response.content  # Read a bit of content

class BurstAttackUser(DDoSUser):
    """Simulates burst attack patterns."""
    
    wait_time = between(0.001, 0.01)  # Extremely short wait times
    
    @task
    def burst_request(self):
        self.client.post("/api/heavy", json={"data": "X" * 10000})

class MixedTrafficUser(DDoSUser):
    """Simulates mixed traffic patterns."""
    
    @task(4)
    def normal_request(self):
        self.client.get("/")
        
    @task(2)
    def api_request(self):
        self.client.get("/api/docs")
        
    @task(2)
    def heavy_request(self):
        self.client.post("/api/heavy", json={"data": "X" * 5000})
        
    @task(2)
    def slow_request(self):
        with self.client.get("/api/slow", stream=True, catch_response=True) as response:
            time.sleep(0.1)
            response.content