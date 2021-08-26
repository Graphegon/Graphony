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
        return (
            f"({self.relation.name}, {self.source}, {self.destination}, {self.weight})"
        )

    @property
    def relation(self):
        return self.graph.relations[self.rid]

    @property
    def source(self):
        return Node(self.graph, self.sid)

    @property
    def destination(self):
        return Node(self.graph, self.did)
