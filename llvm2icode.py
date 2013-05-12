#!/usr/bin/env python
#
# This tried to convert LLVM IR to SDCC iCode
#
import sys

from llvm.core import *
import llvm


CMP_MAP = {ICMP_EQ: "=="}


def oper(opers):
    return [str(x) for x in opers]

with open(sys.argv[1]) as asm:
    mod = Module.from_assembly(asm)


tmp_i = 1
def number_tmps(mod):
    global tmp_i
    for f in mod.functions:
        print `f`
        f_type = str(f.type)[:-1]
        f_type = f_type.split(" ", 1)
        f_type = f_type[0] + " function " + f_type[1]
        print "proc _%s{%s}" % (f.name, f_type)
        for b in f.basic_blocks:
#            print "BB name:", b.name
            for i in b.instructions:
#                print i
                if not i.name and i.type != Type.void():
                    i.name = "t%d" % tmp_i
                    tmp_i += 1


def arg(a):
    if isinstance(a, Argument):
#        print "arg name:", a.name
#        return str(a)
        return "%s{%s}" % (a.name, a.type)
    if isinstance(a, GlobalVariable):
#        print "arg name:", a.name
#        return str(a)
        return "%s{%s}" % (a.name, str(a.type)[:-1])
    if isinstance(a, ConstantInt):
#        print "arg val:", a.z_ext_value
#        return str(a)
        return "%s{%s}" % (a.z_ext_value, a.type)
    1/0


number_tmps(mod)


lab = 1
for f in mod.functions:
#    print `f`
    for b in f.basic_blocks:
        print " _%s($) :" % b.name
        for i in b.instructions:
            print "#", i
            print "# name:", i.name, "type:", i.type, "op:", i.opcode_name, "operands:", i.operands
            if i.name:
                if i.opcode_name == "icmp":
                    print "%s{%s} = %s %s %s" % (i.name, i.type, arg(i.operands[0]), CMP_MAP[i.predicate], arg(i.operands[1]))
                elif i.opcode_name == "load":
                    a = i.operands[0]
                    if isinstance(a, GlobalVariable):
                        print "%s<nospill>{%s} := %s<addr>" % (i.name, i.type, arg(a))
                    else:
                        1/0
#                elif i.opcode_name == "add":
                else:
                    print "??? %s{%s}" % (i.name, i.type)
