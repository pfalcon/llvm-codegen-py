from pllvm import *
from graph import *


class InterferenceGraph(UngraphEdgeList):

    def __init__(self, func, liveness):
        super(self.__class__, self).__init__()
        for inst in func.iter_insts():
            live_out = liveness.live_out(inst)
            # What we could do is to add interference edge between
            # each pair of variables in live_out, but that would be
            # O(n^2) on average. Instead, we can add interference
            # between newly defined variables and already live. This
            # will be O(n) on average. After iterating over all
            # instructions, the end result will be the same, as any
            # var in live_out is defined somewhere.
            #
            # Additionally:
            # "What if a newly defined temporary is not live just after its definition? This
            # would be the case if a variable is defined but never used. It would seem that
            # there's no need to put it in a register at all; thus it would not interfere with any
            # other temporaries. But if the defining instruction is going to execute (perhaps
            # it is necessary for some other side effect of the instruction), then it will write to
            # some register, and that register had better not contain any other live variable.
            # Thus, zero-length live ranges do interfere with any live ranges that overlap
            # them." Appel-2ed 10.2 p.217

            for d in inst.defs():
                for colive in live_out:
                    if d != colive:
                        self.add_edge(d, colive)
