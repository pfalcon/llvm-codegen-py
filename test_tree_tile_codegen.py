from tree_tile import *


def test_add_c_c():
    cg = CodeGen(patterns)
    mi = cg.gen((ADD, CONST(1), CONST(2)))
    assert mi == ["mov a, #1", "add a, #2"], mi
