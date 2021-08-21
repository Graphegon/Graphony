# Graphony Hypergraphs

Graphony is a Python library for doing high-performance graph analysis
using the GraphBLAS over sparse and hypersparse data sets.

Graphony stores graph edges in [GraphBLAS
Matrices](https://graphegon.github.io/pygraphblas/pygraphblas/index.html#pygraphblas.Matrix)
and node and edge properties in [PostgreSQL](https://postgresql.org).

Graphony's primary role is to manage symbolic names and properties for
nodes, relations and edges, and can be used to easily construct, save
and manage graphs in a simple project directory format.

Graphony consists of four concepts:

  - Graph: Top level object that contains all graph data in
    sub-hypergraphs called *relations*.

    Graphs can be any combination of:

    - [Simple](https://en.wikipedia.org/wiki/Graph_(discrete_mathematics)#Graph):
      an edge connects one source to one destination.

    - [Hypergraph](https://en.wikipedia.org/wiki/Hypergraph): an edges
      can connect multiple sources to multiple destinations.

    - [Multigraph](https://en.wikipedia.org/wiki/Multigraph): multiple
      edges can exist between a source and destination.

    - [Property
      Graph](http://graphdatamodeling.com/Graph%20Data%20Modeling/GraphDataModeling/page/PropertyGraphs.html):
      Nodes and and Edges can have arbitrary JSON properties.

  - Relation: A named, typed sub-graph that hold hyperedges.  A
    relation consists of two GraphBLAS [Incidence
    Matrices](https://en.wikipedia.org/wiki/Incidence_matrix) that can
    be multiplied to project an adjacency with themselves, or any
    other combination of relations.

  - Edge: Graphony hyperedges can represent relations between multiple
    incoming and outgoing nodes.
