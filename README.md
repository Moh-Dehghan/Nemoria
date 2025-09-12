# Nemoria
[![PyPI version](https://badge.fury.io/py/nemoria.svg)](https://pypi.org/project/nemoria/)
[![Python Versions](https://img.shields.io/pypi/pyversions/nemoria.svg)](https://pypi.org/project/nemoria/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Nemoria** is a lightweight, asynchronous, in-memory datastore with secure client-server protocol, supporting real-time multi-client CRUD operations. 
It is designed for **fast prototyping, experiments, and educational use cases** where a minimal and hackable data layer is needed.  

✨ With Nemoria, you can **read and write data in real time** from **any process, thread, or program**, using multiple clients simultaneously.

Think of it as a tiny Redis-like system built entirely in Python/asyncio.

---

## Features

- 🚀 **Asynchronous I/O** powered by `asyncio`
- 🔑 **Password-based authentication**
- 🧩 **Nested routes** with hierarchical `Route` objects
- ⚡ **Simple CRUD API** (`get`, `all`, `set`, `delete`, `drop`, `purge`, `ping`)
- 🔄 **Multi-client access** – read and write data in real time across any process, thread, or external program
- 🛠 **Minimalistic & extensible design** for custom protocols

---

## Installation

### A) Install from PyPI
```bash
pip install nemoria
```

---

### B) Local source install
```bash
git clone https://github.com/moh-dehghan/nemoria.git
cd nemoria
pip install -e .
```

---

### C) Install from built distributions (dist/)

**Wheel (recommended)**
```bash
pip install dist/nemoria-1.0.0-py3-none-any.whl
```

**Or Source tarball**
```bash
pip install dist/nemoria-1.0.0.tar.gz
```

---

### Verification
Check if the package is installed correctly:
```bash
python -c "import nemoria; print(nemoria.__version__)"
```
Or:
```python
import nemoria
print(nemoria.__version__)
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

    # Run server
    await server.run_forever(raise_on_error=False)

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
    
    # Connect
    if not await client.connect():
        return

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

### Deleting & Dropping & Purging

```python
# Delete just one nested field
await client.delete(Route("blog", "posts", "1", "tags"))

# Drop entire "posts" subtree
await client.drop(Route("blog", "posts"))

# Clear entire datastore
await client.purge()
```

### Ping & Healthcheck

```python
# Ping
print(await client.ping()) # -> Latency in milliseconds, or `None` on timeout/connection error.

# Healthcheck
print(await client.is_alive()) # -> True or False

```

---

## Development Notes

Nemoria is intentionally designed to be **minimalistic yet extensible**, with a focus on clarity, hackability, and serving as an educational reference.  

- 🧩 **Architecture**:  
  The system follows a clear client–server separation.  
  - `Server`: manages connections, authentication, and route-based storage.  
  - `Client`: provides a high-level API for CRUD operations and route traversal.  
  - `Route`: represents nested hierarchical keys for structured data access.  

- ⚙️ **Technology Stack**:  
  - Implemented in **Python 3.10+** using `asyncio` for fully asynchronous I/O.  
  - Built around standard Python libraries to keep dependencies minimal.  
  - Supports multiple concurrent clients with real-time access guarantees.  

- 🎯 **Design Goals**:  
  - Prioritize **readability** and **hackability** over heavy optimizations.  
  - Provide a safe playground for learning about async networking and protocol design.  
  - Allow easy extension for advanced features like persistence, clustering, and pub/sub.  

- 🛠 **Intended Use**:  
  - Great for **fast prototyping** when you need a lightweight datastore.  
  - Suitable for **experiments** in distributed systems and protocol design.  
  - Serves as a **teaching tool** for learning asyncio, client-server patterns, and hierarchical data structures.  

---

## Roadmap

- [ ] Persistent storage (save/load to disk)  
- [ ] Pub/Sub messaging  
- [ ] Cluster mode (multi-server)  
- [ ] Advanced query language  

---

## Educational Use

Nemoria is not only a functional datastore, but also an **educational resource**.  
It is particularly valuable for:  

- 📚 **Students & Learners**: Understanding how asynchronous servers and clients communicate.  
- 🧑‍💻 **Developers**: Experimenting with custom protocols, networking, and route-based data models.  
- 🏫 **Educators**: Demonstrating practical concepts of `asyncio`, event loops, and concurrency in Python.  

---

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
