from copy import deepcopy

from graph import *


def test_ungraph_edge_normalize():
    g = UngraphEdgeList.from_edge_list([["a", "b"], ["d", "c"]])
    assert g == UngraphEdgeList.from_edge_list([["a", "b"], ["c", "d"]])

def test_ungraph_adj_compare():
    g1 = UngraphAdjList.from_neigh_list({"a": []})
    g2 = UngraphAdjList.from_neigh_list({"a": []})
    assert g1 == g2
    g3 = deepcopy(g1)
    assert g1 == g3

    h1 = UngraphAdjList.from_neigh_list({"b": []})
    assert g1 != h1

    h2 = UngraphAdjList.from_neigh_list({"a": ["b"]})
    assert g1 != h2

    g1.add_node("b")
    assert g1 != h2
    g1.add_edge("a", "b")
    assert g1 == h2
