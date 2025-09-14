"""
Immutable, hashable route type with compact wire encoding.

`Route` models a navigable path made of hashable *segments* (e.g., keys or
indices) to address locations inside nested structures (JSON-like objects,
in-memory stores, etc.). It supports:

- Construction from arbitrary hashable segments
- Path extension via the `/` operator
- Compact Base64URL encoding/decoding (tuples preserved via tagged JSON)
- Friendly string/repr formats, iteration, slicing, and hashing

Round-trip property (for supported segments):
    Route.decode(Route(...).encode()) == Route(...)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Union, Hashable, Tuple, Iterator, Self, overload
from nemoria.cryptography import b64u_encode, b64u_decode
from nemoria.serializer import from_wire, to_wire


@dataclass(frozen=True, slots=True)
class Route:
    """
    Represents a navigable path composed of hashable segments.

    A route is essentially a tuple of "segments" (keys/indices) that identify
    a location inside a nested structure (like a JSON object or in-memory store).

    Segment types:
        - `str`, `int`, `float`, `bool`, `None`
        - `tuple` of segments (recursively nested)

    Features:
        - Encodes/decodes to a compact Base64URL string (tuples preserved).
        - Supports `/` operator to extend the path.
        - String/repr form: `<root><a><1><b>`
    """

    segments: Tuple[Hashable, ...]

    def __init__(self, *segments: Hashable) -> None:
        """
        Initialize a new `Route`.

        Args:
            *segments: Path components (must be hashable).

        Raises:
            TypeError: If any segment is not hashable.
        """
        if not all(isinstance(s, Hashable) for s in segments):
            raise TypeError("Route segments must be Hashable")
        # `frozen=True` -> use object.__setattr__ to set the field
        object.__setattr__(self, "segments", tuple(segments))

    def encode(self) -> str:
        """
        Encode this route into a Base64URL string.

        Implementation details:
            - Each segment is converted to a JSON-safe node via `to_wire`.
            - The list is JSON-serialized with compact separators.
            - The bytes are encoded using Base64URL (no padding differences).

        Returns:
            Base64URL string representing this route.

        Example:
            >>> Route("a", ("b", 1)).encode()
            'eyJfX3QiOiJ0dXBsZSIsInYiOlsiYSIseyJfX3QiOiJ0dXBsZSIsInYiOlsiYiIsMV19XX0'  # doctest: +ELLIPSIS
        """
        payload = [to_wire(s) for s in self.segments]
        data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
        return b64u_encode(data)

    @classmethod
    def decode(cls, token: str) -> Self:
        """
        Decode a Base64URL string back into a `Route`.

        Args:
            token: The Base64URL string produced by `encode()`.

        Returns:
            A reconstructed `Route` instance.

        Raises:
            ValueError: If the payload is not a valid encoded route.
        """
        raw = b64u_decode(token)
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, list):
            raise ValueError("invalid route payload (expected JSON array)")
        segs: Tuple[Hashable, ...] = tuple(from_wire(x) for x in payload)
        return cls(*segs)

    def __truediv__(self, other: Hashable) -> Self:
        """
        Return a new route extended by one segment using `/`.

        Example:
            >>> Route("a") / "b"
            <root><a><b>
        """
        return Route(*self.segments, other)

    def __str__(self) -> str:
        """
        Return a human-readable compact form.

        Example:
            >>> str(Route("a", "b", ("c", 4)))
            '<root><a><b><(c, 4)>'
        """
        return "<root>" + "".join(f"<{s}>" for s in self.segments)

    def __repr__(self) -> str:
        """
        Return the same compact form as `__str__`.

        Useful for logs and debugging.
        """
        return str(self)

    def __len__(self) -> int:
        """
        Return the number of segments in this route.
        """
        return len(self.segments)

    def __iter__(self) -> Iterator[Hashable]:
        """
        Iterate over the segments in order (left to right).
        """
        return iter(self.segments)

    @overload
    def __getitem__(self, idx: int) -> Hashable: ...
    @overload
    def __getitem__(self, idx: slice) -> Self: ...

    def __getitem__(self, idx: Union[int, slice]) -> Union[Hashable, Self]:
        """
        Index or slice the route.

        - Integer index returns a single segment.
        - Slice returns a new `Route` containing the subsequence.

        Examples:
            >>> r = Route("a", "b", "c")
            >>> r[1]
            'b'
            >>> r[0:2]
            <root><a><b>
        """
        if isinstance(idx, slice):
            return Route(*self.segments[idx])
        return self.segments[idx]

    def __contains__(self, item: Hashable) -> bool:
        """
        Return `True` if a segment exists in this route.
        """
        return item in self.segments

    def __reversed__(self) -> Iterator[Hashable]:
        """
        Iterate over the segments in reverse order (right to left).
        """
        return reversed(self.segments)

    def __eq__(self, other: object) -> bool:
        """
        Compare routes by their segment tuples.

        Returns:
            `NotImplemented` if `other` is not a `Route`; otherwise
            a boolean equality result.
        """
        if not isinstance(other, Route):
            return NotImplemented
        return self.segments == other.segments

    def __hash__(self) -> int:
        """
        Hash by the underlying segment tuple.

        This makes `Route` usable as keys in dicts and members of sets.
        """
        return hash(self.segments)
