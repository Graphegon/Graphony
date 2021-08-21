from typing import NamedTuple
from collections import OrderedDict
from operator import attrgetter
from functools import lru_cache
import psycopg2 as pg

from .util import lazy, curse, query

from pygraphblas import Matrix, Vector, BOOL, INT64
from pygraphblas.base import NoValue


class Edge(NamedTuple):
    """An edge between two graph nodes."""

    relation: object
    subject: object
    object: object
    weight: object = True
    id: int = None

    def __repr__(self):
        return f"<{self.relation}({self.subject} -> {self.object}: {self.weight})>"


class Relation:

    LRU_MAXSIZE = None

    def __init__(self, graph, name, weight_type):
        self._graph = graph
        self._name = name
        self._B = Matrix.sparse(weight_type)
        self._BT = Matrix.sparse(weight_type)

    def __repr__(self):
        return f"<{self._B.type.__name__} {self._name}: {self._B.nvals}>"

    def __iter__(self):
        gn = self._graph._get_node_name
        adj = INT64.any_secondi(self._graph._A, self._B)
        for i, j, e in adj:
            yield Edge(self._name, gn(i), gn(j), True, e)

    def __getitem__(self, key):
        id = self._get_relation_id(key)
        if id is None:
            raise KeyError(key)
        return id


