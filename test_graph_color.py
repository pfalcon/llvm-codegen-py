from copy import deepcopy

from graph import Ungraph
from graph_color import RegColoring


def test_color_1_node():
    g = Ungraph.from_neigh_list({"a": []})
    org_g = deepcopy(g)

    c = RegColoring(g, 10)
    assert c.simplify()
    c.select()
    print c.g
    assert c.g == org_g
    assert c.get_coloring() == [("a", 0)], c.get_coloring()
    print "-----------"

def test_color_2_nodes():
    g = Ungraph.from_neigh_list({"a": ["b"], "b": ["a"]})
    org_g = deepcopy(g)

    c = RegColoring(g, 10)
    assert c.simplify()
    c.select()
    print c.g
    assert c.g == org_g
    assert c.get_coloring() == [("a", 1), ("b", 0)], c.get_coloring()
    print "-----------"
