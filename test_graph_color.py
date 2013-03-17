from copy import deepcopy

from graph import Ungraph
from graph_color import RegColoring


def assert_coloring(g, expected_coloring):
    org_g = deepcopy(g)
    c = RegColoring(g, 10)
    assert c.simplify()
    c.select()
    print c.g
    c.g.normalize()
    assert c.g == org_g
    coloring = sorted(c.get_coloring())
    assert coloring == expected_coloring, coloring
    print "-----------"


def test_color_1_node():
    g = Ungraph.from_neigh_list({"a": []})
    assert_coloring(g, [("a", 0)])

def test_color_2_nodes():
    g = Ungraph.from_neigh_list({"a": ["b"], "b": ["a"]})
    assert_coloring(g, [("a", 1), ("b", 0)])

def test_color_3_nodes():
    g = Ungraph.from_neigh_list({"a": ["b", "c"], "b": ["a", "c"], "c": ["a", "b"]})
    assert_coloring(g, [('a', 2), ('b', 0), ('c', 1)])

def test_color_4_nodes_1():
    """
    a-b
    | |
    d-c
    """
    g = Ungraph.from_neigh_list({
        "a": ["b", "d"], "b": ["a", "c"], "c": ["b", "d"], "d": ["a", "c"]
    })
    assert_coloring(g, [('a', 1), ('b', 0), ('c', 1), ('d', 0)])

def test_color_4_nodes_2():
    """
    a-b
    |\|
    d-c
    """
    g = Ungraph.from_neigh_list({
        "a": ["b", "c", "d"], "b": ["a", "c"], "c": ["a", "b", "d"], "d": ["a", "c"]
    })
    assert_coloring(g, [('a', 2), ('b', 0), ('c', 1), ('d', 0)])

def test_MCI_graph():
    "Graph from MCIiJ p.221"
    NEIGHS = {
    "j": ["f", "e", "k", "d", "h", "g"],
    "f": ["j", "e", "m"],
    "e": ["j", "f", "m", "b"],
    "m": ["f", "e", "b", "c"],
    "b": ["k", "e", "m", "c", "d"],
    "m": ["b", "e", "f", "d", "c"],
    "k": ["j", "b", "d", "g"],
    "h": ["j", "g"],
    "g": ["h", "k", "j"],
    "d": ["j", "k", "b", "m"],
    "c": ["b", "m"],
    }

    g = Ungraph.from_neigh_list(NEIGHS)
    g.normalize()
    assert_coloring(g,
        [('b', 3), ('c', 1), ('d', 2), ('e', 2), ('f', 1), ('g', 2), ('h', 1), ('j', 0), ('k', 1), ('m', 0)])
