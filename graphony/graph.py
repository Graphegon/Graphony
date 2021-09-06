"""
Graph objects
"""
import csv
from functools import lru_cache
from pickle import dumps, loads

import psycopg2 as pg

from .util import query
from .relation import Relation
from .node import Node


class Graph:
    """Graph objects"""

    _LRU_MAXSIZE = None

    def __init__(self, dsn, relations=None):
        self.graph = self
        self._conn = pg.connect(dsn)
        if relations is None:
            relations = {}
            with self._conn.cursor() as c:
                c.execute("select id, name, pytype from graphony.relation")
                for r in c.fetchall():
                    relations[r[0]] = Relation(self, r[0], r[1], loads(r[2]))
        self.relations = relations

    @lru_cache(maxsize=_LRU_MAXSIZE)
    @query
    def _upsert_node(self, curs):
        """
        INSERT INTO graphony.node (name, props)
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
    def _upsert_relation(self, curs):
        """
        INSERT INTO graphony.relation (name, pytype)
        VALUES (%s, %s)
        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """

    @lru_cache(maxsize=_LRU_MAXSIZE)
    @query
    def _get_relation_id(self, curs):
        """
        SELECT id FROM graphony.relation where name = %s
        """

    @lru_cache(maxsize=_LRU_MAXSIZE)
    @query
    def _get_relation_name(self, curs):
        """
        SELECT name FROM graphony.relation where id = %s
        """

    @query
    def _new_edge(self, curs):
        """
        INSERT INTO graphony.edge (props) VALUES (null) RETURNING id
        """

    def sql(self, sql_code):
        """Helper method to execute a SQL query and fetch results."""
        with self._conn.cursor() as c:
            c.execute(sql_code)
            return c.fetchall()

    def add_relation(self, name, weight_type=None, incidence=False):
        """Add a new relation"""
        rid = self._upsert_relation(name, dumps(weight_type))
        rel = Relation(self, rid, name, weight_type, incidence)
        self.relations[rid] = rel

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
        return sum(map(len, self.relations.values()))

    def __repr__(self):
        return f"<Graph [{', '.join([r.name for r in self.relations.values()])}]: {len(self)}>"

    def __iter__(self):
        return self()

    def __delitem__(self, key):
        source, relation, destination = key
        if source is not None:  # src, ?, ?
            sid = self[source]
            if relation is not None:  # src, relation, ?
                rel = self.relations[relation]
                if destination is not None:  # src, relation, dest
                    did = self[destination]
                    for _, eid in rel.A[sid]:
                        del rel.A[sid, eid]
                        del rel.B[eid, did]
                        return

                else:  # src, relation, None
                    pass

            else:  # src, None, ?
                if destination is not None:  # src, None, dest
                    pass
                else:  # src, None, None
                    pass
        elif relation is not None:  # None, relation, ?
            if destination is not None:  # None, relation, dest
                pass
            else:  # None, relation, None
                pass
        elif destination is not None:  # None, None, dest
            pass
        else:  # None, None, None
            for _, rel in self.relations.items():
                rel.A.clear()
                rel.B.clear()

    def __getattr__(self, name):
        rid = self._get_relation_id(name)
        if rid is None:
            raise AttributeError(name)
        return self.relations[rid]

    def __call__(self, relation=None, source=None, destination=None):
        """Query the graph for matching triples.

        Source, relation, and/or destination values can be provided, and
        triples that match the given values will be returned.  Passing
        no values will iterate all edges.

        """
        if source is not None:  # source,?,?
            sid = self[source]
            if relation is not None:  # source,relation,?
                rid = self._get_relation_id(relation)
                rel = self.relations[rid]

                if destination is not None:  # source,relation,destination
                    did = self[destination]
                    for edge in rel[sid, did]:
                        yield edge

                else:  # source,relation,None
                    for edge in rel[sid, :]:
                        yield edge
            else:
                if destination is not None:  # source,None,destination
                    did = self[destination]
                    for _, rel in self.relations.items():
                        for edge in rel[sid, did]:
                            yield edge

                else:  # source,None,None
                    for rid, rel in self.relations.items():
                        for edge in rel[sid, :]:
                            yield edge

        elif relation is not None:  # None,relation,?
            rid = self._get_relation_id(relation)
            rel = self.relations[rid]
            if destination is not None:  # None,relation,destination
                did = self[destination]
                for edge in rel[:, did]:
                    yield edge

            else:  # None,relation,None
                for edge in rel:
                    yield edge

        elif destination is not None:  # None,None,destination
            did = self[destination]
            for rid, rel in self.relations.items():
                for edge in rel[:, did]:
                    yield edge

        else:  # None,None,None
            for rid, rel in self.relations.items():
                for edge in rel:
                    yield edge


def read_csv(graph, fname, encoding="utf8", **kw):
    """Read a csv file and accuulate it into a graph"""

    with open(fname, encoding=encoding) as fd:
        rd = csv.reader(fd, **kw)
        for row in rd:
            if row:
                graph += tuple(row)
