from typing import NamedTuple
from operator import attrgetter
from functools import lru_cache
import psycopg2 as pg
from pickle import dumps, loads

from .util import lazy, query

from pygraphblas import Matrix, Vector, BOOL, INT64
from pygraphblas.base import NoValue


class Graph:
    """# A GraphBLAS-backed Hyper/Property graph.

    A graph is set of nodes connected by edges.  Edges can be simple
    1-1 connections, or many-to-many *hyperedges*.  Edges are named
    and typed into distinct collections called *relations*.  Each
    relation holds edges and their weights, which can be any of the
    standard GraphBLAS types, or a User Defined Type.

    Interally The GraphBLAS works numerically, nodes are idenified by
    a 60-bit integer key, so one of Graphony's key tasks is keeping
    track of node ids and the names they map to.  These mappings are
    stored in PostgreSQL.

    ## Creating Graphs

    To demonstrate, first let's create a helper function `p()` that
    will iterate results into a list and "pretty print" them.  This
    isn't necessary to use Graphony, but is only to help format and
    verify the output of this documentation:

    >>> import pprint
    >>> p = lambda r: pprint.pprint(sorted(list(r)))

    Now construct a graph that is connected to a database.

    >>> G = Graph('postgres://postgres:postgres@localhost:5433/graphony')

    Relation tuples can be added directly into the Graph with the `+=`
    method.  In their simplest form, a relation is a Python tuple with
    3 elements, a relation name, a source name, and a destination
    name:

    ## Accumulating Edges

    >>> G += ('friend', 'bob', 'alice')

    Strings like `'bob'` and `'alice'` as edge endpoints create new
    graph nodes automatically.  You can also create a node explicity
    and provide properties for that node as well.

    >>> jane = Node(G, 'jane', favorite_color='blue')
    >>> G += ('friend', 'alice', jane)

    This adds two edges to the `friend` relation, one from bob to
    alice and the other from alice to jane.

    >>> p(G)
    [(friend, bob, alice, True), (friend, alice, jane, True)]

    An iterator of relation tuples can also be provided:

    >>> G += [('coworker', 'bob', 'jane'), ('coworker', 'alice', 'jane')]

    As shown above, tuples with 3 elements (triples), are stored as
    boolean edges whose weights are always `True` and therefore can be
    ommited.  To create edges of a certain type, 4 elements can be
    provided:

    >>> G += [('distance', 'chicago', 'seatle', 422),
    ...       ('distance', 'seattle', 'portland', 42)]

    ## Graph Querying

    Inspecting G shows that it has three columns and six edges:

    >>> G
    <Graph [friend, coworker, distance]: 6>

    The graph can then be called like `G(...)` to examine it.  A query
    consists of three optional arguments for `relation`, 'source' and
    `destination`.  The default value for all three is None, which
    acts as a wildcard to matches all values.

    >>> p(G())
    [(friend, bob, alice, True),
     (friend, alice, jane, True),
     (coworker, bob, jane, True),
     (coworker, alice, jane, True),
     (distance, chicago, seatle, 422),
     (distance, seattle, portland, 42)]

    Only print relations where `bob` is the src:

    >>> p(G(source='bob'))
    [(friend, bob, alice, True), (coworker, bob, jane, True)]

    Only print relations where `coworker` is the relation:

    >>> p(G(relation='coworker'))
    [(coworker, bob, jane, True), (coworker, alice, jane, True)]

    Only print relations where `jane` is the dest:

    >>> p(G(destination='jane'))
    [(friend, alice, jane, True),
     (coworker, bob, jane, True),
     (coworker, alice, jane, True)]

    >>> p(G(source='bob', relation='coworker', destination='jane'))
    [(coworker, bob, jane, True)]

    The entire graph can also be iterated directly.  This is the same
    as `G()` with no arguments:

    >>> p(G)
    [(friend, bob, alice, True),
     (friend, alice, jane, True),
     (coworker, bob, jane, True),
     (coworker, alice, jane, True),
     (distance, chicago, seatle, 422),
     (distance, seattle, portland, 42)]

    Edges can be tested to see if they are contained in the Graph:

    Relations are accessible as attributes of the graph:

    >>> G.friend
    <BOOL friend: 2>
    >>> G.coworker
    <BOOL coworker: 2>

    Relations can be iterated directly:

    >>> p(list(G.friend))
    [(friend, bob, alice, True), (friend, alice, jane, True)]

    Each relation is a pair of incidence matrices, `A` and `B`.  `A`
    is a graph from source ids to edge ids, `B` is a graph from edge
    ids to destination ids.  Due to this incidence pair, a relation
    can store multiple edges between the same source and destination,
    forming a multigraph, and multiple sources and destinations can be
    joined by the same edge, forming a hypergraph.

    ## Graph Algorithms

    When it's necessary to run graph algorithms, a relation can be
    *projected* into an adjacency matrix using any GraphBLAS semiring
    by calling the relation with a semring using the syntax
    `rel(semiring)`.

    XXX

    ## Deleting Edges

    Edges in a graph can be deleted using the `del` keyword:

    >>> del G[None, None, None]
    >>> p(G)
    []

    ## Query Graphs from SQL

    Any tuple producing iterator can be used to construct Graphs.
    Graphony offers a shorthand helper for this.  Any query that
    produces 3 or 4 columns can be used to produce edges into the
    graph.

    >>> G += G.sql(
    ...  "select 'karate', 'karate_' || s_id, 'karate_' || d_id "
    ...  "from graphony.karate")

    >>> len(G)
    78

    All the edges are in the karate relation, as defined in the sql
    query above:

    >>> len(G.karate)
    78

    """

    _LRU_MAXSIZE = None

    def __init__(self, dsn, relations=None, max_cache_size=None):
        self.graph = self
        self._conn = pg.connect(dsn)
        if relations is None:
            relations = {}
            with self._conn.cursor() as c:
                c.execute("select r_id, r_name, r_type from graphony.relation")
                for r in c.fetchall():
                    relations[r[0]] = Relation(self, r[0], r[1], loads(r[2]))
        self._relations = relations

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
        INSERT INTO graphony.relation (r_name, r_type)
        VALUES (%s, %s)
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

    def _add(self, relation, source, destination, weight=True, eid=None):
        """Add an edge to the graph with an optional weight."""
        if not relation.isidentifier() or relation.startswith("_"):
            assert NameError(
                "relation name must start with a letter, "
                "and can only contain letters, numbers, and underscores"
            )

        if isinstance(source, Node):
            sid = source.id
        else:
            sid = self._upsert_node(source)

        if isinstance(destination, Node):
            did = destination.id
        else:
            did = self._upsert_node(destination)

        if eid is None:
            eid = self._new_edge()

        rid = self._upsert_relation(relation, dumps(type(weight)))
        if rid not in self._relations:
            rel = Relation(self, rid, relation, type(weight))
            self._relations[rid] = rel
        else:
            rel = self._relations[rid]

        rel.add(sid, eid, did, weight)

    def __getitem__(self, key):
        if isinstance(key, int):
            id = self._get_node_name(key)
        else:
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
        return sum(map(len, self._relations.values()))

    def __repr__(self):
        return f"<Graph [{', '.join([r.name for r in self._relations.values()])}]: {len(self)}>"

    def __iter__(self):
        return self(weighted=True)

    def __delitem__(self, key):
        source, relation, destination = key
        if source is not None:  # src, ?, ?
            sid = self[source]
            if relation is not None:  # src, relation, ?
                rel = self._relations[relation]
                if destination is not None:  # src, relation, dest
                    did = self[destination]
                    for _, eid in rel.A[sid]:
                        del rel.A[sid, eid]
                        del rel.B[eid, did]
                        return

                else:  # src, relation, None
                    for _, eid in rel.A[sid]:
                        rel.B[eid] = Vector.sparse(BOOL, rel.B.nrows)
                    rel.A[sid] = Vector.sparse(BOOL, rel.A.nrows)

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
            for _, rel in self._relations.items():
                rel.A.clear()
                rel.B.clear()

    def __getattr__(self, name):
        rid = self._get_relation_id(name)
        if rid is None:
            raise AttributeError(name)
        return self._relations[rid]

    def sql(self, query):
        with self._conn.cursor() as c:
            c.execute(query)
            return c.fetchall()

    def __call__(self, relation=None, source=None, destination=None, weighted=True):
        """Query the graph for matching triples.

        Source, relation, and/or destination values can be provided, and
        triples that match the given values will be returned.  Passing
        no values will iterate all triples.

        """
        weight = True
        if source is not None:  # source,?,?
            sid = self[source]
            if relation is not None:  # source,relation,?
                rid = self._get_relation_id(relation)
                rel = self._relations[rid]

                if destination is not None:  # source,relation,destination
                    did = self[destination]
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

                else:  # source,relation,None
                    for did, eid in rel(INT64.any_secondi)[sid]:
                        destination = self._get_node_name(did)
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
                if destination is not None:  # source,None,destination
                    did = self[destination]
                    for relation, rel in self._relations.items():
                        try:
                            eid = rel(INT64.any_secondi)[sid, did]
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

                else:  # source,None,None
                    for rid, rel in self._relations.items():
                        try:
                            for did, eid in rel(INT64.any_secondi)[sid]:
                                if weighted:
                                    weight = rel.B[eid, did]
                                destination = self._get_node_name(did)
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
            if destination is not None:  # None,relation,destination
                did = self[destination]
                for sid, eid in rel(INT64.any_secondi)[:, did]:
                    source = self._get_node_name(sid)
                    yield Edge(
                        self,
                        rid,
                        sid,
                        did,
                        weight,
                        eid,
                    )
            else:  # None,relation,None
                for sid, did, eid in rel(INT64.any_secondi):
                    if weighted:
                        weight = rel.B[eid, did]
                    source = self._get_node_name(sid)
                    destination = self._get_node_name(did)
                    yield Edge(
                        self,
                        rid,
                        sid,
                        did,
                        weight,
                        eid,
                    )

        elif destination is not None:  # None,None,destination
            did = self[destination]
            for rid, rel in self._relations.items():
                try:
                    for sid, eid in rel(INT64.any_secondi)[:, did]:
                        source = self._get_node_name(sid)
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
                for sid, did, eid in rel(INT64.any_secondi):
                    if weighted:
                        weight = rel.B[eid, did]
                    source = self._get_node_name(sid)
                    destination = self._get_node_name(did)
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
        return (
            f"({self.relation.name}, {self.source}, {self.destination}, {self.weight})"
        )

    @property
    def relation(self):
        return self.graph._relations[self.rid]

    @property
    def source(self):
        return Node(self.graph, self.sid)

    @property
    def destination(self):
        return Node(self.graph, self.did)


