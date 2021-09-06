""" Edge objects. """

from typing import NamedTuple
from .node import Node


class Edge(NamedTuple):
    """A hyperedge between graph nodes."""

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
