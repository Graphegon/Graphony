"""pytest file built from README.md"""
import pytest

from phmdoctest.fixture import managenamespace


@pytest.fixture(scope="module")
def _phm_setup_doctest_teardown(doctest_namespace, managenamespace):
    # setup code line 47.
    import os
    import pprint
    import postgresql
    from pathlib import Path
    from pygraphblas import FP64
    from graphony import Graph, Node
    p = lambda r: pprint.pprint(sorted(list(r)))
    pgdata, conn = postgresql.setup()
    postgresql.psql(f'-d "{conn}" -f dbinit/01.sql -f dbinit/02.sql')
    G = Graph(conn)

    managenamespace(operation="update", additions=locals())
    # update doctest namespace
    additions = managenamespace(operation="copy")
    for k, v in additions.items():
        doctest_namespace[k] = v
    yield
    # teardown code line 319.
    postgresql.teardown(pgdata)

    managenamespace(operation="clear")


pytestmark = pytest.mark.usefixtures("_phm_setup_doctest_teardown")


@pytest.fixture()
def populate_doctest_namespace(doctest_namespace, managenamespace):
    additions = managenamespace(operation="copy")
    for k, v in additions.items():
        doctest_namespace[k] = v


def session_00000():
    r"""
    >>> getfixture('populate_doctest_namespace')
    """


def session_00001_line_88():
    r"""
    >>> G.add_relation('friend')
    """


def session_00002_line_94():
    r"""
    >>> G.friend += ('bob', 'alice')

    >>> G.friend.draw(weights=False, filename='docs/imgs/G_friend_1')
    <graphviz.dot.Digraph object at ...>
    """


def session_00003_line_106():
    r"""
    >>> jane = Node(G, 'jane', favorite_color='blue')
    >>> jane.props
    {'favorite_color': 'blue'}
    >>> G.friend += ('alice', jane)

    >>> G.friend.draw(weights=False, filename='docs/imgs/G_friend_2')
    <graphviz.dot.Digraph object at ...>
    """


def session_00004_line_120():
    r"""
    >>> p(G.friend)
    [friend(bob, alice), friend(alice, jane)]
    """


def session_00005_line_127():
    r"""
    >>> G.friend += [('bob', 'sal'), ('alice', 'rick')]

    >>> G.friend.draw(weights=False, filename='docs/imgs/G_friend_3')
    <graphviz.dot.Digraph object at ...>
    """


def session_00006_line_149():
    r"""
    >>> G.add_relation('coworker', incidence=True)
    """


def session_00007_line_156():
    r"""
    >>> G.coworker += [('bob', ('jane', 'alice')), (('alice', 'bob'), 'jane')]

    >>> G.coworker.draw(weights=True, filename='docs/imgs/G_coworker_1')
    <graphviz.dot.Digraph object at ...>
    """


def session_00008_line_170():
    r"""
    >>> G.add_relation('distance', int)
    >>> G.distance += [('bob', 'alice', 422), ('alice', 'jane', 42)]

    >>> G.distance.draw(weights=True, filename='docs/imgs/G_distance_2')
    <graphviz.dot.Digraph object at ...>
    """


def session_00009_line_184():
    r"""
    >>> G.draw(weights=True, filename='docs/imgs/G_all_1')
    <graphviz.dot.Digraph object at ...>
    """


def session_00010_line_196():
    r"""
    >>> p(G())
    [friend(bob, alice),
     friend(bob, sal),
     friend(alice, jane),
     friend(alice, rick),
     coworker((bob), (alice, jane), (True, True)),
     coworker((bob, alice), (jane), (True)),
     distance(bob, alice, 422),
     distance(alice, jane, 42)]
    """


def session_00011_line_210():
    r"""
    >>> p(G(source='bob'))
    [friend(bob, alice),
     friend(bob, sal),
     coworker((bob), (alice, jane), (True, True)),
     coworker((bob, alice), (jane), (True)),
     distance(bob, alice, 422)]
    """


def session_00012_line_221():
    r"""
    >>> p(G(relation='coworker'))
    [coworker((bob), (alice, jane), (True, True)),
     coworker((bob, alice), (jane), (True))]

    """


def session_00013_line_230():
    r"""
    >>> p(G(destination='jane'))
    [friend(alice, jane),
     coworker((bob), (alice, jane), (True, True)),
     coworker((bob, alice), (jane), (True)),
     distance(alice, jane, 42)]
    """


def session_00014_line_242():
    r"""
    >>> p(G(source='bob', relation='coworker', destination='jane'))
    [coworker((bob), (alice, jane), (True, True)),
     coworker((bob, alice), (jane), (True))]
    """


def session_00015_line_255():
    r"""
    >>> G.add_relation('karate')
    >>> G.karate += G.sql(
    ...  "select 'k_' || s_id, 'k_' || d_id "
    ...  "from graphony.karate")

    >>> G.karate.draw(weights=False, filename='docs/imgs/G_karate_3',
    ...               directed=False, graph_attr=dict(layout='sfdp'))
    <graphviz.dot.Graph object at ...>
    """


def session_00016_line_270():
    r"""
    >>> len(G.karate)
    78
    """


def session_00017_line_277():
    r"""
    >>> from more_itertools import windowed
    >>> G.add_relation('debruijn', incidence=True)
    >>> G.debruijn += windowed(map("".join, windowed('ATACGATACAGATACATAGAGATAC', 2)), 2)
    >>> G.debruijn.draw(weights=False, concentrate=False, filename='docs/imgs/G_debruijn_1')
    <graphviz...>
    """


def session_00018_line_301():
    r"""
    >>> G
    <Graph [friend, coworker, distance, karate]: 87>

    >>> from graphony.lib import pagerank
    >>> G.add_relation('PR')
    >>> I = "BCDEFDEEFGGHHIIJK"
    >>> J = "CBBBBADFEBEBEBEEE"
    >>> G.PR += zip(I, J)
    >>> rank, iters = pagerank(G.PR(cast=FP64))

    >>> G.PR.draw(weights=False, filename='docs/imgs/G_PR_1', rankdir='BT',
    ...           label_vector=rank, label_width=4)
    <graphviz.dot.Digraph object at ...>
    """
