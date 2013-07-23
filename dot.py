import sys

# Simple module to output graph as .dot file, which can be viewed
# with dot or xdot.py tools.
def dot(graph, out=sys.stdout):
    print >>out, "digraph G {"
    for fr, to in graph.iter_edges():
        print >>out, '"%s" -> "%s"' % (fr, to)
    print >>out, "}"
