from .graph import Graph, Relation, Edge, Node


def doctest(raise_on_error=False):
    import sys
    import doctest as dt
    from . import graph

    this = sys.modules[__name__]
    for mod in (graph,):
        dt.testmod(mod, optionflags=dt.ELLIPSIS, raise_on_error=raise_on_error)
