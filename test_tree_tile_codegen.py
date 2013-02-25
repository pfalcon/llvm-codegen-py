from tree_tile import *


def test_add_c_c():
    cg = CodeGen(patterns)
    mi = cg.gen((ADD, CONST(1), CONST(2)))
    assert mi == ["mov a, #1", "add a, #2"], mi

def test_add_commute():
    cg = CodeGen(patterns)
    mi1 = cg.gen((ADD, NAME("foo"), CONST(2)))
    mi2 = cg.gen((ADD, CONST(2), NAME("foo")))
    assert mi1 == mi2, "%s != %s" % (mi1, mi2)

def test_add_n_n():
    cg = CodeGen(patterns)
    mi = cg.gen((ADD, NAME("foo"), NAME("bar")))
    assert mi == ["mov a, foo", "add a, bar"], mi
