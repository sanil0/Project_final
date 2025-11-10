"""Script to start the test server."""

import asyncio
from tests.load.test_server import HTTPServer

async def main():
    """Start the test server and wait for interrupt."""
    server = HTTPServer(host="127.0.0.1", port=8000)
    try:
        await server.start()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        await server.stop()
    except Exception as e:
        print(f"Error: {e}")
        await server.stop()
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
