import os

from graph import *
from parse import *
from liveness import *
from interference import *
import dot


datadir = os.path.dirname(__file__) + "/data/"

def gen_interf(fname):
    p = IRParser(open(datadir + fname))
    mod = p.parse()
    f = mod[0]
    l = Liveness(f)
    ig = InterferenceGraph(f, l)
    dot.dot(ig, open(fname + ".dot", "w"))
    return ig

def test_interference():
    ig = gen_interf("appel-2ed-p204.ll")
    assert ig == UngraphEdgeList.from_edge_list([("a", "c"), ("b", "c")])

def test_appel_2ed_p221():
    ig = gen_interf("appel-2ed-p221.ll")
    refg = dot.parse(open(datadir + "appel-2ed-p221.dot"), UngraphEdgeList())
    assert ig == refg, "%s vs %s" % (ig, refg)

def test_clang_strlen():
    ig = gen_interf("strlen.ll.nossa")
