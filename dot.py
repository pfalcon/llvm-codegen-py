import sys
import re

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


def unquote(s):
    if s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return s


def parse(f, graph):
    l = f.readline()
    assert l.startswith("graph") or l.startswith("digraph")
    for l in f:
        if l.strip() == "}":
            break
        fields = re.split(r"-[->]", l, 1)
        fields = [x.strip() for x in fields]
        graph.add_edge(unquote(fields[0]), unquote(fields[1]))
    return graph
