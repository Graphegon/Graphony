"""pytest file built from README.md"""
import pytest

from phmdoctest.fixture import managenamespace


@pytest.fixture(scope="module")
def _phm_setup_doctest_teardown(doctest_namespace, managenamespace):
    # setup code line 47.
    import pprint
    from graphony import Graph, Node
    from graphony.tests import setup

    p = lambda r: pprint.pprint(sorted(list(r)))

    db_conn_string = setup()
    G = Graph(db_conn_string)

    managenamespace(operation="update", additions=locals())
    # update doctest namespace
    additions = managenamespace(operation="copy")
    for k, v in additions.items():
        doctest_namespace[k] = v
    yield
    # teardown code line 264.
    from graphony.tests import teardown
    teardown()

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


def session_00001_line_101():
    r"""
    >>> G.relation('friend')
    """


def session_00002_line_107():
    r"""
    >>> G += ('friend', 'bob', 'alice')
    """


def session_00003_line_115():
    r"""
    >>> jane = Node(G, 'jane', favorite_color='blue')
    >>> G += ('friend', 'alice', jane)
    """


def session_00004_line_123():
    r"""
    >>> p(G)
    [(friend, bob, alice, True), (friend, alice, jane, True)]
    """


def session_00005_line_130():
    r"""
    >>> G.relation('coworker', incidence=True)
    >>> G += [('coworker', 'bob', 'jane'), ('coworker', 'alice', 'jane')]
    """


def session_00006_line_141():
    r"""
    >>> G.relation('distance', int)
    >>> G += [('distance', 'chicago', 'seattle', 422),
    ...       ('distance', 'seattle', 'portland', 42)]
    """


def session_00007_line_154():
    r"""
    >>> p(G())
    [(friend, bob, alice, True),
     (friend, alice, jane, True),
     (coworker, bob, jane, True),
     (coworker, alice, jane, True),
     (distance, chicago, seattle, 422),
     (distance, seattle, portland, 42)]
    """


def session_00008_line_166():
    r"""
    >>> p(G(source='bob'))
    [(friend, bob, alice, True), (coworker, bob, jane, True)]
    """


def session_00009_line_173():
    r"""
    >>> p(G(relation='coworker'))
    [(coworker, bob, jane, True), (coworker, alice, jane, True)]
    """


def session_00010_line_180():
    r"""
    >>> p(G(destination='jane'))
    [(friend, alice, jane, True),
     (coworker, bob, jane, True),
     (coworker, alice, jane, True)]

    >>> p(G(source='bob', relation='coworker', destination='jane'))
    [(coworker, bob, jane, True)]
    """


def session_00011_line_193():
    r"""
    >>> p(G)
    [(friend, bob, alice, True),
     (friend, alice, jane, True),
     (coworker, bob, jane, True),
     (coworker, alice, jane, True),
     (distance, chicago, seattle, 422),
     (distance, seattle, portland, 42)]
    """


def session_00012_line_206():
    r"""
    >>> G.friend
    <Adjacency friend BOOL:2>

    >>> G.coworker
    <Incidence coworker BOOL:2>
    """


def session_00013_line_216():
    r"""
    >>> p(list(G.friend))
    [(friend, bob, alice, True), (friend, alice, jane, True)]
    """


def session_00014_line_242():
    r"""
    >>> G.relation('karate')
    >>> G += G.sql(
    ...  "select 'karate', 'karate_' || s_id, 'karate_' || d_id "
    ...  "from graphony.karate")
    """


def session_00015_line_252():
    r"""
    >>> len(G.karate)
    78
    """


def session_00016_line_258():
    r"""
    >>> G
    <Graph [friend, coworker, distance, karate]: 84>
    """
