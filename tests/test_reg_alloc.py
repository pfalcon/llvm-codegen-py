import os
from cStringIO import StringIO
import difflib

from pllvm import *
from parse import *
from reg_alloc import *


datadir = os.path.dirname(__file__) + "/data/"

def get_mod(fname):
    p = IRParser(open(datadir + fname))
    mod = p.parse()
    return mod

def reg_alloc(fname, K, expected_map):
    mod = get_mod(fname)
    ra = RegAlloc(mod[0], K)
    reg_map = ra.alloc()
    print reg_map
    assert reg_map == expected_map
    IRRenderer.render(mod)
    print "-----------"
    ra.rewrite_regs()
    IRRenderer.render(mod)



def test_appel_2ed_p204():
    reg_alloc("appel-2ed-p204.ll", 4, {'a': 1, 'c': 0, 'b': 1})
