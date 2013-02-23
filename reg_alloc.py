from pprint import pprint


class IREntry:
    """Container for intermediate representation(s). This is needed
    so there's static node's id() value."""

    def __init__(self, data):
        data = list(data)
        self.data = data
        self.DEST = data[0]
        self.OPCODE = data[1]
        self.TYPE = data[2]
        self.ARGS = data[3:]

    def __repr__(self):
        data = (self.DEST, self.OPCODE, self.TYPE) + tuple(self.ARGS)
        return repr(data)

class IRStream:

    def __init__(self, IR):
        self.IR = IR

    @classmethod
    def from_bare_list(cls, IR):
        IR = [IREntry(x) for x in IR]
        return cls(IR)

    def dump(self):
        pprint(self.IR)

    def __iter__(self):
        return iter(self.IR)

    def find_by_opcode(self, opcode):
        for i in self.IR:
            if i.OPCODE == opcode:
                yield i

    def rewrite_reg(self, old_reg, new_reg):
        IR2 = []
        for i in self.IR:
            if i.DEST == old_reg:
                i.DEST = new_reg
            args = []
            for a in i.ARGS:
                if a == old_reg:
                    a = new_reg
                args.append(a)
            i.ARGS = args
            IR2.append(i)
        return IRStream(IR2)



ARG_REGS = ["R7", "R6", "R5", "R4"]
RES_REGS = ["R7", "R6", "R5", "R4"]

IR = [
    ("@func", "define", "i32", ("i16", "%a"), ("i16", "%b")),
    ("%1", "add", "i16", "%b", "%a"),
    ("", "ret", "i16", "%1"),
]

IR = IRStream.from_bare_list(IR)

IR.dump()

def insert_after(l, el, new_el):
    i = l.index(el)
    l.insert(i + 1, el)

def add_cc_reg_copy(IR):
    IR2 = []
    in_regs = ARG_REGS[:]
    for i in IR:
        if i.OPCODE == "define":
            for a in i.ARGS:
                IR2.append((in_regs.pop(0), "copy", a[1]))
        elif i.OPCODE == "ret":
            IR2.append((RES_REGS[0], "copy", i.ARGS[1]))
#                print i
            i.ARGS[1] = RES_REGS[0]
            print "*", i
            IR2.append(i)
        else:
            IR2.append(i)
    return IR2


def rewrite_return(IR):
    for i in IR.find_by_opcode("ret"):
        IR = IR.rewrite_reg("%1", "R15")

    return IR

def rewrite_in_args(IR):
    # unfinished
    for i in IR.find_by_opcode("define"):
        print i
#        IR = IR.rewrite_reg("%1", "R15")

    return IR

def collect_live_ranges(IR):
    in_regs = ARG_REGS[:]
    ranges = {}
    for no, i in enumerate(IR):
        if i.OPCODE == "define":
            for a in i.ARGS:
                ranges[a[1]] = {"type": a[0], "def": no, "use": [], "reg": in_regs.pop(0)}
        else:
            if i.DEST:
                ranges[i.DEST] = {"type": i.TYPE, "def": no, "use": []}
            for a in i.ARGS:
                ranges[a]["use"].append(no)
            if i.OPCODE == "ret":
                ranges[a]["reg"] = RES_REGS[0]

    return ranges

def check_regs_assigned(ranges):
    for var, info in ranges.iteritems():
        assert "reg" in info

def rewrite_per_ranges(IR, ranges):
    for var, props in ranges.iteritems():
        print var, props
        IR = IR.rewrite_reg(var, props["reg"])
    return IR

def other_regs(reg, reg_list):
    return filter(lambda x: x != reg, reg_list)

def another_reg(reg, reg_list):
    regs = other_regs(reg, reg_list)
    assert len(regs) == 1
    return regs[0]

def gen_asm(IR):
    asm = []
    for no, i in enumerate(IR):
        if i.OPCODE == "define":
            pass
        elif i.OPCODE == "ret":
            asm.append("ret")
        elif i.OPCODE == "add":
            if i.DEST in i.ARGS:
                asm.append(("add", another_reg(i.DEST, i.ARGS), i.DEST))
            else:
                1/0
        else:
            1/0
    return asm


print "======"
ranges = collect_live_ranges(IR)
pprint(ranges)
check_regs_assigned(ranges)
IR2 = rewrite_per_ranges(IR, ranges)
IR2.dump()
pprint(gen_asm(IR2))

#IR2 = rewrite_return(IR)
#IR2.dump()
#IR3 = rewrite_return(IR2)
#IR3.dump()
#pprint(rewrite_reg(IR, "%1", "R15"))
