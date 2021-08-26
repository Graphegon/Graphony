from pygraphblas import Matrix, BOOL, INT64

from .edge import Edge


class Relation:
    """
    Relation object.
    """

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
        if weight_type is None:
            weight_type = BOOL
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

            self.A[source.n_id, eid] = A_weight
            self.B[eid, destination.n_id] = weight
        else:
            self.A[source.n_id, destination.n_id] = weight

    def __call__(self, *args, semiring=None, **kwargs):
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
            r_type = "Incidence"
        else:
            A = self.A
            r_type = "Adjacency"
        return f"<{r_type} {self.name} {A.type.__name__}:{A.nvals}>"

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
