"""Property objects.
"""
from functools import total_ordering

from pygraphblas import Matrix, BOOL, INT64, lib
from pygraphblas.gviz import draw_graph

from .edge import Edge, Hedge
from .node import Node


@total_ordering
class Property:
    """
    Property object.
    """

    def __init__(
        self,
        graph,
        rid,
        name,
        weight_type,
        incidence=False,
        incident_A_type=BOOL,
        shape=(lib.GxB_INDEX_MAX, lib.GxB_INDEX_MAX),
    ):
        self.graph = graph
        self.rid = rid
        self.name = name
        self.incidence = incidence
        if weight_type is None:
            weight_type = BOOL

        nrows, ncols = self.shape = shape
        if incidence:
            self.A = Matrix.sparse(incident_A_type, nrows, ncols)
            self.B = Matrix.sparse(weight_type, ncols, nrows)
        else:
            self.A = Matrix.sparse(weight_type, nrows, ncols)
            self.B = None

    def add(self, source, destination, weight=True, eid=None, A_weight=True):
        """Add an edge to this property."""
        if not self.incidence:
            source = self.graph.get_node(source)
            destination = self.graph.get_node(destination)
            self.A[source.n_id, destination.n_id] = weight
            return

        if eid is None:
            eid = self.graph._new_edge()

        if isinstance(source, tuple):
            sources = [self.graph.get_node(s) for s in source]
        else:
            sources = [self.graph.get_node(source)]

        if isinstance(destination, tuple):
            destinations = [self.graph.get_node(d) for d in destination]
        else:
            destinations = [self.graph.get_node(destination)]

        for s in sources:
            self.A[s.n_id, eid] = A_weight
        for d in destinations:
            self.B[eid, d.n_id] = weight

    def label_vector(self, A):
        return {i: self.graph._get_node_name(i) for i in set(A.rows) | set(A.cols)}

    def draw(self, **kwargs):
        A = self()
        if "label_vector" not in kwargs:
            kwargs["label_vector"] = self.label_vector(A)
        if self.incidence:
            return draw_graph(self.A, B=self.B, **kwargs)
        else:
            return draw_graph(self.A, **kwargs)

    def __lt__(self, other):
        return self.rid < other.rid

    def __eq__(self, other):
        return self.rid == other.rid

    def __iadd__(self, property):
        if isinstance(property, tuple):
            self.add(*property)
        else:
            for i in property:
                self.add(*i)
        return self

    def __call__(self, semiring=None, cast=None, **kwargs):
        if not self.incidence:
            if cast is None:
                return self.A
            return self.A.cast(cast)

        if semiring is None:
            semiring = INT64.any_secondi
        return semiring(self.A, self.B, **kwargs)

    def __iter__(self):
        if self.incidence:
            AT = self.A.T
            for eid in set(AT.rows):
                sids = list(AT[eid].indices)
                dids = self.B[eid]
                yield Hedge(self, sids, list(dids.indices), list(dids.vals), eid)
        else:
            for sid, did, weight in self.A:
                yield Edge(self, sid, did, weight)

    def __len__(self):
        return self.B.nvals if self.incidence else self.A.nvals

    def __repr__(self):
        if self.incidence:
            A = self.B
            r_type = "Incidence"
        else:
            A = self.A
            r_type = "Adjacency"
        return f"<{r_type} {self.name} {A.type.__name__}:{A.nvals}>"

    def __getitem__(self, key):
        sid, did = key
        if self.incidence:
            AT = self.A.T
            if isinstance(did, slice):
                eids = self.A[sid]
                for eid, _ in eids:
                    _dids = self.B[eid]
                    dids = list(_dids.indices)
                    weights = list(_dids.vals)
                    sids = list(AT[eid].indices)
                    yield Hedge(self, sids, dids, weights, eid)
            elif isinstance(sid, slice):
                BT = self.B.T
                eids = BT[did]
                for eid, _ in eids:
                    sids = list(AT[eid].indices)
                    dids = self.B[eid]
                    yield Hedge(self, sids, list(dids.indices), list(dids.vals), eid)
            else:
                BT = self.B.T
                deids = BT[did]
                seids = self.A[sid]
                eids = seids.second(deids)
                for eid, _ in eids:
                    sids = list(AT[eid].indices)
                    _dids = self.B[eid]
                    dids = list(_dids.indices)
                    weights = list(_dids.vals)
                    yield Hedge(self, sids, dids, weights, eid)

        else:
            if isinstance(did, slice):
                for did, weight in self.A[sid]:
                    yield Edge(self, sid, did, weight)
            elif isinstance(sid, slice):
                for sid, weight in self.A[:, did]:
                    yield Edge(self, sid, did, weight)
            else:
                yield Edge(self, sid, did, self.a[sid, did])
