#!/usr/bin/env python
import sys
import re

from llvm.core import *
import llvm
import pllvm


INDENT = "  "

PRED_MAP = {ICMP_EQ: "eq"}
LINKAGE_MAP = {LINKAGE_PRIVATE: "private", LINKAGE_COMMON: "common"}

def prim_type(type):
    return type.split(" ", 1)[0]

def render_arg(arg):
    if isinstance(arg, PConstantInt):
        return str(arg)
    else:
        return "%s %s" % (arg.type, arg)

def render_untyped_arg(arg):
    return str(arg)

def render_typed_arg(arg):
    attrs = getattr(arg, "attributes", set())
    flags = ""
    if ATTR_NO_CAPTURE in attrs:
        flags += " nocapture"
    return "%s%s %s" % (arg.type, flags, arg)

def render_args(args):
    return ", ".join([render_arg(x) for x in args])

def render_untyped_args(args):
    """Render list of args without any types.
    (E.g. for instructions with homogenic arg types, where type
    of arge is the the same as type of instruction.)"""
    return ", ".join([render_untyped_arg(x) for x in args])

def render_typed_args(args):
    """Render list of args, each arg accompanied by type.
    (E.g. function call args)"""
    return ", ".join([render_typed_arg(x) for x in args])

def render_types(args):
    return ", ".join([str(x.type) for x in args])


class PModule(pllvm.PModule):
    pass


class PGlobalVariable(pllvm.PGlobalVariable):
    @classmethod
    def from_llvm(cls, v):
        self = cls()
        self.name = v.name
        self.pointer_type = v.type
        self.type = v.type
        self.type_str = str(v.type)[:-1]
        self.is_declaration = v.is_declaration
        self.initializer = convert_arg(v.initializer)
        self.linkage = LINKAGE_MAP[v.linkage]
        self.alignment = v.alignment
        self.global_constant = v.global_constant
        self.unnamed_addr = "unnamed_addr" in str(v)
        return self


class PArgument(pllvm.PArgument):
    pass


class PGlobalVariableRef(pllvm.PGlobalVariableRef):
    pass


class PConstantInt(pllvm.PConstantInt):
    pass


class PConstantDataArray(pllvm.PConstantDataArray):
    pass


# Virtual objects
class PTmpVariable(pllvm.PTmpVariable):
    pass


class PLabelRef(pllvm.PLabelRef):
    pass


class PConstantExpr(pllvm.PConstantExpr):

    @classmethod
    def from_llvm(cls, expr):
        e = cls()
        e.type = expr.type
        e.opcode_name = expr.opcode_name
        e.operands = [convert_arg(x) for x in expr.operands]
        return e


def convert_arg(a):
    if isinstance(a, Argument):
        return PArgument(a.name, a.type)
    if isinstance(a, GlobalVariable):
        return PGlobalVariableRef(a.name, a.type)
    if isinstance(a, Function):
        return PFunction.from_llvm(a, is_ref=True)
    if isinstance(a, ConstantInt):
        return PConstantInt(a.z_ext_value, a.type)
    if isinstance(a, ConstantDataArray):
        return PConstantDataArray(a)
    if isinstance(a, ConstantExpr):
        return PConstantExpr.from_llvm(a)
    if isinstance(a, BasicBlock):
        return PLabelRef(a.name)
    if isinstance(a, Instruction):
        # Result of instruction is temporary
        return PTmpVariable(a.name, a.type)

    raise NotImplementedError(a, type(a))



class PInstruction(pllvm.PInstruction):

    @classmethod
    def from_llvm(cls, parent_block, i):
#        print i.name, i.type, i.opcode_name, i.operands
        out_i = cls()
        out_i.parent = parent_block
        out_i.name = i.name
        out_i.type = i.type
        out_i.opcode_name = i.opcode_name
        out_i.predicate = None
        if hasattr(i, "predicate"):
            out_i.predicate_code = i.predicate
            out_i.predicate = PRED_MAP[i.predicate]
        out_i.operands = [convert_arg(x) for x in i.operands]
        if i.opcode_name == "getelementptr":
            out_i.inbounds = "inbounds" in str(i)
        elif i.opcode_name == "phi":
            out_i.incoming_vars = []
            for x in xrange(i.incoming_count):
                o = i.get_incoming_value(x)
                label = i.get_incoming_block(x).name
                # If this is instruction, i.e. tmpvar, then we came from it basic block
                if isinstance(o, Instruction):
                    out_i.incoming_vars.append((convert_arg(o), label))
                # Alternatively, this can be incoming function argument from basic block %0
                elif isinstance(o, Argument):
                    out_i.incoming_vars.append((convert_arg(o), label))
                # Finally, this can be implicit initialization constant also from bbock %0
                # Not that de-SSA-ization must convert this implicit initialization into
                # explicit!
                elif isinstance(o, ConstantInt):
                    out_i.incoming_vars.append((convert_arg(o), label))
                else:
                    assert False, "Unsupported phi arg type"
        return out_i


class PBasicBlock(pllvm.PBasicBlock):
    pass


class PFunction(pllvm.PFunction):

    @classmethod
    def from_llvm(cls, f, is_ref=False):
        self = cls()
        self.is_ref = is_ref
        self.name = f.name
        self.type = f.type
        self.args = []
        for x in f.args:
            attrs = x.attributes
            x = convert_arg(x)
            x.attributes = attrs
            self.args.append(x)
        self.is_declaration = f.is_declaration
        self.vararg = f.type.pointee.vararg
        self.does_not_throw = f.does_not_throw
        self.result_type = prim_type(str(self.type))
        return self


class IRConverter(object):
    """Convert LLVM IR module to Python representation."""

    @classmethod
    def number_tmps(cls, mod):
        tmp_i = 0
        for f in mod.functions:
#            print `f`
            f_type = str(f.type)[:-1]
            f_type = f_type.split(" ", 1)
            f_type = f_type[0] + " function " + f_type[1]
            for b in f.basic_blocks:
#                print "BB name:", b.name
                if not b.name:
                    b.name = "%d" % tmp_i
                    tmp_i += 1
                for i in b.instructions:
#                    print i
                    if not i.name and i.type != Type.void():
                        i.name = "%d" % tmp_i
                        tmp_i += 1

    @classmethod
    def convert(cls, mod):
        cls.number_tmps(mod)

        out_mod = PModule()

        for v in mod.global_variables:
#            print dir(v)
#            for a in dir(v):
#                print a, getattr(v, a)
#            print v.visibility, v.linkage, "=%s=" % v.section
#            print v.initializer
            out_mod.global_variables.append(PGlobalVariable.from_llvm(v))

        for f in mod.functions:
            out_f = PFunction.from_llvm(f)
            for b in f.basic_blocks:
                out_b = PBasicBlock(out_f, b.name)
                for i in b.instructions:
#                    print "# %s" % i
                    out_b.append(PInstruction.from_llvm(out_b, i))
                out_f.append(out_b)
            out_mod.append(out_f)

        return out_mod


if __name__ == "__main__":
    with open(sys.argv[1]) as asm:
        mod = Module.from_assembly(asm)
    out_mod = IRConverter.convert(mod)
    #print "============="
    pllvm.IRRenderer.render(out_mod)
