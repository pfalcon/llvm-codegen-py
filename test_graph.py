from copy import deepcopy

from graph import Digraph, Ungraph


def test_ungraph_edges_normalize():
    g = Ungraph.from_edge_list([["a", "b"], ["d", "c"]])
    g.normalize()
    l = g.get_edge_list()
    assert l == [["a", "b"], ["c", "d"]], l

def test_compare():
    g1 = Ungraph.from_neigh_list({"a": []})
    g2 = Ungraph.from_neigh_list({"a": []})
    assert g1 == g2
    g3 = deepcopy(g1)
    assert g1 == g3

    h1 = Ungraph.from_neigh_list({"b": []})
    assert g1 != h1

    h2 = Ungraph.from_neigh_list({"a": ["b"]})
    assert g1 != h2
