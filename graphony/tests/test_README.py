"""pytest file built from README.md"""
import pytest

from phmdoctest.fixture import managenamespace


@pytest.fixture(scope="module")
def _phm_setup_doctest_teardown(doctest_namespace, managenamespace):
    # setup code line 76.
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
    # teardown code line 281.
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


def session_00001_line_111():
    r"""
    >>> G.relation('friend')
    """


def session_00002_line_117():
    r"""
    >>> G += ('friend', 'bob', 'alice')
    """


def session_00003_line_125():
    r"""
    >>> jane = Node(G, 'jane', favorite_color='blue')
    >>> G += ('friend', 'alice', jane)
    """


def session_00004_line_133():
    r"""
    >>> p(G)
    [(friend, bob, alice, True), (friend, alice, jane, True)]
    """


def session_00005_line_140():
    r"""
    >>> G.relation('coworker', incidence=True)
    >>> G += [('coworker', 'bob', 'jane'), ('coworker', 'alice', 'jane')]
    """


def session_00006_line_151():
    r"""
    >>> G.relation('distance', int)
    >>> G += [('distance', 'chicago', 'seattle', 422),
    ...       ('distance', 'seattle', 'portland', 42)]
    >>> from pygraphblas.gviz import draw_graph
    >>> draw_graph(G.friend.A, filename='docs/imgs/G_friend_A')
    <graphviz.dot.Digraph object at ...>

    ![G_friend_A.png](docs/imgs/G_friend_A.png)


    """


def session_00007_line_171():
    r"""
    >>> p(G())
    [(friend, bob, alice, True),
     (friend, alice, jane, True),
     (coworker, bob, jane, True),
     (coworker, alice, jane, True),
     (distance, chicago, seattle, 422),
     (distance, seattle, portland, 42)]
    """


def session_00008_line_183():
    r"""
    >>> p(G(source='bob'))
    [(friend, bob, alice, True), (coworker, bob, jane, True)]
    """


def session_00009_line_190():
    r"""
    >>> p(G(relation='coworker'))
    [(coworker, bob, jane, True), (coworker, alice, jane, True)]
    """


def session_00010_line_197():
    r"""
    >>> p(G(destination='jane'))
    [(friend, alice, jane, True),
     (coworker, bob, jane, True),
     (coworker, alice, jane, True)]

    >>> p(G(source='bob', relation='coworker', destination='jane'))
    [(coworker, bob, jane, True)]
    """


def session_00011_line_210():
    r"""
    >>> p(G)
    [(friend, bob, alice, True),
     (friend, alice, jane, True),
     (coworker, bob, jane, True),
     (coworker, alice, jane, True),
     (distance, chicago, seattle, 422),
     (distance, seattle, portland, 42)]
    """


def session_00012_line_223():
    r"""
    >>> G.friend
    <Adjacency friend BOOL:2>

    >>> G.coworker
    <Incidence coworker BOOL:2>
    """


def session_00013_line_233():
    r"""
    >>> p(list(G.friend))
    [(friend, bob, alice, True), (friend, alice, jane, True)]
    """


def session_00014_line_259():
    r"""
    >>> G.relation('karate')
    >>> G += G.sql(
    ...  "select 'karate', 'karate_' || s_id, 'karate_' || d_id "
    ...  "from graphony.karate")
    """


def session_00015_line_269():
    r"""
    >>> len(G.karate)
    78
    """


def session_00016_line_275():
    r"""
    >>> G
    <Graph [friend, coworker, distance, karate]: 84>
    """
