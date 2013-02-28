from graph import Digraph, Ungraph


def test_ungraph_edges_normalize():
    g = Ungraph.from_edge_list([["a", "b"], ["d", "c"]])
    g.normalize()
    l = g.get_edge_list()
    assert l == [["a", "b"], ["c", "d"]], l