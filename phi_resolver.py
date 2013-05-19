#!/usr/bin/env python
import sys
import re

from llvm2py import *


class PhiResolver(object):

    @classmethod
    def convert(cls, mod):
        for f in mod.functions:
            for b in f:
                for i in b.instructions():
                    if i.opcode_name == "phi":
                        for var, label in i.incoming_vars:
                            block = f[label]
                            mov = PInstruction(i.name, i.type, "mov", [var])
                            # Insert move before the last instruction of block,
                            # which is got to be control transfer instruction.
                            block.insert(len(block) - 1, mov)
                        b.remove(i)


if __name__ == "__main__":
    with open(sys.argv[1]) as asm:
        mod = Module.from_assembly(asm)
    out_mod = IRConverter.convert(mod)
    #print "============="
    PhiResolver.convert(out_mod)
    IRRenderer.render(out_mod)
