from copy import deepcopy

from graph import UngraphAdjList as Ungraph
from graph_color import RegColoring


def assert_coloring(g, colors, expected_coloring):
    org_g = deepcopy(g)
    c = RegColoring(g, colors)
    assert c.simplify()
    c.select()
    print c.g
    assert c.g == org_g
    coloring = sorted(c.get_coloring())
    assert coloring == expected_coloring, coloring
    print "-----------"


def test_color_1_node():
    g = Ungraph.from_neigh_list({"a": []})
    assert_coloring(g, 5, [("a", 0)])

def test_color_2_nodes():
    g = Ungraph.from_neigh_list({"a": ["b"], "b": ["a"]})
    assert_coloring(g, 5, [("a", 1), ("b", 0)])

def test_color_3_nodes():
    g = Ungraph.from_neigh_list({"a": ["b", "c"], "b": ["a", "c"], "c": ["a", "b"]})
    assert_coloring(g, 5, [('a', 2), ('b', 1), ('c', 0)])

def test_color_4_nodes_1():
    #"""
    #a-b
    #| |
    #d-c
    #"""
    g = Ungraph.from_neigh_list({
        "a": ["b", "d"], "b": ["a", "c"], "c": ["b", "d"], "d": ["a", "c"]
    })
    assert_coloring(g, 5, [('a', 1), ('b', 0), ('c', 1), ('d', 0)])

def test_color_4_nodes_2():
    #"""
    #a-b
    #|\|
    #d-c
    #"""
    g = Ungraph.from_neigh_list({
        "a": ["b", "c", "d"], "b": ["a", "c"], "c": ["a", "b", "d"], "d": ["a", "c"]
    })
    assert_coloring(g, 5, [('a', 2), ('b', 0), ('c', 1), ('d', 0)])

def test_appel_2ed_p221():
    # "Graph from MCIiJ p.221"
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
    assert_coloring(g, 4,
        [('b', 1), ('c', 2), ('d', 2), ('e', 2), ('f', 3), ('g', 2), ('h', 0), ('j', 1), ('k', 0), ('m', 0)]
    )
