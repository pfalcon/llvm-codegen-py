import os

from graph import *
from parse import *
from liveness import *


datadir = os.path.dirname(__file__) + "/data/"

def test_appel_2ed_p204():
    expected_ranges = [
        set(["a", "c"]),
        set(["b", "c"]),
        set(["b", "c"]),
        set(["a", "c"]),
        set(["a", "c"]),
        set([]),
    ]
    p = IRParser(open(datadir + "appel-2ed-p204.ll"))
    mod = p.parse()
    f = mod["func"]
    l = Liveness(f)
    live_ranges = l.live_out_map()
    print live_ranges
    for i, inst in enumerate(f.iter_insts()):
        print i, inst
        assert live_ranges[inst] == expected_ranges[i], "[%s] %s vs %s" % (inst, live_ranges[inst], expected_ranges[i])


def test_appel_2ed_p204_llvm_variant():
    expected_ranges = [
        set(["a", "c"]),
        set(["b", "c"]),
        set(["b", "c"]),
        set(["a", "c"]),
        set(["a", "c", "btmp"]), # Not in Appel, for icmp inst
        set(["a", "c"]),
        set([]),
    ]
    p = IRParser(open(datadir + "appel-2ed-p204-llvm-br.ll"))
    mod = p.parse()
    f = mod["func"]
    l = Liveness(f)
    live_ranges = l.live_out_map()
    print live_ranges
    for i, inst in enumerate(f.iter_insts()):
        print i, inst
        assert live_ranges[inst] == expected_ranges[i], "[%s] %s vs %s" % (inst, live_ranges[inst], expected_ranges[i])
