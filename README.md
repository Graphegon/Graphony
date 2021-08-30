# Graphony Hypergraphs

Graphony is a Python library for doing high-performance graph analysis
using the GraphBLAS over sparse and hypersparse data sets.

Graphony uses
[pygraphblas](https://graphegon.github.io/pygraphblas/pygraphblas/index.html)
to store graph data in sparse [GraphBLAS
Matrices](http://graphblas.org) and node and edge properties in
[PostgreSQL](https://postgresql.org).

Graphony's primary role is to easily construct graph matrices and
manage symbolic names and properties for graphs, nodes, relations and
edges, and can be used to easily construct, save and manage data in a
simple project directory format.

A graph is set of nodes connected by edges.  Edges are typed and
group into named collections called *relations*.  Each relation
holds edges one of two forms, an [adjancency
matrix](https://en.wikipedia.org/wiki/Adjacency_matrix) which can
hold a simple graph with directed or undirected 1-to-1 edges.

![An adjacency matrix](./docs/Incidence.png)

Or two [incidence
matrices](https://en.wikipedia.org/wiki/Incidence_matrix), which can
hold multigraphs and hypergraphs where node and edge relationships can
be many-to-many.  In either case the edge weights can be any of the
standard GraphBLAS types, or a User Defined Type.

![An incidence matrix](./docs/Incidence.png)

It's usually very helpful to be able to project a pair of incidence
matrices to an adjacency matrix using matrix multiplication.  This
"collapses" a hypergraph into a regular directed graph with simple
edges:

![Projecting An incidence matrix to adjacency](./docs/Projection.png)

Interally The GraphBLAS works row and column position indexes, which
are a 60-bit integer key, so one of Graphony's key tasks is keeping
track of node indexes and the names they map to.  These mappings are
stored in PostgreSQL.  It's important to note that the graph structure
itself is not stored in PostgreSQL instead the structure is stored in
GraphBLAS matrices. Only the node id and name mappings and node and
edge properties are stored in the database.

## Creating Graphs

To demonstrate, first let's create a helper function `p()` that will
iterate results into a list and "pretty print" them.  This isn't
necessary to use Graphony, but is only to help format and verify the
output of this documentation.  Next, create a new Graph object and
connect it to a database:

<!--phmdoctest-setup-->
```python3
import pprint
import postgresql
from graphony import Graph, Node
p = lambda r: pprint.pprint(sorted(list(r)))
pgdata, db_conn_string = postgresql.setup()
postgresql.psql(f'-d "{db_conn_string}" -f dbinit/01.sql -f dbinit/02.sql')
G = Graph(db_conn_string)
```

Graphony consists of four concepts:

  - Graph: Top level object that contains all graph data in
    sub-graphs called *relations*.

    Graphs can be any combination of:

    - [Simple](https://en.wikipedia.org/wiki/Graph_(discrete_mathematics)#Graph):
      an edge connects one source to one destination.

    - [Hypergraph](https://en.wikipedia.org/wiki/Hypergraph): a graph
      with at lest one *hyperedge* connecting multiple source nodes to
      multiple destinations.

    - [Multigraph](https://en.wikipedia.org/wiki/Multigraph): multiple
      edges can exist between a source and destination.

    - [Property
      Graph](http://graphdatamodeling.com/Graph%20Data%20Modeling/GraphDataModeling/page/PropertyGraphs.html):
      Nodes and and Edges can have arbitrary JSON properties.

  - Relation: A named, typed sub-graph that holds edges.  A
    relation consists of two GraphBLAS [Incidence
    Matrices](https://en.wikipedia.org/wiki/Incidence_matrix) that can
    be multiplied to project an adjacency with themselves, or any
    other combination of relations.

  - Edge: Relation edges can be simple point to point edges or
    hyperedges that represent relations between multiple incoming and
    outgoing nodes.
    
  - Node: A node in the graph.

## Accumulating Edges

Relation tuples can be added directly into the Graph with the `+=`
method.  In their simplest form, a relation is a Python tuple with
3 elements, a relation name, a source name, and a destination
name:

Before you can add an edge to a relation, it must be declared
first.

```python3
>>> G.relation('friend')
```

Now edges in that relation can be added to the graph:

```python3
>>> G += ('friend', 'bob', 'alice')
```

Strings like `'bob'` and `'alice'` as edge endpoints create new
graph nodes automatically.  You can also create a node explicity
and provide properties for that node as well.

```python3
>>> jane = Node(G, 'jane', favorite_color='blue')
>>> G += ('friend', 'alice', jane)
```

This adds two edges to the `friend` relation, one from bob to
alice and the other from alice to jane.

```python3
>>> p(G)
[(friend, bob, alice, True), (friend, alice, jane, True)]
```

An iterator of relation tuples can also be provided:

```python3
>>> G.relation('coworker', incidence=True)
>>> G += [('coworker', 'bob', 'jane'), ('coworker', 'alice', 'jane')]
```

As shown above, tuples with 3 elements (triples), are stored as
boolean edges whose weights are always `True` and therefore can be
ommited.

To create edges of a certain type, 4 elements can be provided:

```python3
>>> G.relation('distance', int)
>>> G += [('distance', 'chicago', 'seattle', 422),
...       ('distance', 'seattle', 'portland', 42)]
```

## Graph Querying

The graph can then be called like `G(...)` to examine it.  A query
consists of three optional arguments for `relation`, 'source' and
`destination`.  The default value for all three is None, which
acts as a wildcard to matches all values.

```python3
>>> p(G())
[(friend, bob, alice, True),
 (friend, alice, jane, True),
 (coworker, bob, jane, True),
 (coworker, alice, jane, True),
 (distance, chicago, seattle, 422),
 (distance, seattle, portland, 42)]
```

Only print relations where `bob` is the src:

```python3
>>> p(G(source='bob'))
[(friend, bob, alice, True), (coworker, bob, jane, True)]
```

Only print relations where `coworker` is the relation:

```python3
>>> p(G(relation='coworker'))
[(coworker, bob, jane, True), (coworker, alice, jane, True)]
```

Only print relations where `jane` is the dest:

```python3
>>> p(G(destination='jane'))
[(friend, alice, jane, True),
 (coworker, bob, jane, True),
 (coworker, alice, jane, True)]

>>> p(G(source='bob', relation='coworker', destination='jane'))
[(coworker, bob, jane, True)]
```

The entire graph can also be iterated directly.  This is the same
as `G()` with no arguments:

```python3
>>> p(G)
[(friend, bob, alice, True),
 (friend, alice, jane, True),
 (coworker, bob, jane, True),
 (coworker, alice, jane, True),
 (distance, chicago, seattle, 422),
 (distance, seattle, portland, 42)]
```
Edges can be tested to see if they are contained in the Graph:

Relations are accessible as attributes of the graph:

```python3
>>> G.friend
<Adjacency friend BOOL:2>

>>> G.coworker
<Incidence coworker BOOL:2>
```

Relations can be iterated directly:

```python3
>>> p(list(G.friend))
[(friend, bob, alice, True), (friend, alice, jane, True)]
```

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

```python3
>>> G.relation('karate')
>>> G += G.sql(
...  "select 'karate', 'karate_' || s_id, 'karate_' || d_id "
...  "from graphony.karate")
```

All the edges are in the karate relation, as defined in the sql
query above:

```python3
>>> len(G.karate)
78
```
Inspecting G shows that it has three columns and six edges:

```python3
>>> G
<Graph [friend, coworker, distance, karate]: 84>
```

<!--phmdoctest-teardown-->
```python3
postgresql.teardown(pgdata)
```
