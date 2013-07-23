#!/usr/bin/env python
import sys
import re
from copy import copy

from llvm2py import *


class Liveness(object):

    def __init__(self, func):
        self.live_in = {}
        self.live_out = {}
        for b in func:
            for i in b.instructions():
                self.live_in[i] = set()
                self.live_out[i] = set()

        changed = True
        iter = 1
        while changed:
            changed = False
            print "iter", iter
            iter += 1
            for b in func:
                for i in b.instructions():
                    print "Analyzing", i, "| def:", i.defines(), "| use:", i.uses()
                    new_in = copy(self.live_in[i])
                    new_out = copy(self.live_out[i])
                    new_in = i.uses() | (new_out - i.defines())
                    new_out = set()
                    print "Succ:", i.succ()
                    for s in i.succ():
                        new_out |= self.live_in[s]
                    if new_in != self.live_in[i] or new_out != self.live_out[i]:
                        changed = True
                        self.live_in[i] = new_in
                        self.live_out[i] = new_out

    def live_out_map(self):
        return self.live_out


if __name__ == "__main__":
    with open(sys.argv[1]) as asm:
        mod = Module.from_assembly(asm)
    out_mod = IRConverter.convert(mod)
    #print "============="
    Liveness(out_mod[0])

#    IRRenderer.render(out_mod)
