#!/usr/bin/env python
import sys
import re


ATTR_NO_CAPTURE = "ATTR_NO_CAPTURE"

INDENT = "  "

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

    def __getitem__(self, key):
        for f in self:
            if f.name == key:
                return f
        return None


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
        self.type = None
        self.opcode_name = None
        self.operands = []

    def __str__(self):
        return "%s(%s)" % (self.opcode_name, render_typed_args(self.operands))

    def __repr__(self):
        return self.__str__()


class PInstruction(object):

    def __init__(self, *args, **kwargs):
        if args or kwargs:
            self.name, self.type, self.opcode_name, self.operands = args
        else:
            self.type = "?type"
            self.operands = []

    def defines(self):
        if self.name:
            return set([self.name])
        else:
            return set()

    defs = defines

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
        elif self.opcode_name == "bricmp":
            labels = [self.operands[2].name, self.operands[3].name]
            func = self.parent.parent
            return [func[l][0] for l in labels]
        else:
            b = self.parent
            i = b.index(self)
            if i < len(b) - 1:
                return [b[i + 1]]
            else:
                # Return first instruction of next block
                f = b.parent
                ib = f.index(b)
                return [f[ib + 1][0]]

    def __str__(self):
        if self.name:
            if self.opcode_name == "load":
                if len(self.operands) == 1:
                    return INDENT + "%%%s = %s %s" % (self.name, self.opcode_name, render_arg(self.operands[0]))
                else:
                    # Extended MEM[p + N] form
                    return INDENT + "%%%s = %s getelementptr %s" % (self.name, self.opcode_name, render_typed_args(self.operands))
            if self.opcode_name == "icmp":
                return INDENT + "%%%s = %s %s %s %s" % (self.name, self.opcode_name, self.predicate, self.operands[0].type, render_untyped_args(self.operands))
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
            if len(self.operands) == 0:
                # Not completely initialized inst, still render for parser, etc. debugging
                return INDENT + "%s ???" % self.opcode_name
            if self.opcode_name == "ret":
                return INDENT + "%s %s %s" % (self.opcode_name, self.operands[0].type, self.operands[0])
            if self.opcode_name == "store":
                return INDENT + "%s %s, %s" % (self.opcode_name, render_arg(self.operands[0]), render_arg(self.operands[1]))
            if self.opcode_name == "br":
                if len(self.operands) == 0:
                    return INDENT + "br ???"
                args_no = [0]
                if len(self.operands) == 3:
                    args_no = [0, 2, 1]
                return INDENT + "%s %s" % (self.opcode_name, ", ".join([render_arg(self.operands[x]) for x in args_no]))
            if self.opcode_name == "bricmp":
                args_no = [0, 1, 3, 2]
                return INDENT + "%s %s %s" % (self.opcode_name, self.predicate, ", ".join([render_arg(self.operands[x]) for x in args_no]))

            return INDENT + "%s %s" % (self.opcode_name, ", ".join([render_arg(x) for x in self.operands]))

    def __repr__(self):
        return self.__str__()


class PBasicBlock(object):
    def __init__(self, func, label):
        self.parent = func
        self.name = label
        self.insts = []

    def instructions(self):
        """Return copy of block's instruction list, so you can iterate
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
            self.result_type = prim_type(str(self.type))
        self.is_ref = False
        self.bblocks = []
        self.is_declaration = False
        self.does_not_throw = True
        self.vararg = False

    def append(self, inst):
        self.bblocks.append(inst)

    def index(self, block):
        return self.bblocks.index(block)

    def __iter__(self):
        return iter(self.bblocks)

    def iter_insts(self):
        """Iterate over instructions of a function, ignoring basic
        block boundaries."""
        for b in self:
            for i in b:
                yield i

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.bblocks[key]

        for b in self:
            if b.name == key:
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



class IRRenderer(object):
    """Render textual representation of PLLVMIR, compatible with
    rendered by native LLVM tools."""

    @staticmethod
    def render(mod, out=sys.stdout):
        if len(mod.global_variables):
            print >>out
            for v in mod.global_variables:
                print >>out, v
            print >>out

        last_f = None
        for f in mod:
            if f.is_declaration:
                print >>out, str(f)
                print >>out
                continue
            else:
                print >>out, str(f) + " {"

            if last_f: print
            last_b = None
            for b in f:
                if last_b: print >>out
                if b.name[0].isdigit():
                    print >>out, ";%s:" % b.name
                else:
                    print >>out, "%s:" % b.name
                for i in b:
                    print >>out, i
                last_b = b
            print >>out, "}"
            last_f = f


if __name__ == "__main__":
    with open(sys.argv[1]) as asm:
        mod = Module.from_assembly(asm)
    out_mod = IRConverter.convert(mod)
    #print "============="
    IRRenderer.render(out_mod)
