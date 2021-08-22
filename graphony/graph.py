from typing import NamedTuple
from collections import OrderedDict
from operator import attrgetter
from functools import lru_cache
import psycopg2 as pg

from .util import lazy, curse, query

import pygraphblas as gb
from pygraphblas import Matrix, Vector, BOOL, INT64
from pygraphblas.base import NoValue


class Graph:
    """A GraphBLAS-backed multiple property graph.

    A graph consists of a set of nodes connected by edges.  Each
    matrix stores a property relation between graph edges.

    Each unique relation is stored as an adjacency matrix from sources
    to destinations.  To demonstrate, first create a helper function
    `p()` that will iterate results into a list and "pretty print"
    them.

    >>> import pprint
    >>> p = lambda r: pprint.pprint(sorted(list(r)))

    Now construct a graph that is connected to a database.  Shown here
    is an in-memory sqlite database for demostration purposes:

    >>> G = Graph('postgres://postgres:postgres@localhost:5433/graphony')

    Relation tuples can be added directly into the Graph with the `+=`
    method.

    >>> G += ('friend', 'bob', 'alice')
    >>> G += ('friend', 'alice', 'jane')

    Or an iterator of relation tuples can be provided:

    >>> G += [('coworker', 'bob', 'jane'), ('coworker', 'alice', 'jane')]

    Inspecting G shows that it has two columns and four edges:

    >>> G
    <Graph [friend, coworker]: 4>

    The graph can then be called like `G(...)` to examine it.  A query
    consists of three optional arguments for `src`, `relation` and
    `dest`.  The default value for all three is None, which acts as a
    wildcard to matches all values.

    >>> p(G())
    [friend(bob -> alice: True),
     friend(alice -> jane: True),
     coworker(bob -> jane: True),
     coworker(alice -> jane: True)]

    Only print relations where `bob` is the src:

    >>> p(G(src='bob'))
    [friend(bob -> alice: True), coworker(bob -> jane: True)]

    Only print relations where `coworker` is the relation:

    >>> p(G(relation='coworker'))
    [coworker(bob -> jane: True), coworker(alice -> jane: True)]

    Only print relations where `jane` is the dest:

    >>> p(G(dest='jane'))
    [friend(alice -> jane: True),
     coworker(bob -> jane: True),
     coworker(alice -> jane: True)]

    >>> p(G(src='bob', relation='coworker', dest='jane'))
    [coworker(bob -> jane: True)]

    Relations are accessible as attributes of the graph:

    >>> G.friend
    <BOOL friend: 2>
    >>> G.coworker
    <BOOL coworker: 2>

    Relations can be iterated directly:

    >>> p(list(G.friend))
    [friend(bob -> alice: True), friend(alice -> jane: True)]

    >>> G += [('distance', 'chicago', 'seatle', 422),
    ...       ('distance', 'seattle', 'portland', 42)]

    >>> p(list(G))
    [friend(bob -> alice: True),
     friend(alice -> jane: True),
     coworker(bob -> jane: True),
     coworker(alice -> jane: True),
     distance(chicago -> seatle: 422),
     distance(seattle -> portland: 42)]

    """

    _LRU_MAXSIZE = None

    def __init__(self, dsn, max_cache_size=None):
        self.graph = self
        self._dsn = dsn
        self._conn = pg.connect(self._dsn)
        self._relations = {}

    @lru_cache(maxsize=_LRU_MAXSIZE)
    @query
    def _upsert_node(self, curs):
        """
        INSERT INTO graphony.node (n_name)
        VALUES (%s)
        ON CONFLICT (n_name) DO UPDATE SET n_name = EXCLUDED.n_name
        RETURNING n_id
        """

    @lru_cache(maxsize=_LRU_MAXSIZE)
    @query
    def _get_node_id(self, curs):
        """
        SELECT n_id FROM graphony.node where n_name = %s
        """

    @lru_cache(maxsize=_LRU_MAXSIZE)
    @query
    def _get_node_name(self, curs):
        """
        SELECT n_name FROM graphony.node where n_id = %s
        """

    @lru_cache(maxsize=_LRU_MAXSIZE)
    @query
    def _upsert_relation(self, curs):
        """
        INSERT INTO graphony.relation (r_name)
        VALUES (%s)
        ON CONFLICT (r_name) DO UPDATE SET r_name = EXCLUDED.r_name
        RETURNING r_id
        """

    @lru_cache(maxsize=_LRU_MAXSIZE)
    @query
    def _get_relation_id(self, curs):
        """
        SELECT r_id FROM graphony.relation where r_name = %s
        """

    @lru_cache(maxsize=_LRU_MAXSIZE)
    @query
    def _get_relation_name(self, curs):
        """
        SELECT r_name FROM graphony.relation where r_id = %s
        """

    @query
    def _new_edge(self, curs):
        """
        INSERT INTO graphony.edge (e_props) VALUES (null) RETURNING e_id
        """

    def _add(self, relation, src, dest, weight=True, eid=None):
        """Add an edge to the graph with an optional weight."""
        if not relation.isidentifier() or relation.startswith("_"):
            assert NameError(
                "relation name must start with a letter, "
                "and can only contain letters, numbers, and underscores"
            )
        rid = self._upsert_relation(relation)
        sid = self._upsert_node(src)
        did = self._upsert_node(dest)
        if eid is None:
            eid = self._new_edge()

        if rid not in self._relations:
            rel = Relation(self, rid, relation, type(weight))
            self._relations[rid] = rel
        else:
            rel = self._relations[rid]

        rel.add(sid, eid, did, weight)

    def __getitem__(self, key):
        id = self._get_node_id(key)
        if id is None:
            raise KeyError(key)
        return id

    def __iadd__(self, relation):
        if isinstance(relation, tuple):
            self._add(*relation)
        elif isinstance(relation, Graph):
            raise TypeError("todo")
        else:
            for i in relation:
                self._add(*i)
        return self

    def __len__(self):
        """Returns the number of triples in the graph."""
        return sum(map(attrgetter("B.nvals"), self._relations.values()))

    def __repr__(self):
        return f"<Graph [{', '.join([r.name for r in self._relations.values()])}]: {len(self)}>"

    def __iter__(self):
        return self(weighted=True)

    def __getattr__(self, name):
        rid = self._get_relation_id(name)
        if rid is None:
            raise AttributeError(name)
        return self._relations[rid]

    def __call__(self, src=None, relation=None, dest=None, weighted=False):
        """Query the graph for matching triples.

        Src, relation, and/or dest values can be provided, and
        triples that match the given values will be returned.  Passing
        no values will iterate all triples.

        """
        weight = True
        if src is not None:  # src,?,?
            sid = self[src]
            if relation is not None:  # src,relation,?
                rid = self._get_relation_id(relation)
                rel = self._relations[rid]

                if dest is not None:  # src,relation,dest
                    did = self[dest]
                    eids = rel.A[sid]
                    for eid, _ in eids:
                        if weighted:
                            weight = rel.B[eid, did]
                        yield Edge(
                            self,
                            rid,
                            sid,
                            did,
                            weight,
                            eid,
                        )

                else:  # src,relation,None
                    for did, eid in rel.AB[sid]:
                        dest = self._get_node_name(did)
                        if weighted:
                            weight = rel.B[eid, did]
                        yield Edge(
                            self,
                            rid,
                            sid,
                            did,
                            weight,
                            eid,
                        )
            else:
                if dest is not None:  # src,None,dest
                    did = self[dest]
                    for relation, rel in self._relations.items():
                        try:
                            eid = rel.AB[sid, did]
                            if weighted:
                                weight = rel.B[eid, did]
                            yield Edge(
                                self,
                                rid,
                                sid,
                                did,
                                weight,
                                eid,
                            )
                        except NoValue:
                            continue

                else:  # src,None,None
                    for rid, rel in self._relations.items():
                        try:
                            for did, eid in rel.AB[sid]:
                                if weighted:
                                    weight = rel.B[eid, did]
                                dest = self._get_node_name(did)
                                yield Edge(
                                    self,
                                    rid,
                                    sid,
                                    did,
                                    weight,
                                    eid,
                                )
                        except NoValue:
                            continue

        elif relation is not None:  # None,relation,?
            rid = self._get_relation_id(relation)
            rel = self._relations[rid]
            if dest is not None:  # None,relation,dest
                did = self[dest]
                for sid, eid in rel.AB[:, did]:
                    src = self._get_node_name(sid)
                    yield Edge(
                        self,
                        rid,
                        sid,
                        did,
                        weight,
                        eid,
                    )
            else:  # None,relation,None
                for sid, did, eid in rel.AB:
                    if weighted:
                        weight = rel.B[eid, did]
                    src = self._get_node_name(sid)
                    dest = self._get_node_name(did)
                    yield Edge(
                        self,
                        rid,
                        sid,
                        did,
                        weight,
                        eid,
                    )

        elif dest is not None:  # None,None,dest
            did = self[dest]
            for rid, rel in self._relations.items():
                try:
                    for sid, eid in rel.AB[:, did]:
                        src = self._get_node_name(sid)
                        if weighted:
                            weight = rel.B[eid, did]
                        yield Edge(
                            self,
                            rid,
                            sid,
                            did,
                            weight,
                            eid,
                        )
                except NoValue:
                    continue

        else:  # None,None,None
            for rid, rel in self._relations.items():
                for sid, did, eid in rel.AB:
                    if weighted:
                        weight = rel.B[eid, did]
                    src = self._get_node_name(sid)
                    dest = self._get_node_name(did)
                    yield Edge(
                        self,
                        rid,
                        sid,
                        did,
                        weight,
                        eid,
                    )


