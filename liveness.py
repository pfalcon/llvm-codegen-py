#!/usr/bin/env python
import sys
import re
from copy import copy

from llvm2py import *


class Liveness(object):

    @classmethod
    def run(cls, func):
        live_in = {}
        live_out = {}
        for b in func:
            for i in b.instructions():
                live_in[i] = set()
                live_out[i] = set()

        changed = True
        iter = 1
        while changed:
            changed = False
            print "iter", iter
            iter += 1
            for b in func:
                for i in b.instructions():
                    print "Analyzing", i, "| def:", i.defines(), "| use:", i.uses()
                    new_in = copy(live_in[i])
                    new_out = copy(live_out[i])
                    new_in = i.uses() | (new_out - i.defines())
                    new_out = set()
                    print "Succ:", i.succ()
                    for s in i.succ():
                        new_out |= live_in[s]
                    if new_in != live_in[i] or new_out != live_out[i]:
                        changed = True
                        live_in[i] = new_in
                        live_out[i] = new_out
        return live_out


if __name__ == "__main__":
    with open(sys.argv[1]) as asm:
        mod = Module.from_assembly(asm)
    out_mod = IRConverter.convert(mod)
    #print "============="
    Liveness.run(out_mod)

#    IRRenderer.render(out_mod)
