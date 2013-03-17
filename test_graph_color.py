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
    assert c.get_coloring() == expected_coloring, c.get_coloring()
    print "-----------"


def test_color_1_node():
    g = Ungraph.from_neigh_list({"a": []})
    assert_coloring(g, [("a", 0)])

def test_color_2_nodes():
    g = Ungraph.from_neigh_list({"a": ["b"], "b": ["a"]})
    assert_coloring(g, [("a", 1), ("b", 0)])

def test_color_3_nodes():
    g = Ungraph.from_neigh_list({"a": ["b", "c"], "b": ["a", "c"], "c": ["a", "b"]})
    assert_coloring(g, [('a', 2), ('c', 1), ('b', 0)])
