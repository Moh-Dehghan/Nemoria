# Nemoria

**Nemoria** is a lightweight, asynchronous, in-memory datastore with with CRUD client-server architecture.  
It is designed for **fast prototyping, experiments, and educational use cases** where a minimal and hackable data layer is needed.  

✨ With Nemoria, you can **read and write data in real time** from **any process, thread, or program**, using multiple clients simultaneously.

Think of it as a tiny Redis-like system built entirely in Python/asyncio.

---

## Features

- 🚀 **Asynchronous I/O** powered by `asyncio`
- 🔑 **Password-based authentication**
- 🧩 **Nested routes** with hierarchical `Route` objects
- ⚡ **Simple CRUD API** (`get`, `all`, `set`, `delete`, `drop`, `purge`)
- 🔄 **Multi-client access** – read and write data in real time across any process, thread, or external program
- 🛠 **Minimalistic & extensible design** for custom protocols

---

## Installation

```bash
git clone https://github.com/moh-dehghan/nemoria.git
cd nemoria
pip install -e .
```

---

## Quick Start

### 1. Run the Server

```python
# server.py
import asyncio
from nemoria import Server

async def main():
    server = Server(host="localhost", port=1234, namespace="TEST", password="12345678")
    await server.run_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
```

Run it in one terminal:

```bash
python server.py
```

---

### 2. Connect a Client

```python
# client.py
import asyncio
from nemoria import Client, Route

async def main():
    client = Client(host="localhost", port=1234, password="12345678")
    await client.connect()

    # Create data
    await client.set(Route("user", "profile", "name"), "Alice")
    await client.set(Route("user", "profile", "age"), 30)

    # Read data
    print(await client.get(Route("user", "profile", "name")))  # -> "Alice"
    print(await client.all())  # -> {'user': {'profile': {'name': 'Alice', 'age': 30}}}

    # Update data
    await client.set(Route("user", "profile", "age"), 31)
    print(await client.get(Route("user", "profile", "age")))  # -> 31

    # Delete part of a route
    await client.delete(Route("user", "profile", "age"))
    print(await client.all())

    # Drop the entire top-level route
    await client.drop(Route("user"))
    print(await client.all())  # -> {}

    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
```

Run it in another terminal:

```bash
python client.py
```

---

## More Examples

### Storing Nested Data

```python
await client.set(Route("blog", "posts", "1", "title"), "Hello World")
await client.set(Route("blog", "posts", "1", "tags"), ["intro", "nemoria"])
await client.set(Route("blog", "posts", "2", "title"), "Async Rocks")

print(await client.all())
# {
#   "blog": {
#     "posts": {
#       "1": {"title": "Hello World", "tags": ["intro", "nemoria"]},
#       "2": {"title": "Async Rocks"}
#     }
#   }
# }
```

### Deleting & Dropping

```python
# Delete just one nested field
await client.delete(Route("blog", "posts", "1", "tags"))

# Drop entire "posts" subtree
await client.drop(Route("blog", "posts"))
```

---

## Development Notes

- Nemoria is intentionally **minimalistic** – it focuses on clarity and hackability.
- The project is written with **Python 3.10+** and `asyncio`.
- Perfect as a teaching tool for async networking, custom protocols, and in-memory data design.

---

## Roadmap

- [ ] Persistent storage (save/load to disk)  
- [ ] Pub/Sub messaging  
- [ ] Cluster mode (multi-server)  
- [ ] Advanced query language  

---

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
