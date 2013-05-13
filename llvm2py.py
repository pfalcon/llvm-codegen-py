#!/usr/bin/env python
import sys

from llvm.core import *
import llvm


PRED_MAP = {ICMP_EQ: "eq"}


def prim_type(type):
    return type.split(" ", 1)[0]

def render_arg(arg):
    if isinstance(arg, PConstantInt):
        return str(arg)
    else:
        return "%s %s" % (arg.type, arg)

def render_args(args):
    return ", ".join([render_arg(x) for x in args])

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
        self.type = v.type
        self.is_declaration = v.is_declaration

    def __str__(self):
        return "@%s = common global %s 0" % (self.name, str(self.type)[:-1])

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

def convert_arg(a):
    if isinstance(a, Argument):
        return PArgument(a.name, a.type)
    if isinstance(a, GlobalVariable):
        return PGlobalVariableRef(a.name, a.type)
    if isinstance(a, ConstantInt):
        return PConstantInt(a.z_ext_value, a.type)
    if isinstance(a, BasicBlock):
        return PLabelRef(a.name)
    if isinstance(a, Instruction):
        # Result of instruction is temporary
        return PTmpVariable(a.name, a.type)

    raise NotImplementedError(a, type(a))



class PInstruction(object):

    def __init__(self, i):
#        print i.name, i.type, i.opcode_name, i.operands
        self.name = i.name
        self.type = i.type
        self.opcode_name = i.opcode_name
        self.predicate = None
        if hasattr(i, "predicate"):
            self.predicate = i.predicate
        self.operands = [convert_arg(x) for x in i.operands]
        if i.opcode_name == "phi":
            self.incoming_vars = [(o.name, o.basic_block.name) for o in i.operands]

    def __str__(self):
        if self.name:
            if self.opcode_name == "load":
                return "   %%%s = %s %s" % (self.name, self.opcode_name, render_arg(self.operands[0]))
            if self.opcode_name == "icmp":
                return "   %%%s = %s %s %s" % (self.name, self.opcode_name, PRED_MAP[self.predicate], render_args(self.operands))
            if self.opcode_name == "phi":
                args = ", ".join(["[ %%%s, %%%s ]" % x for x in self.incoming_vars])
                return "   %%%s = %s %s %s" % (self.name, self.opcode_name, self.type, args)
            opers = ", ".join([str(x) for x in self.operands])
            return "   %%%s = %s %s %s" % (self.name, self.opcode_name, self.type, opers)
        else:
            if self.opcode_name == "ret":
                return "   %s %s %s" % (self.opcode_name, self.operands[0].type, self.operands[0])
            if self.opcode_name == "store":
                return "   %s %s, %s" % (self.opcode_name, render_arg(self.operands[0]), render_arg(self.operands[1]))
            if self.opcode_name == "br":
                args_no = [0]
                if len(self.operands) == 3:
                    args_no = [0, 2, 1]
                return "   %s %s" % (self.opcode_name, ", ".join([render_arg(self.operands[x]) for x in args_no]))
            return "   %s %s" % (self.opcode_name, ", ".join([render_arg(x) for x in self.operands]))

    def __repr__(self):
        return self.__str__()


class PBasicBlock(object):
    def __init__(self, label):
        self.label = label
        self.insts = []

    def append(self, inst):
        self.insts.append(inst)

    def __iter__(self):
        return iter(self.insts)

class PFunction(object):
    def __init__(self, f):
        self.name = f.name
        self.type = f.type
        self.args = [convert_arg(x) for x in f.args]
        self.is_declaration = f.is_declaration
        self.bblocks = []

    def append(self, inst):
        self.bblocks.append(inst)

    def __iter__(self):
        return iter(self.bblocks)

    def __str__(self):
        out = []
        for a in self.args:
            out.append("%s %%%s" % (a.type, a.name))
        pref = "declare" if self.is_declaration else "define"
        return "%s %s @%s(%s)" % (pref, prim_type(str(self.type)), self.name, ", ".join(out))



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
#                   print "BB name:", b.name
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
#                            print "# %s" % i
                    out_b.append(PInstruction(i))
                out_f.append(out_b)
            out_mod.append(out_f)

        return out_mod


class IRRenderer(object):
    """Render textual representation of PLLVMIR, compatible with
    rendered by native LLVM tools."""

    @staticmethod
    def render(out_mod):
        for f in out_mod:
            if f.is_declaration:
                print str(f)
                print

        print
        for v in out_mod.global_variables:
            print v
        print

        for f in out_mod:
            if f.is_declaration:
                continue
            else:
                print str(f) + " {"

            last_b = None
            for b in f:
                if last_b: print
                print "%s:" % b.label
                for i in b:
                    print i
                last_b = b
            print "}"


if __name__ == "__main__":
    with open(sys.argv[1]) as asm:
        mod = Module.from_assembly(asm)
    out_mod = IRConverter.convert(mod)
    #print "============="
    IRRenderer.render(out_mod)
