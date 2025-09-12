"""
Test Script for Nemoria Client
===============================

This script demonstrates how to interact with the Nemoria server using the
high-level `Client` API. It performs basic CRUD operations on nested routes
to validate correct behavior of the client-server communication.

Steps:
    1. Connect to the Nemoria server at localhost:1234
    2. Create a nested route ("one/two/3") and set its value
    3. Display all stored keys/values
    4. Delete an intermediate route ("one/two")
    5. Display all keys/values again
    6. Drop the top-level route ("one")
    7. Display all keys/values again
    8. Keep the client running until interrupted (Ctrl+C)
"""

import asyncio
from nemoria import Client, Route


async def main():
    """
    Main test routine.

    This coroutine connects a `Client` to the server, demonstrates
    setting, deleting, and dropping routes, and prints the state
    of the datastore after each operation.
    """
    client = Client(host="localhost", port=1234, password="12345678")

    await client.connect()

    # Set value at nested route: one/two/3 = 4
    route = Route("one", "two", "3")
    await client.set(route, 4)
    print(await client.all())

    # Delete intermediate route: one/two
    await client.delete(Route("one", "two"))
    print(await client.all())

    # Drop top-level route: one
    await client.drop(Route("one"))
    print(await client.all())

    # Keep alive until manual interruption
    await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
