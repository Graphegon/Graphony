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
    # teardown code line 284.
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
    >>> G += ('friend', 'bob', 'alice')
    >>> G.draw('friend', filename='docs/imgs/G_friend_1')
    <graphviz.dot.Digraph object at ...>
    """


def session_00003_line_131():
    r"""
    >>> jane = Node(G, 'jane', favorite_color='blue')
    >>> G += ('friend', 'alice', jane)
    """


def session_00004_line_139():
    r"""
    >>> p(G)
    [(friend, bob, alice, True), (friend, alice, jane, True)]
    """


def session_00005_line_146():
    r"""
    >>> G.add_relation('coworker', incidence=True)
    >>> G += [('coworker', 'bob', 'jane'), ('coworker', 'alice', 'jane')]
    """


def session_00006_line_157():
    r"""
    >>> G.add_relation('distance', int)
    >>> G += [('distance', 'chicago', 'seattle', 422),
    ...       ('distance', 'seattle', 'portland', 42)]
    >>> G.draw('friend', filename='docs/imgs/G_friend_2')
    <graphviz.dot.Digraph object at ...>
    """


def session_00007_line_174():
    r"""
    >>> p(G())
    [(friend, bob, alice, True),
     (friend, alice, jane, True),
     (coworker, bob, jane, True),
     (coworker, alice, jane, True),
     (distance, chicago, seattle, 422),
     (distance, seattle, portland, 42)]
    """


def session_00008_line_186():
    r"""
    >>> p(G(source='bob'))
    [(friend, bob, alice, True), (coworker, bob, jane, True)]
    """


def session_00009_line_193():
    r"""
    >>> p(G(relation='coworker'))
    [(coworker, bob, jane, True), (coworker, alice, jane, True)]
    """


def session_00010_line_200():
    r"""
    >>> p(G(destination='jane'))
    [(friend, alice, jane, True),
     (coworker, bob, jane, True),
     (coworker, alice, jane, True)]

    >>> p(G(source='bob', relation='coworker', destination='jane'))
    [(coworker, bob, jane, True)]
    """


def session_00011_line_213():
    r"""
    >>> p(G)
    [(friend, bob, alice, True),
     (friend, alice, jane, True),
     (coworker, bob, jane, True),
     (coworker, alice, jane, True),
     (distance, chicago, seattle, 422),
     (distance, seattle, portland, 42)]
    """


def session_00012_line_226():
    r"""
    >>> G.friend
    <Adjacency friend BOOL:2>

    >>> G.coworker
    <Incidence coworker BOOL:2>
    """


def session_00013_line_236():
    r"""
    >>> p(list(G.friend))
    [(friend, bob, alice, True), (friend, alice, jane, True)]
    """


def session_00014_line_262():
    r"""
    >>> G.add_relation('karate')
    >>> G += G.sql(
    ...  "select 'karate', 'karate_' || s_id, 'karate_' || d_id "
    ...  "from graphony.karate")
    """


def session_00015_line_272():
    r"""
    >>> len(G.karate)
    78
    """


def session_00016_line_278():
    r"""
    >>> G
    <Graph [friend, coworker, distance, karate]: 84>
    """
