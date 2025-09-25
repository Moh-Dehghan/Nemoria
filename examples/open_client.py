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

    # Connect
    if not await client.connect():
        return

    # Create data
    await client.set(route=Route("user", "profile", "name"), value="Alice")
    await client.set(route=Route("user", "profile", "age"), value=30)
    await client.save(codec="json", path="config.json", threadsafe=True)

    # Read data
    print(await client.get(route=Route("user", "profile", "name")))  # -> "Alice"
    print(await client.all())  # -> {'user': {'profile': {'name': 'Alice', 'age': 30}}}

    # Update data
    await client.set(
        route=Route("user", "profile", "age"),
        value=31,
        save_on_disk=True,
        codec="json",
        path="config.json",
        threadsafe=True,
    )  # -> 31
    print(await client.all())

    # Delete part of a route
    await client.delete(
        route=Route("user", "profile", "age"),
        save_on_disk=True,
        codec="json",
        path="config.json",
        threadsafe=True,
    )
    print(await client.all())

    # Drop the entire top-level route
    await client.drop(route=Route("user"))
    print(await client.all())  # -> {}

    await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
