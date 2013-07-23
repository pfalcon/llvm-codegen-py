import os

from graph import *
from parse import *
from liveness import *


datadir = os.path.dirname(__file__) + "/data/"

def test_func_if():
    expected_ranges = [
        set(["a", "c"]),
        set(["b", "c"]),
        set(["b", "c"]),
        set(["a", "c"]),
        set(["a", "c", "btmp"]), # Not in Appel, for icmp inst
        set(["a", "c"]),
        set([]),
    ]
    p = IRParser(open(datadir + "appel-2ed-p204.ll"))
    mod = p.parse()
    f = mod["func"]
    live_ranges = Liveness.run(f)
    print live_ranges
    for i, inst in enumerate(f.iter_insts()):
        print i, inst
        assert live_ranges[inst] == expected_ranges[i], "[%s] %s vs %s" % (inst, live_ranges[inst], expected_ranges[i])
