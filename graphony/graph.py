from typing import NamedTuple
from operator import attrgetter
from functools import lru_cache
import psycopg2 as pg
from pickle import dumps, loads

from .util import lazy, query

from pygraphblas import Matrix, Vector, BOOL, INT64
from pygraphblas.base import NoValue


class Graph:
    """# Hypersparse Multi-property Hypergraphs

    A graph is set of nodes connected by edges.  Edges are typed and
    group into named collections called *relations*.  Each relation
    holds edges one of two forms, an [adjancency
    matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) which can
    hold a simple graph with directed or undirected 1-to-1 edges, or
    two [incidence
    matrices](https://en.wikipedia.org/wiki/Incidence_matrix), which
    can hold multigraphs and hypergraphs where node and edge
    relationships can be many-to-many.  In either case the edge
    weights can be any of the standard GraphBLAS types, or a User
    Defined Type.

    Interally The GraphBLAS works numerically, nodes are idenified by
    a 60-bit integer key, so one of Graphony's key tasks is keeping
    track of node ids and the names they map to.  These mappings are
    stored in PostgreSQL.  It's important to note that the graph
    structure itself is not stored in PostgreSQL instead the structure
    is stored in GraphBLAS matrices. Only the node id and name
    mappings and node and edge properties are stored in the database.

    ## Creating Graphs

    To demonstrate, first let's create a helper function `p()` that
    will iterate results into a list and "pretty print" them.  This
    isn't necessary to use Graphony, but is only to help format and
    verify the output of this documentation:

    >>> import pprint
    >>> p = lambda r: pprint.pprint(sorted(list(r)))

    Now construct a graph that is connected to a database.

    >>> db = 'postgres://postgres:postgres@localhost:5433/graphony'
    >>> G = Graph(db)

    ## Accumulating Edges

    Relation tuples can be added directly into the Graph with the `+=`
    method.  In their simplest form, a relation is a Python tuple with
    3 elements, a relation name, a source name, and a destination
    name:

    Before you can add an edge to a relation, it must be declared
    first.

    >>> G.relation('friend')

    Now edges in that relation can be added to the graph:

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

    >>> G.relation('coworker', incidence=True)
    >>> G += [('coworker', 'bob', 'jane'), ('coworker', 'alice', 'jane')]

    As shown above, tuples with 3 elements (triples), are stored as
    boolean edges whose weights are always `True` and therefore can be
    ommited.

    To create edges of a certain type, 4 elements can be provided:

    >>> G.relation('distance', int)
    >>> G += [('distance', 'chicago', 'seattle', 422),
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
     (distance, chicago, seattle, 422),
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
     (distance, chicago, seattle, 422),
     (distance, seattle, portland, 42)]

    Edges can be tested to see if they are contained in the Graph:

    Relations are accessible as attributes of the graph:

    >>> G.friend
    <Adjacency friend BOOL:2>

    >>> G.coworker
    <Incidence coworker BOOL:2>

    Relations can be iterated directly:

    >>> p(list(G.friend))
    [(friend, bob, alice, True), (friend, alice, jane, True)]

    ## Graph Algorithms

    Graphony uses The GraphBLAS API to store graphs and runs graph
    algorithms by doing parallel sparse matrix multiplication using
    the SuiteSparse:GraphBLAS library.

    Matrix multiplication is a very power, but rather abstract
    approach to writing graph algorithms, and it can be tricky to
    writem common algorithms optimially form scratch, so Graphony
    contains some common graph algorithms which can also act as
    starting points for custom algorithms:

    >>>

    ## Query Graphs from SQL

    Any tuple producing iterator can be used to construct Graphs.
    Graphony offers a shorthand helper for this.  Any query that
    produces 3 or 4 columns can be used to produce edges into the
    graph.

    >>> G.relation('karate')
    >>> G += G.sql(
    ...  "select 'karate', 'karate_' || s_id, 'karate_' || d_id "
    ...  "from graphony.karate")

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
                c.execute("select id, r_name, r_type from graphony.relation")
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
        RETURNING id
        """

    @lru_cache(maxsize=_LRU_MAXSIZE)
    @query
    def _get_node_id(self, curs):
        """
        SELECT id FROM graphony.node where n_name = %s
        """

    @lru_cache(maxsize=_LRU_MAXSIZE)
    @query
    def _get_node_name(self, curs):
        """
        SELECT n_name FROM graphony.node where id = %s
        """

    @lru_cache(maxsize=_LRU_MAXSIZE)
    @query
    def _upsert_relation(self, curs):
        """
        INSERT INTO graphony.relation (r_name, r_type)
        VALUES (%s, %s)
        ON CONFLICT (r_name) DO UPDATE SET r_name = EXCLUDED.r_name
        RETURNING id
        """

    @lru_cache(maxsize=_LRU_MAXSIZE)
    @query
    def _get_relation_id(self, curs):
        """
        SELECT id FROM graphony.relation where r_name = %s
        """

    @lru_cache(maxsize=_LRU_MAXSIZE)
    @query
    def _get_relation_name(self, curs):
        """
        SELECT r_name FROM graphony.relation where id = %s
        """

    @query
    def _new_edge(self, curs):
        """
        INSERT INTO graphony.edge (e_props) VALUES (null) RETURNING id
        """

    def sql(self, query):
        with self._conn.cursor() as c:
            c.execute(query)
            return c.fetchall()

    def add(self, relation, source, destination, weight=True, eid=None):
        """Add an edge to the graph with an optional weight."""
        if not relation.isidentifier() or relation.startswith("_"):
            assert NameError(
                "relation name must start with a letter, "
                "and can only contain letters, numbers, and underscores"
            )

        rel = getattr(self, relation)

        if isinstance(source, str):
            source = Node(self, source)

        if isinstance(destination, str):
            destination = Node(self, destination)

        rel.add(source, destination, weight)

    def relation(self, name, type=BOOL, incidence=False):
        rid = self._upsert_relation(name, dumps(type))
        rel = Relation(self, rid, name, type, incidence)
        self._relations[rid] = rel

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
            self.add(*relation)
        elif isinstance(relation, Graph):
            raise TypeError("todo")
        else:
            for i in relation:
                self.add(*i)
        return self

    def __len__(self):
        """Returns the number of triples in the graph."""
        return sum(map(len, self._relations.values()))

    def __repr__(self):
        return f"<Graph [{', '.join([r.name for r in self._relations.values()])}]: {len(self)}>"

    def __iter__(self):
        return self()

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

    def __call__(self, relation=None, source=None, destination=None):
        """Query the graph for matching triples.

        Source, relation, and/or destination values can be provided, and
        triples that match the given values will be returned.  Passing
        no values will iterate all edges.

        """
        weight = True
        if source is not None:  # source,?,?
            sid = self[source]
            if relation is not None:  # source,relation,?
                rid = self._get_relation_id(relation)
                rel = self._relations[rid]

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
                    for relation, rel in self._relations.items():
                        for edge in rel[sid, did]:
                            yield edge

                else:  # source,None,None
                    for rid, rel in self._relations.items():
                        for edge in rel[sid, :]:
                            yield edge

        elif relation is not None:  # None,relation,?
            rid = self._get_relation_id(relation)
            rel = self._relations[rid]
            if destination is not None:  # None,relation,destination
                did = self[destination]
                for edge in rel[:, did]:
                    yield edge

            else:  # None,relation,None
                for edge in rel:
                    yield edge

        elif destination is not None:  # None,None,destination
            did = self[destination]
            for rid, rel in self._relations.items():
                for edge in rel[:, did]:
                    yield edge

        else:  # None,None,None
            for rid, rel in self._relations.items():
                for edge in rel:
                    yield edge


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

    __slots__ = ("graph", "id", "props")

    def __init__(self, graph, id, **props):
        if isinstance(id, str):
            id = graph._upsert_node(id)

        self.graph = graph
        self.id = id
        self.props = props

    @property
    def name(self):
        return self.graph._get_node_name(self.id)

    def __repr__(self):
        return self.name


