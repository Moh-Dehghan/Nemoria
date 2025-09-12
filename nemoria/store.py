"""
An async-safe nested key-value store with per-route locks (flat lock map).

This module keeps the data (`db`) as nested dicts, while per-route locks are
stored in a flat dict keyed by the route. A meta-lock (`locks_guard`) serializes
lock creation so concurrent tasks don't create two different locks for the same route.

Typical usage:
    store = Store()
    await store.set(Route("users", "42", "name"), "Alice")
    name = await store.get(Route("users", "42", "name"))
    await store.delete(Route("users", "42"))      # collapses parent to None
    await store.drop(Route("users"))              # prunes empty ancestors
"""

from __future__ import annotations

import asyncio
from typing import Optional, Any, Hashable, MutableMapping, Dict
from nemoria.route import Route


class Store:
    """
    Task-safe nested store for asyncio workloads with a flat lock map.

    Data is held under `self.db` as a nested dict. Per-route locks are kept in
    a flat map `self.locks` keyed by the route (or a stable key for it).
    To avoid races during on-demand lock creation, `locks_guard` protects the
    check-then-create sequence.

    Notes:
        - `get()` returns `None` if the route is missing.
        - `set()` auto-creates intermediate dicts along the route.
        - `delete()` removes the target subtree and collapses its parent to `None` if empty.
        - `drop()` removes the target key and prunes empty parents bottom-up.
        - Locks are created lazily on first use of a route.
    """

    def __init__(self) -> None:
        """
        Initialize empty data and lock maps.

        Creates:
            - `db`: the nested data dictionary.
            - `locks`: the flat lock dictionary (Route-keyed).
            - `locks_guard`: a meta-lock used only to serialize lock creation.
        """
        self.db: Dict[Hashable, Any] = {}
        self.locks: Dict[Hashable, asyncio.Lock] = {}  # flat: Route (or key) -> Lock
        self.locks_guard = asyncio.Lock()  # guards lock creation

    async def lock(self, route: Route) -> asyncio.Lock:
        """
        Get or create the per-route lock.

        Fast path: return an existing lock from `locks`.
        Slow path: under `locks_guard`, create the lock if missing.
        This method never raises due to lock lookup.
        """

        # Fast path
        lock = self.locks.get(route)
        if lock is not None:
            return lock

        # Slow path: serialize creation to avoid duplicates
        async with self.locks_guard:
            return self.locks.setdefault(route, asyncio.Lock())

    async def get(self, route: Route) -> Optional[Any]:
        """
        Read a value at `route` (returns `None` if missing).

        The per-route lock is acquired to serialize with concurrent writers.

        Args:
            route: Path to read from.

        Returns:
            Stored value, or `None` if the route doesn't exist.
        """
        async with await self.lock(route):
            try:
                return self._get(self.db, route)
            except KeyError:
                return None

    async def all(self) -> Dict[Hashable, Any]:
        """
        Return the internal data dictionary **by reference**.

        Warning:
            This returns the live underlying dict; external code can mutate it
            without going through `set()`/`delete()` and therefore without locking.
            Prefer a read-only snapshot in production.

        Returns:
            The internal `db` dictionary (live reference).
        """
        return self.db

    async def set(self, route: Route, value: Any) -> None:
        """
        Write `value` at `route`, creating intermediate dicts as needed.

        The per-route lock is acquired before writing. Exceptions from `_set()`
        (e.g., empty route or type mismatch) are currently swallowed—consider
        logging or re-raising in production.

        Args:
            route: Path to write to.
            value: Value to store at the final segment.
        """
        async with await self.lock(route):
            try:
                self._set(self.db, route, value)
            except (ValueError, TypeError):
                pass  # TODO: log or re-raise per your error policy

    async def delete(self, route: Route) -> None:
        """
        Delete the subtree at `route`, collapsing its parent to `None` if empty.

        Semantics:
            - Remove the target subtree (key and its descendants).
            - If the *immediate parent* becomes empty, replace that parent
              (in its own parent) with `None`.
            - No ancestor pruning beyond the immediate parent.
            - Top-level special case: `delete(["k"])` sets `db["k"] = None`.

        This method is a no-op if the path does not exist.
        """
        async with await self.lock(route):
            try:
                self._delete(self.db, route, drop=False)
            except ValueError:
                pass

    async def drop(self, route: Route) -> None:
        """
        Drop the key at `route` entirely and prune empty ancestors upwards.

        Semantics:
            - Remove the target key itself (and its subtree, if any).
            - If any parent becomes empty, remove it too (recursive prune).

        This method is a no-op if the path does not exist.
        """
        async with await self.lock(route):
            try:
                self._delete(self.db, route, drop=True)
            except ValueError:
                pass

    async def purge(self) -> None:
        """
        Clear all data and all locks.

        Guarded by `locks_guard` to provide a consistent reset.
        """
        async with self.locks_guard:
            self.db.clear()
            self.locks.clear()

    @staticmethod
    def _get(obj: MutableMapping[Hashable, Any], route: Route) -> Any:
        """
        Traverse `obj` by `route` and return the value.

        Args:
            obj: Root mapping to traverse.
            route: Successive keys used to descend.

        Returns:
            Value at the end of the route.

        Raises:
            KeyError: If any segment is missing.
        """
        cur: Any = obj
        for seg in route:
            if isinstance(cur, MutableMapping) and seg in cur:
                cur = cur[seg]
            else:
                raise KeyError(seg)
        return cur

    @staticmethod
    def _set(
        obj: MutableMapping[Hashable, Any],
        route: Route,
        value: Any,
    ) -> None:
        """
        Set `value` at `route` inside `obj`, creating parents as needed.

        Args:
            obj: Root mapping to modify.
            route: Path to set.
            value: Value to assign.

        Raises:
            ValueError: If `route` is empty.
            TypeError: If a non-mapping is encountered on the path.
        """
        if len(route) == 0:
            raise ValueError("route cannot be empty")

        cur: Any = obj
        for seg in route[:-1]:
            if not isinstance(cur, MutableMapping):
                raise TypeError(f"expected mapping at segment {seg!r}")
            if seg not in cur:
                cur[seg] = {}  # auto-create intermediate dict
            cur = cur[seg]

        if not isinstance(cur, MutableMapping):
            raise TypeError(f"expected mapping at final parent for {route[-1]!r}")
        cur[route[-1]] = value

    @staticmethod
    def _delete(
        obj: MutableMapping[Hashable, Any],
        route: Route,
        drop: bool = False,
    ) -> None:
        """
        Core delete logic used by `delete()` and `drop()`.

        Modes:
            - drop=True  : remove key; prune empty parents bottom-up.
            - drop=False : remove subtree; if the immediate parent becomes empty,
                           replace that parent (in its own parent) with `None`.
                           Special-case: when len(route)==1 -> obj[key] = None.

        Behavior:
            - Missing/malformed paths are silent no-ops.
            - Empty route raises ValueError.
        """
        if len(route) == 0:
            raise ValueError("route cannot be empty")

        # Top-level special case for delete-mode
        if not drop and len(route) == 1:
            obj[route[0]] = None
            return

        # Walk to the parent of the target key
        cur: Any = obj
        parents: list[MutableMapping[Hashable, Any]] = []
        keys: list[Hashable] = []
        for seg in route[:-1]:
            if not isinstance(cur, MutableMapping) or seg not in cur:
                return  # no-op if path missing
            parents.append(cur)
            keys.append(seg)
            cur = cur[seg]

        if not isinstance(cur, MutableMapping):
            return  # malformed path → no-op

        target = route[-1]
        if target not in cur:
            return  # nothing to delete

        # Remove the target subtree (or leaf)
        cur.pop(target)

        if drop:
            # Prune empty parents bottom-up
            node = cur
            for gp, k in zip(reversed(parents), reversed(keys)):
                if isinstance(node, MutableMapping) and not node:
                    gp.pop(k, None)
                    node = gp
                else:
                    break
        else:
            # Collapse only the immediate parent to None if it became empty
            if not cur and parents:
                gp = parents[-1]
                key_of_parent = keys[-1]
                gp[key_of_parent] = None
