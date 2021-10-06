""" Edge and Hedge objects. """

from typing import NamedTuple, List
from .node import Node


class Edge(NamedTuple):
    """A simple Edge between one source and one destination node."""

    property: object
    sid: int
    did: int
    weight: object = True
    eid: int = None

    def __repr__(self):
        if self.weight and isinstance(self.weight, bool):
            weight = ""
        else:
            weight = f", {self.weight}"
        return f"{self.property.name}({self.source}, {self.destination}{weight})"

    @property
    def source(self):
        """Return edge source."""
        return Node(self.property.graph, self.sid)

    @property
    def destination(self):
        """Return edge destination"""
        return Node(self.property.graph, self.did)


class Hedge(NamedTuple):
    """A hyperedge (Hedge) can connect multiple source nodes to multiple
    destination nodes.

    """

    property: object
    sids: List[int]
    dids: List[int]
    weights: List[object] = None
    eid: int = None

    def __repr__(self):
        sources = ", ".join(map(str, self.sources))
        destinations = ", ".join(map(str, self.destinations))
        weights = ", ".join(map(str, self.weights))
        return f"{self.property.name}(({sources}), ({destinations}), ({weights}))"

    @property
    def sources(self):
        """Return edge sources."""
        g = self.property.graph
        return [Node(g, sid) for sid in self.sids]

    @property
    def destinations(self):
        """Return edge destinations."""
        g = self.property.graph
        return [Node(g, did) for did in self.dids]
