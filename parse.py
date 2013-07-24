import sys

from pllvm import *

class IRParser(object):

    def __init__(self, fileobj):
        self.f = fileobj
        self.mod = PModule()
        self.func = None
        self.block = None
        self.tmp_count = 0

    @staticmethod
    def convert_arg(arg, type=None):
        if type is None:
            type, arg = arg.split(None, 1)

        try:
            v = int(arg)
            return PConstantInt(v, type)
        except:
            pass
        if arg[0] == "%":
            return PTmpVariable(arg[1:], type)
        if arg.startswith("label "):
            label = arg.split(None, 1)[1]
            assert label[0] == "%"
            return PLabelRef(label[1:])
        1/0

    def next_tmp(self):
        t = str(self.tmp_count)
        self.tmp_count += 1
        return t

    def make_block(self, label=None):
        if not label:
            label = self.next_tmp()
        self.block = PBasicBlock(self.func, label)
        self.func.append(self.block)
        self.block.parent = self.func

    def parse(self):
        for l in self.f:
            l = l.rstrip()
            if not l:
                continue

            if l.startswith("define "):
                m = re.match(r"define (?P<type>.+?) @(?P<name>.+?)\((?P<args>.+?)\)(?P<mods>.*?) \{", l)
                assert m, "Syntax error in func definition:" + l
#                print "!", m.groupdict()
                args = [x.strip() for x in m.group("args").split(",")]
                args = [self.convert_arg(x) for x in args]
                self.func = PFunction(m.group("name"), m.group("type"), args)
                mods = m.group("mods").strip().split()
                self.func.does_not_throw = "nounwind" in mods
                self.mod.append(self.func)
                self.func.parent = self.mod
                continue

            if self.func:
                if l == "}":
                    self.block = None
                    self.func = None
                    continue

                if l[-1] == ":":
                    self.make_block(l[:-1].strip())
                    continue

                if self.block is None:
                    self.make_block()

#                print "in: ", l.strip()
                comps = [x.strip() for x in l.split("=", 1)]
                if len(comps) == 2:
                    lhs, rhs = comps
                    assert lhs[0] == "%"
                    lhs = lhs[1:]
                else:
                    lhs = None
                    rhs = comps[0]
                opcode, rhs = rhs.split(None, 1)
                inst = PInstruction()
                inst.name = lhs
                inst.opcode_name = opcode
                if opcode in ("icmp", "bricmp"):
                    pred, rhs = rhs.split(None, 1)
                    inst.predicate = pred
                type, rhs = rhs.split(None, 1)
                inst.type = type
                args = [x.strip() for x in rhs.split(",")]
                args = [self.convert_arg(x, type) for x in args]
                if opcode == "br" and len(args) == 3:
                    args = [args[0], args[2], args[1]]
                if opcode == "bricmp":
                    args = [args[0], args[1], args[3], args[2]]
                inst.operands = args
#                print "out:", str(inst).strip()
                self.block.append(inst)
                inst.parent = self.block

        return self.mod


if __name__ == "__main__":
    p = IRParser(open(sys.argv[1]))
    mod = p.parse()
    IRRenderer.render(mod)
