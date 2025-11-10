"""Test server for load testing."""

import asyncio
import random
import time
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Create FastAPI app with docs disabled
app = FastAPI(
    title="Load Test Server",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

@app.get("/healthz")
async def healthcheck():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/")
async def root():
    """Root endpoint for testing."""
    return {"message": "Hello from test server"}

@app.get("/api/test")
async def api_test_endpoint():
    """Test endpoint that simulates processing."""
    await asyncio.sleep(random.uniform(0.1, 0.5))
    return {"status": "success", "timestamp": time.time()}

import asyncio
import logging
import random
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Load Test Server",
    docs_url=None,  # Disable API docs to reduce 404 noise
    redoc_url=None  # Disable ReDoc to reduce 404 noise
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global server state
server_state = {"is_running": True}

@app.get("/healthz")
async def healthcheck():
    """Health check endpoint."""
    if not server_state["is_running"]:
        return JSONResponse({"status": "shutting_down"}, status_code=503)
    return {"status": "ok"}

@app.get("/")
async def root():
    """Root endpoint for testing."""
    if not server_state["is_running"]:
        return JSONResponse({"status": "shutting_down"}, status_code=503)
    return {"message": "Hello from test server"}

@app.get("/api/test")
async def api_test_endpoint():
    """Test endpoint that simulates processing."""
    if not server_state["is_running"]:
        return JSONResponse({"status": "shutting_down"}, status_code=503)
    await asyncio.sleep(random.uniform(0.1, 0.5))
    return {"status": "success", "timestamp": time.time()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
