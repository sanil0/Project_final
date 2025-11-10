"""Simplified load test runner."""

import asyncio
import os
import logging
import aiohttp
import pytest
from tests.load.config import NORMAL_TRAFFIC

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_load_test(base_url: str, target_rps: float, duration: int) -> dict:
    """Run a simple load test."""
    total_requests = int(target_rps * duration)
    successes = 0
    failures = 0
    response_times = []

    async def make_request(session):
        nonlocal successes, failures
        try:
            start_time = asyncio.get_event_loop().time()
            async with session.get(f"{base_url}/") as response:
                response_time = asyncio.get_event_loop().time() - start_time
                response_times.append(response_time)
                if response.status == 200:
                    successes += 1
                else:
                    failures += 1
        except Exception as e:
            logger.error(f"Request failed: {e}")
            failures += 1

    async with aiohttp.ClientSession() as session:
        tasks = [make_request(session) for _ in range(total_requests)]
        await asyncio.gather(*tasks)

    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    total_requests = successes + failures
    success_rate = (successes / total_requests * 100) if total_requests > 0 else 0

    return {
        "total_requests": total_requests,
        "successes": successes,
        "failures": failures,
        "success_rate": success_rate,
        "avg_response_time": avg_response_time
    }

@pytest.mark.asyncio
async def test_simple_load():
    """Run a simple load test against a lightweight in-process server."""
    from aiohttp import web

    async def handle_root(request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    async def handle_healthz(request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    app = web.Application()
    app.add_routes([
        web.get('/', handle_root),
        web.get('/healthz', handle_healthz),
    ])

    runner = web.AppRunner(app)
    await runner.setup()
    # Bind to a free ephemeral port
    site = web.TCPSite(runner, '127.0.0.1', 0)
    await site.start()
    # Extract the actual bound port
    sockets = getattr(site, '_server').sockets
    port = sockets[0].getsockname()[1] if sockets else 0
    base_url = f"http://127.0.0.1:{port}"

    try:
        # Quick readiness check
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/healthz") as response:
                assert response.status == 200, "Health endpoint not ready"

        # Run load test
        logger.info("Starting load test...")
        results = await run_load_test(
            base_url=base_url,
            target_rps=NORMAL_TRAFFIC.target_rps,
            duration=NORMAL_TRAFFIC.duration_seconds
        )

        # Log results
        logger.info("\nTest Results:")
        logger.info(f"Total Requests: {results['total_requests']}")
        logger.info(f"Success Rate: {results['success_rate']:.2f}%")
        logger.info(f"Average Response Time: {results['avg_response_time']:.3f}s")

        # Assert test passed
        assert results['success_rate'] > 80, "Success rate below 80%"
        assert results['avg_response_time'] < 1.0, "Average response time too high"
    finally:
        await runner.cleanup()