import os

from llvm2py import *


datadir = os.path.dirname(__file__) + "/data"

def test_func_if():
    f = "func-if.ll"
    os.system("./llvm2py.py %s/%s >%s/out/%s" % (datadir, f, datadir, f))
    os.system("diff -u %s/%s %s/out/%s" % (datadir, f, datadir, f))
