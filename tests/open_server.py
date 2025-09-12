"""
Test Server for Nemoria
=======================

This script launches a Nemoria server instance for local testing.
It is intended to be used together with the `open_client.py` script
to validate the full client-server interaction.

Features:
    • Binds to localhost on port 1234
    • Uses a dedicated namespace "TEST"
    • Requires password authentication ("12345678")
    • Runs indefinitely until interrupted (Ctrl+C)

Usage:
    1. Run this server in one terminal:
           $ python open_server.py
    2. Run the client test script in another terminal:
           $ python open_client.py
    3. Observe the client performing CRUD operations
       and verify server behavior.
"""

import asyncio
from nemoria import Server


async def main():
    """
    Main entry point for the test server.

    Creates a `Server` instance bound to localhost:1234 with
    namespace "TEST" and password "12345678", then runs it
    until a KeyboardInterrupt is received.
    """
    server = Server(
        host="localhost",
        port=1234,
        namespace="TEST",
        password="12345678",
    )
    await server.run_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
