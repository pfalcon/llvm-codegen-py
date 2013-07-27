from pprint import pprint


ARG_REGS = ["R7", "R6", "R5", "R4"]
RES_REGS = ["R7", "R6", "R5", "R4"]
WORK_REGS = set(["R7", "R6", "R5", "R4", "R3", "R2"])
REG_WIDTH = 8


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
    def from_list(cls, IR):
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





def get_width(type):
    assert type[0] == "i"
    if type[-1] == "*":
        type = type[:-1]
    return int(type[1:])

def get_size(type):
    return get_width(type) / REG_WIDTH

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
#            print "*", i
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
    ranges = {}
    for no, i in enumerate(IR):
        if i.OPCODE == "define":
            for a in i.ARGS:
                ranges[a[1]] = {"type": a[0], "def": no, "use": []}
        elif i.OPCODE == "global":
            pass
        else:
            if i.DEST:
                ranges[i.DEST] = {"type": i.TYPE, "def": no, "use": []}
            for a in i.ARGS:
                if a[0] == "%":
                    ranges[a]["use"].append(no)

    return ranges

def assign_in_out_regs(IR, ranges):
    in_regs = ARG_REGS[:]
    for no, i in enumerate(IR):
        if i.OPCODE == "define":
            for a in i.ARGS:
                size = get_width(a[0]) / REG_WIDTH
                regs = in_regs[0:size]
                in_regs = in_regs[size:]
                ranges[a[1]]["reg"] = regs
        elif i.OPCODE == "ret":
            size = get_width(i.TYPE) / REG_WIDTH
            ranges[i.ARGS[0]]["reg"] = RES_REGS[0:size]

    return ranges

def get_live_range(ranges, var):
    if len(ranges[var]["use"]) == 0:
        ## No uses? Dead var
        #return None
        return (ranges[var]["def"], ranges[var]["def"])
    return (ranges[var]["def"], ranges[var]["use"][-1])

def range_intersects(r1, r2):
    if r1[0] > r2[0]:
        # Make sure that r1 starts earlier
        r2, r1 = r1, r2
#    print "*", r1, r2

#    if r1[1] >= r2[0]:
    if r1[1] > r2[0]:
        return True
    return False

def intersect_live_ranges(ranges, var):
    var_r = get_live_range(ranges, var)
    if not var_r:
        return None
    intersecting_vars = []
    for v, info in ranges.iteritems():
        if v == var: continue
        lr = get_live_range(ranges, v)
        if range_intersects(var_r, lr):
            intersecting_vars.append(v)
    return intersecting_vars

def assign_regs(IR, ranges):
    for var, info in ranges.iteritems():
        if "reg" in info: continue
        inters = intersect_live_ranges(ranges, var)
        print "covars:", var, inters
        all_regs = set()
        for v in inters:
            all_regs |= set(ranges[v]["reg"])
        print all_regs
        free_regs = WORK_REGS - all_regs
        print free_regs
        regs = []
        for i in xrange(get_size(ranges[var]["type"])):
            regs.append(free_regs.pop())
        ranges[var]["reg"] = regs


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

def split_value_op(asm, i, size, first_op, next_ops):
    for b in xrange(size):
        asm.append(("mov", "a", i.ARGS[0][b]))
        if b == 0:
            asm.append((first_op, "a", i.ARGS[1][b]))
        else:
            asm.append((next_ops, "a", i.ARGS[1][b]))
        asm.append(("mov", i.DEST[b], "a"))


def gen_asm(IR):
    asm = []
    for no, i in enumerate(IR):
        size = get_width(i.TYPE) / REG_WIDTH
        if i.OPCODE == "define":
            pass
        elif i.OPCODE == "ret":
            asm.append("ret")
        elif i.OPCODE == "add":
            split_value_op(asm, i, size, "add", "addc")

#            if i.DEST in i.ARGS:
#                asm.append(("add", another_reg(i.DEST, i.ARGS), i.DEST))
#            else:
#                1/0
        elif i.OPCODE == "load":
            for b in xrange(size):
                asm.append(("mov", i.DEST[b], i.ARGS[0] + "+%d" % b))
        elif i.OPCODE == "global":
            asm.append((i.DEST, "data", i.ARGS[0]))
        else:
            print i.OPCODE
            1/0
    return asm

if __name__ == "__main__":
    IR = [
    ("@val", "global", "i16", "0"),
    ("@func", "define", "i32", ("i16", "%a"), ("i16", "%b")),
    ("%2", "load", "i16*", "@val"),
    ("%1", "add", "i16", "%b", "%a"),
    ("", "ret", "i16", "%1"),
    ]

    IR = IRStream.from_list(IR)
    IR.dump()

    print "======"
    ranges = collect_live_ranges(IR)
    assign_in_out_regs(IR, ranges)
    print "Assigned in/out regs"
    pprint(ranges)
    print "Assigned remaining regs"
    assign_regs(IR, ranges)
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
