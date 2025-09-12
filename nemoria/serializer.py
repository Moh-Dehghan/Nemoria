"""
Utilities to encode/decode *route segments* into a JSON-safe wire format.

Supported segment shapes:
- JSON primitives: `str`, `int`, `float`, `bool`, `None` (passed through)
- Tuples of supported segments (encoded as a tagged object)

Tuples are represented as:
    {"__t": "tuple", "v": [ ...encoded elements... ]}

Notes:
- These helpers are intentionally small. For non-tuple segments, `to_wire`
  does not verify JSON-serializability; callers should only pass JSON-safe
  values (or tuples thereof).
- Round-trip is guaranteed for supported values:
    from_wire(to_wire(x)) == x
"""

from __future__ import annotations

from typing import Hashable


def to_wire(seg: Hashable) -> object:
    """
    Serialize a single route segment into a JSON-safe form.

    Tuples are encoded recursively using the `{"__t": "tuple", "v": [...]}` tag.
    Other supported primitives (`str`, `int`, `float`, `bool`, `None`) are
    returned unchanged.

    Args:
        seg: Segment value to convert.

    Returns:
        A JSON-serializable object representing the segment.

    Examples:
        >>> to_wire(("a", 1, None))
        {'__t': 'tuple', 'v': ['a', 1, None]}
        >>> to_wire("user")
        'user'

    Notes:
        - Values like `bytes`, `frozenset`, or custom objects are not made
          JSON-safe here; avoid passing them (wrap/convert beforehand).
    """
    if isinstance(seg, tuple):
        # Encode tuple elements recursively so nested tuples are preserved
        return {"__t": "tuple", "v": [to_wire(s) for s in seg]}
    return seg  # JSON primitives are already wire-safe


def from_wire(node: object) -> Hashable:
    """
    Deserialize a JSON-safe node back into a route segment.

    Recognizes the `{"__t": "tuple", "v": [...]}` convention for tuples
    and decodes elements recursively. JSON primitives are returned as-is.

    Args:
        node: JSON-safe object to decode.

    Returns:
        The corresponding segment value (hashable), e.g. a tuple or a primitive.

    Raises:
        ValueError: If the node uses an invalid tuple tag or contains an
                    unsupported shape.

    Examples:
        >>> from_wire({'__t': 'tuple', 'v': ['a', 1, None]})
        ('a', 1, None)
        >>> from_wire(True)
        True
    """
    if isinstance(node, dict) and node.get("__t") == "tuple":
        v = node.get("v")
        if not isinstance(v, list):
            raise ValueError("invalid tuple tag payload")
        # Recursively decode each element back to a hashable value
        return tuple(from_wire(x) for x in v)  # type: ignore[return-value]

    if isinstance(node, (str, int, float, bool)) or node is None:
        return node

    # Any other shape is not a valid encoded segment
    raise ValueError("invalid segment element in route payload")
