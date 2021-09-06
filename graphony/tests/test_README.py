"""pytest file built from README.md"""
import pytest

from phmdoctest.fixture import managenamespace


@pytest.fixture(scope="module")
def _phm_setup_doctest_teardown(doctest_namespace, managenamespace):
    # setup code line 78.
    import pprint
    import postgresql
    from graphony import Graph, Node
    p = lambda r: pprint.pprint(sorted(list(r)))
    pgdata, db_conn_string = postgresql.setup()
    postgresql.psql(f'-d "{db_conn_string}" -f dbinit/01.sql -f dbinit/02.sql')
    G = Graph(db_conn_string)

    managenamespace(operation="update", additions=locals())
    # update doctest namespace
    additions = managenamespace(operation="copy")
    for k, v in additions.items():
        doctest_namespace[k] = v
    yield
    # teardown code line 291.
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


def session_00001_line_114():
    r"""
    >>> G.add_relation('friend')
    """


def session_00002_line_120():
    r"""
    >>> G.friend += ('bob', 'alice')
    >>> G.friend.draw(show_weight=False, filename='docs/imgs/G_friend_1')
    <graphviz.dot.Digraph object at ...>
    """


def session_00003_line_131():
    r"""
    >>> jane = Node(G, 'jane', favorite_color='blue')
    >>> jane.props
    {'favorite_color': 'blue'}
    >>> G.friend += ('alice', jane)
    >>> G.friend.draw(show_weight=False, filename='docs/imgs/G_friend_2')
    <graphviz.dot.Digraph object at ...>
    """


def session_00004_line_144():
    r"""
    >>> p(G)
    [(friend, bob, alice, True), (friend, alice, jane, True)]
    """


def session_00005_line_151():
    r"""
    >>> G.friend += [('bob', 'sal'), ('alice', 'rick')]
    >>> G.friend.draw(show_weight=False, filename='docs/imgs/G_friend_3')
    <graphviz.dot.Digraph object at ...>
    """


def session_00006_line_164():
    r"""
    >>> G.add_relation('coworker', incidence=True)
    >>> G.coworker += [('bob', 'jane'), ('alice', 'jane')]

    >>> G.add_relation('distance', int)
    >>> G.distance += [('chicago', 'seattle', 422),
    ...                ('seattle', 'portland', 42)]
    """


def session_00007_line_180():
    r"""
    >>> p(G())
    [(friend, bob, alice, True),
     (friend, bob, sal, True),
     (friend, alice, jane, True),
     (friend, alice, rick, True),
     (coworker, bob, jane, True),
     (coworker, alice, jane, True),
     (distance, chicago, seattle, 422),
     (distance, seattle, portland, 42)]
    """


def session_00008_line_194():
    r"""
    >>> p(G(source='bob'))
    [(friend, bob, alice, True),
     (friend, bob, sal, True),
     (coworker, bob, jane, True)]
    """


def session_00009_line_203():
    r"""
    >>> p(G(relation='coworker'))
    [(coworker, bob, jane, True), (coworker, alice, jane, True)]
    """


def session_00010_line_210():
    r"""
    >>> p(G(destination='jane'))
    [(friend, alice, jane, True),
     (coworker, bob, jane, True),
     (coworker, alice, jane, True)]

    >>> p(G(source='bob', relation='coworker', destination='jane'))
    [(coworker, bob, jane, True)]
    """


def session_00011_line_224():
    r"""
    >>> G.friend
    <Adjacency friend BOOL:4>

    >>> G.coworker
    <Incidence coworker BOOL:2>
    """


def session_00012_line_234():
    r"""
    >>> p(list(G.friend))
    [(friend, bob, alice, True),
     (friend, bob, sal, True),
     (friend, alice, jane, True),
     (friend, alice, rick, True)]
    """


def session_00013_line_263():
    r"""
    >>> G.add_relation('karate')
    >>> G.karate += G.sql(
    ...  "select 'k_' || s_id, 'k_' || d_id "
    ...  "from graphony.karate")
    >>> G.karate.draw(show_weight=False, filename='docs/imgs/G_karate_3',
    ...               directed=False, graph_attr=dict(layout='sfdp'))
    <graphviz.dot.Graph object at ...>
    """


def session_00014_line_279():
    r"""
    >>> len(G.karate)
    78
    """


def session_00015_line_285():
    r"""
    >>> G
    <Graph [friend, coworker, distance, karate]: 86>
    """
