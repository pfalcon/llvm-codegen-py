import os
from cStringIO import StringIO
import difflib

from pllvm import *
from parse import *
from phi_resolver import *


datadir = os.path.dirname(__file__) + "/data/"

def test_strlen():
    f = "strlen.ll"
    p = IRParser(open(datadir + f))
    mod = p.parse()
    PhiResolver.convert(mod)

    out = StringIO()
    IRRenderer.render(mod, out)
    expected = open(datadir + "strlen.ll.nossa").readlines()
    result = out.getvalue().splitlines(True)
    diff = "".join(difflib.unified_diff(expected, result))
    assert diff == "", "Unexpected PHI elimination result:\n" + diff