class Edge(NamedTuple):
    """A hyperedge between graph nodes."""

    graph: Graph
    rid: int
    sid: int
    did: int
    weight: object = True
    eid: int = None

    def __repr__(self):
        return f"{self.relation}({self.src} -> {self.dest}: {self.weight})"

    @property
    def relation(self):
        return self.graph._get_relation_name(self.rid)

    @property
    def src(self):
        return self.graph._get_node_name(self.sid)

    @property
    def dest(self):
        return self.graph._get_node_name(self.did)


class Relation:
    def __init__(
        self,
        graph,
        rid,
        name,
        weight_type,
        transposed=False,
        semiring=INT64.any_secondi,
    ):
        self.graph = graph
        self.rid = rid
        self.name = name
        self.transposed = transposed
        self.semiring = semiring
        self.A = Matrix.sparse(BOOL)
        self.B = Matrix.sparse(weight_type)

    def add(self, sid, eid, did, weight):
        self.A[sid, eid] = True
        self.B[eid, did] = weight

    @property
    def AB(self):
        return self.semiring(self.A, self.B)

    def __iter__(self):
        for i, j, e in self.AB:
            yield Edge(self.graph, self.rid, i, j, True, e)

    def __repr__(self):
        return f"<{self.B.type.__name__} {self.name}: {self.B.nvals}>"


def read_csv(self, fname, **kw):
    import csv

    with open(fname) as fd:
        rd = csv.reader(fd, **kw)
        for row in rd:
            if row:
                self += tuple(row)
