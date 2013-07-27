class IGraph(object):

    # directed = None

    def empty(self):
        "Return True if graph is empty."
        raise NotImplementedError

    def add_edge(self, from_node, to_node):
        """Add edge between 2 nodes. If any of the nodes does not exist,
        it will be created."""
        raise NotImplementedError

    def iter_edges(self):
        "Iterate over all edges in the graph."
        raise NotImplementedError

    def iter_nodes(self):
        "Iterate over all nodes in the graph."
        raise NotImplementedError

    def neighs(self, n):
        "Return list of node's neighbors."
        raise NotImplementedError

    def degree(self, n):
        "Return node's degree, i.e. number of its neighbors."
        return len(self.neighs(n))


class DigraphEdgeList(IGraph):

    directed = True

    def __init__(self):
        self.edge_list = set()

    @classmethod
    def from_edge_list(cls, edge_list):
        self = cls()
        for from_node, to_node in edge_list:
            self.add_edge(from_node, to_node)
        return self

    def empty(self):
        return len(self.edge_list) == 0

    def add_edge(self, from_node, to_node):
        self.edge_list.add((from_node, to_node))

    def iter_edges(self):
        return iter(self.edge_list)

    def iter_nodes(self):
        seen = set()
        for nodes in self.edge_list:
            for n in nodes:
                if n not in seen:
                    seen.add(n)
                    yield n

    def __eq__(self, other):
        return self.edge_list == other.edge_list


class UngraphEdgeList(DigraphEdgeList):

    directed = False

    def add_edge(self, from_node, to_node):
        if from_node < to_node:
            edge = (from_node, to_node)
        else:
            edge = (to_node, from_node)
        DigraphEdgeList.add_edge(self, *edge)

    def neighs(self, n):
        "Return list of node's neighbors."
        neighs = []
        for from_node, to_node in self.edge_list:
            if from_node == n:
                neighs.append(to_node)
            elif to_node == n:
                neighs.append(from_node)
        return neighs


class DigraphAdjList(IGraph):
    "Graph representation based on adjacency (neighborhood) list for each node."

    def __init__(self):
        self.neigh_list = {}

    def empty(self):
        return len(self.neigh_list) == 0

    def neighs(self, n):
        "Return list of node's neighbors."
        return self.neigh_list[n]

    def succ(self, n):
        return self.neighs(n)

    def pred(self, n):
        preds = []
        for fr, to in self.iter_edges():
            if to == n:
                preds.append(fr)
        return preds

    def iter_edges(self):
        "Iterate over all edges in the graph."
        for node, neighs in self.neigh_list.iteritems():
            for neigh in neighs:
                yield (node, neigh)


class Digraph(object):
    """Directed graph class, can be created from 2 representations:
    Edge list:
        (Node1 -> Node2), (Node1 -> Node3), ...
    Neighbors list:
        { Node1: [Node2, Node3], ... }
    """

    def __init__(self):
        self.edge_list = None
        self.neigh_list = None
        self.node_attrs = {}

    @classmethod
    def from_edge_list(cls, l):
        g = cls()
        g.edge_list = l
        return g

    @classmethod
    def from_neigh_list(cls, l):
        g = cls()
        g.neigh_list = l
        return g

    def empty(self):
        "Return True if graph is empty, i.e. contains 0 nodes."
        if self.edge_list is not None:
            return len(self.edge_list) == 0
        else:
            return len(self.neigh_list) == 0

    def neighs(self, n):
        "Return list of node's neighbors."
        if self.neigh_list is not None:
            return self.neigh_list[n]
        else:
            raise NotImplementedError

    def succ(self, n):
        return self.neighs(n)

    def pred(self, n):
        preds = []
        for fr, to in self.iter_edges():
            if to == n:
                preds.append(fr)
        return preds

    def degree(self, n):
        "Return node's degree, i.e. number of its neighbors."
        if self.neigh_list is not None:
            return len(self.neigh_list[n])
        else:
            raise NotImplementedError

    def get_edge_list(self):
        "Return list of all edges in the graph."
        if self.edge_list is not None:
            return self.edge_list
        else:
            raise NotImplementedError

    def iter_nodes(self):
        "Iterate over all nodes in the graph."
        if self.neigh_list is not None:
            return self.neigh_list.iterkeys()
        else:
            raise NotImplementedError

    def iter_edges(self):
        "Iterate over all edges in the graph."
        if self.neigh_list is not None:
            for node, neighs in self.neigh_list.iteritems():
                for neigh in neighs:
                    yield (node, neigh)
        else:
            raise NotImplementedError

    def remove(self, n):
        "Remove node and all its edges from the graph."
        if self.neigh_list is not None:
            del self.neigh_list[n]
            for nd, neighs in self.neigh_list.iteritems():
                try:
                    neighs.remove(n)
                except ValueError:
                    pass
        else:
            raise NotImplementedError

    def get_node_attr(self, node, attr):
        "Get node attribute (arbitrary named values attached to node)."
        return self.node_attrs.setdefault(node, {}).get(attr)

    def set_node_attr(self, node, attr, val):
        "Set node attribute (arbitrary named values attached to node)."
        self.node_attrs.setdefault(node, {})[attr] = val

    def __str__(self):
        if self.edge_list is not None:
            return str(self.edge_list)
        else:
            return str(self.neigh_list)

    def print_with_attrs(self):
        for n in self.iter_nodes():
            print n, self.node_attrs.get(n), self.succ(n)

    def __eq__(self, other):
        if self.neigh_list is not None and other.neigh_list is not None:
            return self.neigh_list == other.neigh_list
        raise NotImplementedError


class Ungraph(Digraph):
    """Undirected graph. Implementation is based on Digraph, and requires
    edges of both direction between nodes to be recorded.
    """

    def normalize_edge_repr(self):
        for n in self.edge_list:
            if n[0] > n[1]:
                n[0], n[1] = n[1], n[0]

    def normalize_neigh_repr(self):
        for n, neighs in self.neigh_list.iteritems():
            neighs.sort()

    def normalize(self):
        if self.edge_list is not None:
            self.normalize_edge_repr()
        else:
            self.normalize_neigh_repr()

    def add_with_neighs(self, node, neighs):
        "Add node to the graph, together with edges to specified neighbors."
        for n in neighs:
            self.neigh_list[n].append(node)
        self.neigh_list[node] = neighs
