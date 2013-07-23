import sys

# Simple module to output graph as .dot file, which can be viewed
# with dot or xdot.py tools.
def dot(graph, out=sys.stdout, directed=None):
    if directed is None:
        directed = graph.directed
    if directed:
        header = "digraph"
        edge = "->"
    else:
        header = "graph"
        edge = "--"

    print >>out, "%s G {" % header
    for fr, to in graph.iter_edges():
        print >>out, '"%s" %s "%s"' % (fr, edge, to)
    print >>out, "}"
