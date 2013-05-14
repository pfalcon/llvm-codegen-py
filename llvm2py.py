#!/usr/bin/env python
import sys
import re

from llvm.core import *
import llvm


INDENT = "  "

PRED_MAP = {ICMP_EQ: "eq"}


def prim_type(type):
    return type.split(" ", 1)[0]

def render_arg(arg):
    if isinstance(arg, PConstantInt):
        return str(arg)
    else:
        return "%s %s" % (arg.type, arg)

def render_typed_arg(arg):
    return "%s %s" % (arg.type, arg)

def render_args(args):
    return ", ".join([render_arg(x) for x in args])

def render_typed_args(args):
    return ", ".join([render_typed_arg(x) for x in args])


class PModule(object):
    def __init__(self):
        self.functions = []
        self.global_variables = []

    def append(self, inst):
        self.functions.append(inst)

    def __iter__(self):
        return iter(self.functions)


class PGlobalVariable(object):
    def __init__(self, v):
        self.name = v.name
        self.pointer_type = v.type
        self.type = str(v.type)[:-1]
        self.is_declaration = v.is_declaration
        self.initializer = convert_arg(v.initializer)

    def __str__(self):
        return "@%s = common global %s %s" % (self.name, self.type, self.initializer)

    def __repr__(self):
        return self.__str__()


class PArgument(object):
    def __init__(self, name, type):
        self.name = name
        self.type = type

    def __str__(self):
        return "%" + self.name

    def __repr__(self):
        return self.__str__()

class PGlobalVariableRef(object):
    def __init__(self, name, type):
        self.name = name
        self.type = type

    def __str__(self):
        return "@" + self.name

    def __repr__(self):
        return self.__str__()

class PConstantInt(object):
    def __init__(self, value, type):
        self.value = value
        self.type = type

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return self.__str__()

class PConstantDataArray(object):
    def __init__(self, v):
        self.type = v.type
        m = re.match(r"\[.+? x .+?\] (.+)", str(v))
        self.value = m.group(1)

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return self.__str__()

# Virtual objects
class PTmpVariable(object):
    def __init__(self, name, type):
        self.name = name
        self.type = type

    def __str__(self):
        return "%" + self.name

    def __repr__(self):
        return self.__str__()

class PLabelRef(object):
    def __init__(self, name):
        self.name = name
        self.type = "label"

    def __str__(self):
        return "%" + self.name

    def __repr__(self):
        return self.__str__()

class PConstantExpr(object):

    def __init__(self):
        pass

    @classmethod
    def from_llvm(cls, expr):
        e = cls()
        e.type = expr.type
        e.opcode_name = expr.opcode_name
        e.operands = [convert_arg(x) for x in expr.operands]
        return e

    def __str__(self):
        return "%s(%s)" % (self.opcode_name, render_typed_args(self.operands))

    def __repr__(self):
        return self.__str__()

def convert_arg(a):
    if isinstance(a, Argument):
        return PArgument(a.name, a.type)
    if isinstance(a, GlobalVariable):
        return PGlobalVariableRef(a.name, a.type)
    if isinstance(a, Function):
        return PGlobalVariableRef(a.name, a.type)
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



class PInstruction(object):

    def __init__(self, *args, **kwargs):
        if args or kwargs:
            self.name, self.type, self.opcode_name, self.operands = args

    @classmethod
    def from_llvm(cls, i):