class Node:

    __slots__ = ("relation", "id", "props")

    def __init__(self, relation, id, **props):
        if isinstance(id, str):
            id = relation.graph._upsert_node(id)
        self.relation = relation
        self.id = id
        self.props = props

    @property
    def name(self):
        return self.relation.graph._get_node_name(self.id)

    def __repr__(self):
        return self.name


class Relation:
    def __init__(
        self,
        graph,
        rid,
        name,
        weight_type,
    ):
        self.graph = graph
        self.rid = rid
        self.name = name
        self.A = Matrix.sparse(BOOL)
        self.B = Matrix.sparse(weight_type)

    def add(self, sid, eid, did, weight):
        self.A[sid, eid] = True
        self.B[eid, did] = weight

    def __call__(self, semiring=None, *args, **kwargs):
        if semiring is None:
            semiring = INT64.any_secondi
        return semiring(self.A, self.B, *args, **kwargs)

    def __iter__(self):
        for sid, did, eid in self(INT64.any_secondi):
            w = self.B[eid]
            for _, weight in w:
                yield Edge(self.graph, self.rid, sid, did, weight, eid)

    def __len__(self):
        return self.B.nvals

    def __repr__(self):
        return f"<{self.B.type.__name__} {self.name}: {self.B.nvals}>"


def read_csv(self, fname, **kw):
    import csv

    with open(fname) as fd:
        rd = csv.reader(fd, **kw)
        for row in rd:
            if row:
                self += tuple(row)
