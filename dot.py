# Simple module to output graph as .dot file, which can be viewed
# with dot or xdot.py tools.
def dot(graph):
    print "digraph G {"
    for fr, to in graph.iter_edges():
        print '"%s" -> "%s"' % (fr, to)
    print "}"
