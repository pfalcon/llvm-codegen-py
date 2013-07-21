#!/usr/bin/env python
import sys
import re

from llvm.core import *
import llvm


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
        self.type = v.type
        self.type_str = str(v.type)[:-1]
        self.is_declaration = v.is_declaration
        self.initializer = convert_arg(v.initializer)
        self.linkage = LINKAGE_MAP[v.linkage]
        self.alignment = v.alignment
        self.global_constant = v.global_constant
        self.unnamed_addr = "unnamed_addr" in str(v)

    def __str__(self):
        flags = []
        if self.unnamed_addr:
            flags.append("unnamed_addr")
        if self.global_constant:
            flags.append("constant")
        else:
            flags.append("global")
        flags = " ".join(flags)
        s = "@%s = %s %s %s %s" % ( self.name, self.linkage, flags, self.type_str, self.initializer)
        if self.alignment:
            s += ", align %d" % self.alignment
        return s

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



class PInstruction(object):

    def __init__(self, *args, **kwargs):
        if args or kwargs:
            self.name, self.type, self.opcode_name, self.operands = args

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

    def defines(self):
        if self.name:
            return set([self.name])
        else:
            return set()

    def uses(self):
        uses = set()
        for op in self.operands:
            if isinstance(op, (PArgument, PTmpVariable)):
                uses.add(op.name)
        return uses

    def succ(self):
        if self.opcode_name == "ret":
            return []
        elif self.opcode_name == "br":
            if len(self.operands) == 3:
                labels = [self.operands[1].name, self.operands[2].name]
            else:
                labels = [self.operands[0].name]
            func = self.parent.parent
            return [func[l][0] for l in labels]
        else:
            b = self.parent
            i = b.index(self)
            return [b[i + 1]]

    def __str__(self):
        if self.name:
            if self.opcode_name == "load":
                return INDENT + "%%%s = %s %s" % (self.name, self.opcode_name, render_arg(self.operands[0]))
            if self.opcode_name == "icmp":
                return INDENT + "%%%s = %s %s %s" % (self.name, self.opcode_name, self.predicate, render_args(self.operands))
            if self.opcode_name == "phi":
                args = ", ".join(["[ %s, %%%s ]" % x for x in self.incoming_vars])
                return INDENT + "%%%s = %s %s %s" % (self.name, self.opcode_name, self.type, args)
            if self.opcode_name == "call":
                func = self.operands[-1]
                args = self.operands[:-1]
                if func.vararg:
                    return INDENT + "%%%s = %s %s %s(%s)" % (self.name, self.opcode_name, func.type, func, render_typed_args(args))
                else:
                    return INDENT + "%%%s = %s %s %s(%s)" % (self.name, self.opcode_name, self.type, func, render_typed_args(args))
            if self.opcode_name == "getelementptr":
                op = "getelementptr"
                if self.inbounds:
                    op += " inbounds"
                return INDENT + "%%%s = %s %s" % (self.name, op, render_typed_args( self.operands))
            return INDENT + "%%%s = %s %s %s" % (self.name, self.opcode_name, self.type, render_untyped_args(self.operands))
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
    def __init__(self, func, label):
        self.parent = func
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

    def index(self, inst):
        return self.insts.index(inst)

    def __iter__(self):
        return iter(self.insts)

    def __len__(self):
        return len(self.insts)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.insts[key]
        else:
            for i in self:
                if i.name == inst:
                    return i


class PFunction(object):
    def __init__(self, *args, **kwargs):
        if args or kwargs:
            self.name, self.type, self.args = args

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
        if self.is_ref:
            return "@" + self.name
        flags = ""
        if self.does_not_throw:
            flags += " nounwind"
        if self.is_declaration:
#            return "declare %s @%s(%s)" % (self.result_type, self.name, render_types(self.args))
            # This handles stuff like varargs
            rest, argt = str(self.type.pointee).split(" ", 1)
            return "declare %s @%s%s%s" % (self.result_type, self.name, argt, flags)
        else:
            return "define %s @%s(%s)%s" % (self.result_type, self.name, render_typed_args(self.args), flags)



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
            out_mod.global_variables.append(PGlobalVariable(v))

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


class IRRenderer(object):
    """Render textual representation of PLLVMIR, compatible with
    rendered by native LLVM tools."""

    @staticmethod
    def render(mod):
        print
        for v in mod.global_variables:
            print v
        print

        last_f = None
        for f in mod:
            if f.is_declaration:
                print str(f)
                print
                continue
            else:
                print str(f) + " {"

            if last_f: print
            last_b = None
            for b in f:
                if last_b: print
                if b.name[0].isdigit():
                    print ";%s:" % b.name
                else:
                    print "%s:" % b.name
                for i in b:
                    print i
                last_b = b
            print "}"
            last_f = f


if __name__ == "__main__":
    with open(sys.argv[1]) as asm:
        mod = Module.from_assembly(asm)
    out_mod = IRConverter.convert(mod)
    #print "============="
    IRRenderer.render(out_mod)