#        print i.name, i.type, i.opcode_name, i.operands
        out_i = cls()
        out_i.name = i.name
        out_i.type = i.type
        out_i.opcode_name = i.opcode_name
        out_i.predicate = None
        if hasattr(i, "predicate"):
            out_i.predicate_code = i.predicate
            out_i.predicate = PRED_MAP[i.predicate]
        out_i.operands = [convert_arg(x) for x in i.operands]
        if i.opcode_name == "phi":
            out_i.incoming_vars = [(o.name, o.basic_block.name) for o in i.operands]
        return out_i

    def __str__(self):
        if self.name:
            if self.opcode_name == "load":
                return INDENT + "%%%s = %s %s" % (self.name, self.opcode_name, render_arg(self.operands[0]))
            if self.opcode_name == "icmp":
                return INDENT + "%%%s = %s %s %s" % (self.name, self.opcode_name, self.predicate, render_args(self.operands))
            if self.opcode_name == "phi":
                args = ", ".join(["[ %%%s, %%%s ]" % x for x in self.incoming_vars])
                return INDENT + "%%%s = %s %s %s" % (self.name, self.opcode_name, self.type, args)
            if self.opcode_name == "call":
                func = self.operands[-1]
                args = self.operands[:-1]
                return INDENT + "%%%s = %s %s %s(%s)" % (self.name, self.opcode_name, self.type, func, render_typed_args(args))
            return INDENT + "%%%s = %s %s %s" % (self.name, self.opcode_name, self.type, render_args(self.operands))
        else:
            if self.opcode_name == "ret":
                return INDENT + "%s %s %s" % (self.opcode_name, self.operands[0].type, self.operands[0])
            if self.opcode_name == "store":
                return INDENT + "%s %s, %s" % (self.opcode_name, render_arg(self.operands[0]), render_arg(self.operands[1]))
            if self.opcode_name == "br":
                args_no = [0]
                if len(self.operands) == 3:
                    args_no = [0, 2, 1]
                return INDENT + "%s %s" % (self.opcode_name, ", ".join([render_arg(self.operands[x]) for x in args_no]))
            return INDENT + "%s %s" % (self.opcode_name, ", ".join([render_arg(x) for x in self.operands]))

    def __repr__(self):
        return self.__str__()


class PBasicBlock(object):
    def __init__(self, label):
        self.name = label
        self.insts = []

    def instructions(self):
        """Return copy of block's instruction list, for you can iterate
        over it while modifying block."""
        return self.insts[:]

    def insert(self, pos, inst):
        self.insts.insert(pos, inst)

    def append(self, inst):
        self.insts.append(inst)

    def remove(self, inst):
        self.insts.remove(inst)

    def __iter__(self):
        return iter(self.insts)

    def __len__(self):
        return len(self.insts)

    def __getitem__(self, var_name):
        for i in self:
            if i.name == var_name:
                return i


class PFunction(object):
    def __init__(self, f):
        self.name = f.name
        self.type = f.type
        self.args = [convert_arg(x) for x in f.args]
        self.is_declaration = f.is_declaration
        self.bblocks = []
        self.result_type = prim_type(str(self.type))

    def append(self, inst):
        self.bblocks.append(inst)

    def __iter__(self):
        return iter(self.bblocks)

    def __getitem__(self, bblock_label):
        for b in self:
            if b.name == bblock_label:
                return b

    def __str__(self):
        out = []
        for a in self.args:
            out.append("%s %%%s" % (a.type, a.name))
        pref = "declare" if self.is_declaration else "define"
        return "%s %s @%s(%s)" % (pref, self.result_type, self.name, ", ".join(out))



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
            out_mod.global_variables.append(PGlobalVariable(v))

        for f in mod.functions:
            out_f = PFunction(f)
            for b in f.basic_blocks:
                out_b = PBasicBlock(b.name)
                for i in b.instructions:
#                    print "# %s" % i
                    out_b.append(PInstruction.from_llvm(i))
                out_f.append(out_b)
            out_mod.append(out_f)

        return out_mod


class IRRenderer(object):
    """Render textual representation of PLLVMIR, compatible with
    rendered by native LLVM tools."""

    @staticmethod
    def render(out_mod):
        print
        for v in out_mod.global_variables:
            print v
        print

        for f in out_mod:
            if f.is_declaration:
                print str(f)
                print
                continue
            else:
                print str(f) + " {"

            last_b = None
            for b in f:
                if last_b: print
                print "%s:" % b.name
                for i in b:
                    print i
                last_b = b
            print "}"
            print


class PhiResolver(object):

    @classmethod
    def convert(cls, mod):
        for f in mod.functions:
            for b in f:
                for i in b.instructions():
                    if i.opcode_name == "phi":
                        for var, block in i.incoming_vars:
                            block = f[block]
                            mov = PInstruction(i.name, block[var].type, "mov", [PTmpVariable(var, block[var].type)])
                            block.insert(len(block) - 1, mov)
                        b.remove(i)


if __name__ == "__main__":
    with open(sys.argv[1]) as asm:
        mod = Module.from_assembly(asm)
    out_mod = IRConverter.convert(mod)
    #print "============="
    PhiResolver.convert(out_mod)
    IRRenderer.render(out_mod)
