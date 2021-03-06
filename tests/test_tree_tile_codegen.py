from tree_tile import *


def test_add_c_c():
    cg = CodeGen(patterns)
    mi = cg.gen((ADD, CONST(1), CONST(2)))
    assert mi == ["mov a, #1", "add a, #2"], mi

def test_add_c_c_dag():
    # Test pattern match against DAG
    cg = CodeGen(patterns)
    node = CONST(2)
    tree = (ADD, node, node)
    mi = cg.gen(tree)
    assert mi == ["mov a, #2", "clr c", "rlc a"], mi

def test_add_commute():
    cg = CodeGen(patterns)
    mi1 = cg.gen((ADD, NAME("foo"), CONST(2)))
    mi2 = cg.gen((ADD, CONST(2), NAME("foo")))
    assert mi1 == mi2, "%s != %s" % (mi1, mi2)

def test_add_n_n():
    cg = CodeGen(patterns)
    mi = cg.gen((ADD, (MEMI, CONST("foo")), (MEMI, CONST("bar"))))
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

def test_load_memx_c():
    cg = CodeGen(patterns)
    mi = cg.gen((MEMX, CONST(5)))
    assert mi == ["mov dptr, #5", "movx a,@dptr"], mi

def test_load_memi_c():
    cg = CodeGen(patterns)
    mi = cg.gen((MEMI, CONST(10)))
    assert mi == ["mov a, 10"], mi
    mi = cg.gen((MEMI, CONST(200)))
    assert mi == ["mov r0, #200", "mov a,@r0"], mi

def test_load_memx_n():
    cg = CodeGen(patterns)
    mi = cg.gen((MEMX, NAME("p")))
    assert mi == ["mov DPL, p", "mov DPH, p+1", "movx a, @dptr"], mi

def test_store_memx_gen():
    cg = CodeGen(patterns)
    mi = cg.gen((STORE, NAME("v"), CONST(1)))
    assert mi == ["mov a, #1", "mov v, a"], mi
