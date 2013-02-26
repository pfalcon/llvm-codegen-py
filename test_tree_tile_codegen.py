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

def test_add_n_n_n():
    cg = CodeGen(patterns)
    mi = cg.gen((ADD, (ADD, NAME("foo"), NAME("bar")), NAME("baz")))
    assert mi == ["mov a, foo", "add a, bar", "add a, baz"], mi
    mi2 = cg.gen((ADD, NAME("baz"), (ADD, NAME("foo"), NAME("bar"))))
    assert mi == mi2, "%s != %s" % (mi, mi2)

def test_add_generic():
    cg = CodeGen(patterns)
    mi = cg.gen((ADD, (ADD, NAME("v1"), NAME("v2")),
                      (ADD, NAME("v3"), NAME("v4"))))
    assert mi == ["mov a, v1", "add a, v2", "push A", "mov a, v3", "add a, v4", "pop R2", "add a, r2"], mi

def test_load_memx():
    cg = CodeGen(patterns)
    mi = cg.gen((MEMX, CONST(5)))
    assert mi == ["mov dptr, #5", "movx a,@dptr"], mi

def test_load_memi():
    cg = CodeGen(patterns)
    mi = cg.gen((MEMI, CONST(10)))
    assert mi == ["mov r0, #10", "mov a,@r0"], mi