class Relation:
    def __init__(
        self,
        graph,
        rid,
        name,
        weight_type,
        incidence=False,
        incident_A_type=BOOL,
    ):
        self.graph = graph
        self.rid = rid
        self.name = name
        self.incidence = incidence
        if incidence:
            self.A = Matrix.sparse(incident_A_type)
            self.B = Matrix.sparse(weight_type)
        else:
            self.A = Matrix.sparse(weight_type)
            self.B = None

    def add(self, source, destination, weight, eid=None, A_weight=True):
        if self.incidence:
            if eid is None:
                eid = self.graph._new_edge()

            self.A[source.id, eid] = A_weight
            self.B[eid, destination.id] = weight
        else:
            self.A[source.id, destination.id] = weight

    def __call__(self, semiring=None, *args, **kwargs):
        if not self.incidence:
            return self.A

        if semiring is None:
            semiring = INT64.any_secondi
        return semiring(self.A, self.B, *args, **kwargs)

    def __iter__(self):
        if self.incidence:
            for sid, did, eid in self(INT64.any_secondi):
                w = self.B[eid]
                for _, weight in w:
                    yield Edge(self.graph, self.rid, sid, did, weight, eid)
        else:
            for sid, did, weight in self.A:
                yield Edge(self.graph, self.rid, sid, did, weight)

    def __len__(self):
        return self.B.nvals if self.incidence else self.A.nvals

    def __repr__(self):
        if self.incidence:
            A = self.B
            type = "Incidence"
        else:
            A = self.A
            type = "Adjacency"
        return f"<{type} {self.name} {A.type.__name__}:{A.nvals}>"

    def __getitem__(self, key):
        sid, did = key
        if self.incidence:
            A = self.A.any_second(self.B)
        else:
            A = self.A

        if isinstance(sid, slice):
            for sid, weight in A[sid, did]:
                yield Edge(self.graph, self.rid, sid, did, weight)
        elif isinstance(did, slice):
            for did, weight in A[sid, did]:
                yield Edge(self.graph, self.rid, sid, did, weight)
        else:
            yield Edge(self.graph, self.rid, sid, did, A[sid, did])


def read_csv(self, fname, **kw):
    import csv

    with open(fname) as fd:
        rd = csv.reader(fd, **kw)
        for row in rd:
            if row:
                self += tuple(row)
