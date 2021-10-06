""" Node objects. """


from psycopg2.extras import Json
from .util import query


class Node:
    """
    Node object.
    """

    __slots__ = ("graph", "n_id")

    def __init__(self, graph, n_id, **attrs):
        if isinstance(n_id, str):
            n_id = graph._upsert_node(n_id, Json(attrs))

        self.graph = graph
        self.n_id = n_id

    def __str__(self):
        return self.name

    @property
    @query
    def attrs(self, curs):
        """
        SELECT attrs from graphony.node where id = {self.n_id}
        """

    @property
    def name(self):
        """Lookup and return node name."""
        return self.graph._get_node_name(self.n_id)

    def __repr__(self):
        return self.name

    def __getattr__(self, name):
        try:
            return self.attrs[name]
        except KeyError:
            raise AttributeError
