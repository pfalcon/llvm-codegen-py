import os
from cStringIO import StringIO
import difflib

from llvm2py import *
from parse import *


datadir = os.path.dirname(__file__) + "/data/"

def test_func_if():
    f = "appel-2ed-p204.ll"
    p = IRParser(open(datadir + f))
    mod = p.parse()
    out = StringIO()
    IRRenderer.render(mod, out)
    org = open(datadir + f).readlines()
    new = out.getvalue().splitlines(True)
    diff = "".join(difflib.unified_diff(org, new))
    assert diff == "", "Parse roundtrip mismatch:\n" + diff