class Graph:
    """A GraphBLAS-backed multiple property graph.

    A graph consists of a set of nodes connected by edges.  Each
    matrix stores a property relation between graph edges.

    Each unique relation is stored as an adjacency matrix from
    subjects to objects.  To demonstrate, first create a helper
    function `p()` that will iterate results into a list and "pretty
    print" them.

    >>> import pprint
    >>> p = lambda r: pprint.pprint(sorted(list(r)))

    Now construct a graph that is connected to a database.  Shown here
    is an in-memory sqlite database for demostration purposes:

    >>> G = Graph('postgres://postgres:postgres@localhost:5433/graphony')

    Relation tuples can be added directly into the Graph with the `+=`
    method.

    >>> G += ('bob', 'friend', 'alice')
    >>> G += ('alice', 'friend', 'jane')

    Or an iterator of relation tuples can be provided:

    >>> G += [('bob', 'coworker', 'jane'), ('tim', 'friend', 'bob')]

    Inspecting G shows that it has two columns and four edges:

    >>> G
    <Graph [friend, coworker]: 4>

    The graph can then be called like `G(...)` to query it.  A query
    consists of three optional arguments for `subject`, `relation`
    and `object`.  The default value for all three is None, which acts
    as a wildcard to matches all values.

    >>> p(G())
    [<coworker(bob -> jane: True)>,
     <friend(alice -> jane: True)>,
     <friend(bob -> alice: True)>,
     <friend(tim -> bob: True)>]

    Only print relations where `bob` is the subject:

    >>> p(G(subject='bob'))
    [<coworker(bob -> jane: True)>, <friend(bob -> alice: True)>]

    Only print relations where `coworker` is the relation:

    >>> p(G(relation='coworker'))
    [<coworker(bob -> jane: True)>]

    Only print relations where `jane` is the object:

    >>> p(G(object='jane'))
    [<coworker(bob -> jane: True)>, <friend(alice -> jane: True)>]

    Relations are accessible as attributes of the graph:

    >>> G.friend
    <BOOL friend: 3>
    >>> G.coworker
    <BOOL coworker: 1>

    Relations can be iterated directly:

    >>> p(list(G.friend))
    [<friend(alice -> jane: True)>,
     <friend(bob -> alice: True)>,
     <friend(tim -> bob: True)>]

    >>> G += [('bob', 'distance', 'alice', 42),
    ...       ('alice', 'distance', 'jane', 420)]

    >>> p(list(G))
    [<coworker(bob -> jane: True)>,
     <distance(alice -> jane: 420)>,
     <distance(bob -> alice: 42)>,
     <friend(alice -> jane: True)>,
     <friend(bob -> alice: True)>,
     <friend(tim -> bob: True)>]
    """

    LRU_MAXSIZE = None

    def __init__(self, dsn, max_cache_size=None):
        self._dsn = dsn
        self._graph = self
        self._conn = pg.connect(self._dsn)
        self._A = Matrix.sparse(BOOL)
        self._AT = Matrix.sparse(BOOL)
        self._relations = {}

    @lru_cache(maxsize=LRU_MAXSIZE)
    @curse
    @query
    def _upsert_node(self, curs):
        """
        INSERT INTO graphony.node (n_name)
        VALUES (%s)
        ON CONFLICT (n_name) DO UPDATE SET n_name = EXCLUDED.n_name
        RETURNING n_id
        """

    @lru_cache(maxsize=LRU_MAXSIZE)
    @curse
    @query
    def _get_node_id(self, curs):
        """
        SELECT n_id FROM graphony.node where n_name = %s
        """

    @lru_cache(maxsize=LRU_MAXSIZE)
    @curse
    @query
    def _get_node_name(self, curs):
        """
        SELECT n_name FROM graphony.node where n_id = %s
        """

    @curse
    @query
    def _new_edge(self, curs):
        """
        INSERT INTO graphony.edge (e_props) VALUES (null) RETURNING e_id
        """

    def __getitem__(self, key):
        id = self._get_node_id(key)
        if id is None:
            raise KeyError(key)
        return id

    def _add(self, relation, subject, object, weight=True, eid=None):
        """Add a triple to the graph with an optional weight."""
        if not relation.isidentifier() or relation.startswith("_"):
            assert NameError(
                "relation name must start with a letter, "
                "and can only contain letters, numbers, and underscores"
            )
        sid = self._upsert_node(subject)
        oid = self._upsert_node(object)
        if relation not in self._relations:
            self._relations[relation] = Relation(self, relation, type(weight))

        if eid is None:
            eid = self._new_edge()

        self._A[sid, eid] = True
        self._AT[eid, sid] = True
        self._relations[relation]._B[eid, oid] = weight
        self._relations[relation]._BT[oid, eid] = weight

    def __getattr__(self, name):
        if name not in self._relations:
            return AttributeError(name)
        return self._relations[name]

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
        return sum(map(attrgetter("_B.nvals"), self._relations.values()))

    def __repr__(self):
        return f"<Graph [{', '.join(self._relations.keys())}]: {len(self)}>"

    def __iter__(self):
        return self(weighted=True)

    def __call__(self, subject=None, relation=None, object=None, weighted=False):
        """Query the graph for matching triples.

        Subject, relation, and/or object values can be provided, and
        triples that match the given values will be returned.  Passing
        no values will iterate all triples.

        """
        weight = True
        if subject is not None:  # subject,?,?
            sid = self[subject]
            if relation is not None:  # subject,relation,?
                rel = self._relations[relation]

                if object is not None:  # subject,relation,object
                    oid = self[object]
                    eids = rel._BT[oid]
                    for eid, _ in eids:
                        if weighted:
                            weight = rel._B[eid, oid]
                        yield Edge(
                            rel._name,
                            subject,
                            object,
                            weight,
                            eid,
                        )

                else:  # subject,relation,None
                    adj = rel._B.type.any_secondi(self._A, rel._B)
                    for oid, eid in adj[sid]:
                        object = self._get_node_name(oid)
                        if weighted:
                            weight = rel._B[eid, oid]
                        yield Edge(
                            rel._name,
                            subject,
                            object,
                            weight,
                            eid,
                        )
            else:
                if object is not None:  # subject,None,object
                    oid = self[object]
                    for relation, rel in self._relations.items():
                        try:
                            adj = INT64.any_secondi(self._A, rel._B)
                            eid = adj[sid, oid]
                            if weighted:
                                weight = rel._B[eid, oid]
                            yield Edge(
                                rel._name,
                                subject,
                                object,
                                weight,
                                eid,
                            )
                        except NoValue:
                            continue

                else:  # subject,None,None
                    for relation, rel in self._relations.items():
                        try:
                            adj = INT64.any_secondi(self._A, rel._B)
                            for oid, eid in adj[sid]:
                                if weighted:
                                    weight = rel._B[eid, oid]
                                object = self._get_node_name(oid)
                                yield Edge(
                                    rel._name,
                                    subject,
                                    object,
                                    weight,
                                    eid,
                                )
                        except NoValue:
                            continue

        elif relation is not None:  # None,relation,?
            rel = self._relations[relation]
            adj = INT64.any_secondi(self._A, rel._B)
            if object is not None:  # None,relation,object
                oid = self[object]
                for sid, eid in adj[:, oid]:
                    subject = self._get_node_name(sid)
                    yield Edge(
                        rel._name,
                        subject,
                        object,
                        weight,
                        eid,
                    )
            else:  # None,relation,None
                for sid, oid, eid in adj:
                    if weighted:
                        weight = rel._B[eid, oid]
                    subject = self._get_node_name(sid)
                    object = self._get_node_name(oid)
                    yield Edge(
                        rel._name,
                        subject,
                        object,
                        weight,
                        eid,
                    )

        elif object is not None:  # None,None,object
            oid = self[object]
            for relation, rel in self._relations.items():
                try:
                    adj = INT64.any_secondi(self._A, rel._B)
                    for sid, eid in adj[:, oid]:
                        subject = self._get_node_name(sid)
                        if weighted:
                            weight = rel._B[eid, oid]
                        yield Edge(
                            rel._name,
                            subject,
                            object,
                            weight,
                            eid,
                        )
                except NoValue:
                    continue

        else:  # None,None,None
            for relation, rel in self._relations.items():
                adj = INT64.any_secondi(self._A, rel._B)
                for sid, oid, eid in adj:
                    if weighted:
                        weight = rel._B[eid, oid]
                    subject = self._get_node_name(sid)
                    object = self._get_node_name(oid)
                    yield Edge(
                        rel._name,
                        subject,
                        object,
                        weight,
                        eid,
                    )


def read_csv(self, fname, **kw):
    """Read a csv file of triples into the graph.

    File rows must contain 3 or 4 values, a subj/pred/obj triple
    and an optional weight.

    """
    import csv

    with open(fname) as fd:
        rd = csv.reader(fd, **kw)
        for row in rd:
            if row:
                if 3 <= len(row) <= 4:
                    self.add(*row)
                else:
                    raise TypeError("Row must be 3 or 4 columns")
