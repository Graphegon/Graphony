from psycopg2.extras import Json


class Node:
    """
    Node object.
    """

    __slots__ = ("graph", "n_id", "props")

    def __init__(self, graph, n_id, **props):
        if isinstance(n_id, str):
            n_id = graph._upsert_node(n_id, Json(props))

        self.graph = graph
        self.n_id = n_id
        self.props = props

    @property
    def name(self):
        return self.graph._get_node_name(self.n_id)

    def __repr__(self):
        return self.name
