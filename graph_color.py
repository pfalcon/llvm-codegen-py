from graph import Ungraph
from copy import deepcopy
from pprint import pprint

# MCIiJ p.220

class RegColoring:

    def __init__(self, graph, K):
        self.g = graph
        self.K = K
        self.node_stack = []
        self.all_colors = set([x for x in xrange(K)])

    def simplify(self):
        """Simplify algorithm. Returns True if simplification is complete and
        graph is empty or false if only significant-degree nodes left in it."""

        while not self.g.empty():
            found = False
            for n in sorted(self.g.iter_nodes()):
                if self.g.degree(n) < self.K:
                    found = True
                    self.node_stack.append((n, self.g.neighs(n)))
                    self.g.remove(n)
                    print "Removed:", n
                    print "Graph after removal:", self.g
                    break
            if not found:
                return False

        return True

    def select(self):
        assert self.g.empty()

        while self.node_stack:
            node, neighs = self.node_stack.pop()
            self.g.add_with_neighs(node, neighs)

            n_neighs = self.g.neighs(node)
            assert neighs == n_neighs

            used_colors = set([self.g.get_node_attr(n, "color") for n in neighs])
            assert None not in used_colors
#                if None in used_colors:
#                    used_colors.remove(None)
            remaining_colors = self.all_colors - used_colors
            remaining_colors = sorted(list(remaining_colors))
            self.g.set_node_attr(node, "color", remaining_colors[0])
            print "color %s = %s" % (node, remaining_colors[0])

    def get_coloring(self):
        return [(n, self.g.get_node_attr(n, "color")) for n in self.g.iter_nodes()]
