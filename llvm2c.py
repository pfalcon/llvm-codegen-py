import sys
import re

from llvm2py import *


def render_i(s):
    print "  " + s

def render(s):
    print s

def var(v):
    if isinstance(v, PConstantInt):
        return str(v)
    if isinstance(v, PLabelRef):
        return "_" + v.name
    s = v.name
    if s[0].isdigit():
        return "_tmp" + s
    return s

def convert_i(i, defined_vars):
    op = i.opcode_name
    args = i.operands
#    print "//", i
    if op == "ret":
        render_i("return %s;" % var(args[0]))
    elif op == "br":
        if len(args) == 3:
            render_i("if (%s) goto %s; else goto %s;" % (var(args[0]), var(args[2]), var(args[1])))
        else:
            render_i("goto %s;" % var(args[0]))
    elif op == "load":
            render_i("%s %s = %s;" % (i.type, var(i), var(args[0])))
    elif op == "store":
            render_i("%s = %s;" % (var(args[1]), var(args[0])))
    elif op == "mov":
        if i.name in defined_vars:
            render_i("%s = %s;" % (var(i), var(args[0])))
        else:
            render_i("%s %s = %s;" % (i.type, var(i), var(args[0])))
        # mov is the only case when same var can be reused, the rest
        # vars are SSA-conformant
        defined_vars.add(i.name)
    elif op == "icmp":
        c_op = {"eq": "==", "ne": "!="}[i.predicate]
        render_i(("%s %s = %s " + c_op + " %s;") % (i.type, var(i), var(args[0]), var(args[1])))
    elif op in ["add", "sub"]:
        params = [i, args[0], args[1]]
        params = [var(x) for x in params]
        params = [i.type] + params
        c_op = {"add": "+", "sub": "-"}[op]
        render_i(("%s %s = %s " + c_op + " %s;") % tuple(params))
    else:
        print "//", i

def convert(mod):
    render('#include "llvmir.h"')
    render("")

    for f in mod:
        if f.is_declaration:
            args = []
            for a in f.args:
                    args.append("%s %s" % (a.type, a.name))
            render("%s %s(%s);" % (f.result_type, f.name, ", ".join(args)))

    for v in mod.global_variables:
        render("%s %s = %s;" % (v.type, v.name, 0))

    for f in mod.functions:
        if not f.is_declaration:
            args = []
            for a in f.args:
                    args.append("%s %s" % (a.type, a.name))
            render("%s %s(%s)" % (f.result_type, f.name, ", ".join(args)))
            render("{")
            defined_vars = set()
            for b in f:
                render("_%s:;" % b.name)
                for i in b.instructions():
                    convert_i(i, defined_vars)
            render("}")

with open(sys.argv[1]) as asm:
    llvmmod = Module.from_assembly(asm)
mod = IRConverter.convert(llvmmod)
PhiResolver.convert(mod)
convert(mod)
