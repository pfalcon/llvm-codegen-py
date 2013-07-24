import os

from graph import *
from parse import *
from liveness import *
from interference import *
import dot


datadir = os.path.dirname(__file__) + "/data/"

def test_interference():
    p = IRParser(open(datadir + "appel-2ed-p204.ll"))
    mod = p.parse()
    f = mod["func"]
    l = Liveness(f)
    ig = InterferenceGraph(f, l)
    #dot.dot(ig, open("interf.dot", "w"))
    assert ig == UngraphEdgeList.from_edge_list([("a", "c"), ("b", "c")])
