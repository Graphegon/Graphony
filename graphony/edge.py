""" Edge and Hedge objects. """

from typing import NamedTuple, List
from .node import Node


class Edge(NamedTuple):
    """A simple Edge between one source and one destination node."""

    graph: object
    rid: int
    sid: int
    did: int
    weight: object = True
    eid: int = None

    def __repr__(self):
        if self.weight and isinstance(self.weight, bool):
            weight = ""
        else:
            weight = f", {self.weight}"
        return f"{self.relation.name}({self.source}, {self.destination}{weight})"

    @property
    def relation(self):
        """Return edge relation."""
        return self.graph.relations[self.rid]

    @property
    def source(self):
        """Return edge source."""
        return Node(self.graph, self.sid)

    @property
    def destination(self):
        """Return edge destination"""
        return Node(self.graph, self.did)


class Hedge(NamedTuple):
    """A hyperedge (Hedge) can connect multiple source nodes to multiple
    destination nodes.

    """

    graph: object
    rid: int
    sids: List[int]
    dids: List[int]
    weights: List[object] = None
    eid: int = None

    def __repr__(self):
        sources = ", ".join(map(str, self.sources))
        destinations = ", ".join(map(str, self.destinations))
        weights = ", ".join(map(str, self.weights))
        return f"{self.relation.name}(({sources}), ({destinations}), ({weights}))"

    @property
    def relation(self):
        """Return edge relation."""
        return self.graph.relations[self.rid]

    @property
    def sources(self):
        """Return edge sources."""
        return [Node(self.graph, sid) for sid in self.sids]

    @property
    def destinations(self):
        """Return edge destinations."""
        return [Node(self.graph, did) for did in self.dids]
