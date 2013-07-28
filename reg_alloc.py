from pllvm import *
from graph import *
from liveness import *
from interference import *
from graph_color import *


class RegAlloc(object):

    def __init__(self, func, num_regs):
        self.num_regs = num_regs
        self.func = func
        self.liveness = Liveness(func)
        interf = InterferenceGraph(func, self.liveness)
        # Use graph implementation more optimal for coloring algo
        self.interf = UngraphAdjList()
        self.interf.from_graph(interf)

    def alloc(self):
        regcolor = RegColoring(self.interf, self.num_regs)
        regcolor.simplify()
        regcolor.select()
        self.reg_map = regcolor.get_coloring()
        return self.reg_map

    def reg(self, var):
        return "R%d" % self.reg_map[var]

    def rewrite_regs(self):
        for i in self.func.iter_insts():
            if i.name:
                i.name = self.reg(i.name)
            for a in i.operands:
                if isinstance(a, PTmpVariable):
                    a.name = self.reg(a.name)
        # Remove void moves
        for i in list(self.func.iter_insts()):
            if i.opcode_name == "mov" and isinstance(i.operands[0], PTmpVariable):
                if i.name == i.operands[0].name:
                    i.parent.remove(i)
