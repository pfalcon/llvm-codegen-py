import os

try:
    import llvm.core
except ImportError:
    from nose.exc import SkipTest
    raise SkipTest("llvmpy module is not available")

from llvm2py import *


datadir = os.path.dirname(__file__) + "/data"

def test_func_if():
    f = "func-if.ll"
    os.system("./llvm2py.py %s/%s >%s/out/%s" % (datadir, f, datadir, f))
    rc = os.system("diff -u %s/%s %s/out/%s" % (datadir, f, datadir, f))
    assert rc == 0, "Roundtrip failed"
