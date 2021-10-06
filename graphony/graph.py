"""
Graph objects
"""
import csv
from functools import lru_cache
from pickle import dumps, loads

import psycopg2 as pg

from .util import query
from .property import Property
from .node import Node


class Graph:
    """Graph objects"""

    _LRU_MAXSIZE = None

    def __init__(self, dsn, properties=None):
        self.graph = self
        self._conn = pg.connect(dsn)
        if properties is None:
            properties = {}
            with self._conn.cursor() as c:
                c.execute("select id, name, pytype from graphony.property")
                for r in c.fetchall():
                    properties[r[0]] = Property(self, r[0], r[1], loads(r[2]))
        self.properties = properties

    @lru_cache(maxsize=_LRU_MAXSIZE)
    @query
    def _upsert_node(self, curs):
        """
        INSERT INTO graphony.node (name, attrs)
        VALUES (%s, %s)
        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """

    @lru_cache(maxsize=_LRU_MAXSIZE)
    @query
    def _get_node_id(self, curs):
        """
        SELECT id FROM graphony.node where name = %s
        """

    @lru_cache(maxsize=_LRU_MAXSIZE)
    @query
    def _get_node_name(self, curs):
        """
        SELECT name FROM graphony.node where id = %s
        """

    @lru_cache(maxsize=_LRU_MAXSIZE)
    @query
    def _upsert_property(self, curs):
        """
        INSERT INTO graphony.property (name, pytype)
        VALUES (%s, %s)
        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """

    @lru_cache(maxsize=_LRU_MAXSIZE)
    @query
    def _get_property_id(self, curs):
        """
        SELECT id FROM graphony.property where name = %s
        """

    @lru_cache(maxsize=_LRU_MAXSIZE)
    @query
    def _get_property_name(self, curs):
        """
        SELECT name FROM graphony.property where id = %s
        """

    @query
    def _new_edge(self, curs):
        """
        INSERT INTO graphony.edge (attrs) VALUES (null) RETURNING id
        """

    def sql(self, sql_code):
        """Helper method to execute a SQL query and fetch results."""
        with self._conn.cursor() as c:
            c.execute(sql_code)
            return c.fetchall()

    def get_node(self, name):
        if isinstance(name, Node):
            return name
        return Node(self.graph, name)

    def add_property(self, name, weight_type=None, incidence=False):
        """Add a new property"""
        rid = self._upsert_property(name, dumps(weight_type))
        rel = Property(self, rid, name, weight_type, incidence)
        self.properties[rid] = rel

    def __getitem__(self, key):
        if isinstance(key, int):
            n_id = self._get_node_name(key)
        else:
            n_id = self._get_node_id(key)
        if n_id is None:
            raise KeyError(key)
        return n_id

    def __len__(self):
        """Returns the number of triples in the graph."""
        return sum(map(len, self.properties.values()))

    def __repr__(self):
        return f"<Graph [{', '.join([r.name for r in self.properties.values()])}]: {len(self)}>"

    def __iter__(self):
        return self()

    def __delitem__(self, key):
        source, property, destination = key
        if source is not None:  # src, ?, ?
            sid = self[source]
            if property is not None:  # src, property, ?
                rel = self.properties[property]
                if destination is not None:  # src, property, dest
                    did = self[destination]
                    for _, eid in rel.A[sid]:
                        del rel.A[sid, eid]
                        del rel.B[eid, did]
                        return

                else:  # src, property, None
                    pass

            else:  # src, None, ?
                if destination is not None:  # src, None, dest
                    pass
                else:  # src, None, None
                    pass
        elif property is not None:  # None, property, ?
            if destination is not None:  # None, property, dest
                pass
            else:  # None, property, None
                pass
        elif destination is not None:  # None, None, dest
            pass
        else:  # None, None, None
            for _, rel in self.properties.items():
                rel.A.clear()
                rel.B.clear()

    def __getattr__(self, name):
        rid = self._get_property_id(name)
        if rid is None:
            raise AttributeError(name)
        return self.properties[rid]

    def __call__(self, property=None, source=None, destination=None):
        """Query the graph for matching triples.

        Source, property, and/or destination values can be provided, and
        triples that match the given values will be returned.  Passing
        no values will iterate all edges.

        """
        if source is not None:  # source,?,?
            sid = self[source]
            if property is not None:  # source,property,?
                rid = self._get_property_id(property)
                rel = self.properties[rid]

                if destination is not None:  # source,property,destination
                    did = self[destination]
                    for edge in rel[sid, did]:
                        yield edge

                else:  # source,property,None
                    for edge in rel[sid, :]:
                        yield edge
            else:
                if destination is not None:  # source,None,destination
                    did = self[destination]
                    for _, rel in self.properties.items():
                        for edge in rel[sid, did]:
                            yield edge

                else:  # source,None,None
                    for rid, rel in self.properties.items():
                        for edge in rel[sid, :]:
                            yield edge

        elif property is not None:  # None,property,?
            rid = self._get_property_id(property)
            rel = self.properties[rid]
            if destination is not None:  # None,property,destination
                did = self[destination]
                for edge in rel[:, did]:
                    yield edge

            else:  # None,property,None
                for edge in rel:
                    yield edge

        elif destination is not None:  # None,None,destination
            did = self[destination]
            for rid, rel in self.properties.items():
                for edge in rel[:, did]:
                    yield edge

        else:  # None,None,None
            for rid, rel in self.properties.items():
                for edge in rel:
                    yield edge

    def draw(self, **kwargs):
        g = None
        for rid in self.properties:
            rel = self.properties[rid]
            kwargs["weight_prefix"] = f"{rel.name}: "
            g = rel.draw(g=g, **kwargs)
        return g


def read_csv(graph, fname, encoding="utf8", **kw):
    """Read a csv file and accuulate it into a graph"""

    with open(fname, encoding=encoding) as fd:
        rd = csv.reader(fd, **kw)
        for row in rd:
            if row:
                graph += tuple(row)
