""" Graphony Hypersparse Hypergraphs """

import sys
import doctest as dt

from .graph import Graph
from .property import Property
from .node import Node
from .edge import Edge
from . import graph
from . import lib


def doctest(raise_on_error=False):
    """Run all doctests."""

    for mod in (graph,):
        dt.testmod(mod, optionflags=dt.ELLIPSIS, raise_on_error=raise_on_error)
