ADD = "ADD"
MEMI = "MEMI"
MEMX = "MEMX"
STORE = "STORE"

class ANY:
    "Wildcard match"
    pass


class CONST(object):

    def __init__(self, val):
        self.val = val

    def __str__(self):
        return str(self.val)

    def __repr__(self):
        return "CONST(%s)" % self.val


class NAME(object):

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return str(self.name)

class EVAL(object):

    def __init__(self, num):
        self.num = num


tree = (ADD, CONST(1), CONST(2))
tree2 = (ADD, NAME("foo"), CONST(2))
tree3 = (ADD, CONST(2), NAME("foo"))

patterns = [
[{"pat": (ADD, ANY, CONST), "commute": True},
 (EVAL(1), "add a, #{2}")],
[{"pat": (ADD, ANY, NAME), "commute": True},
 (EVAL(1), "add a, {2}")],

[(ADD, ANY, ANY),
 (EVAL(1), "push A", EVAL(2), "pop R2", "add a, r2")],

[(STORE, NAME, ANY), (EVAL(2), "mov {1}, a")],

# Fallback nodes
[{"pat": (MEMI, CONST), "pred": lambda n: n[1].val < 128},
 ("mov a,{1}", )],
[{"pat": (MEMI, CONST), "pred": lambda n: n[1].val >= 128},
 ("mov r0, #{1}", "mov a,@r0")],
[(MEMX, CONST), ("mov dptr, #{1}", "movx a,@dptr")],

[(MEMI, NAME), ("mov r0, {1}", "mov a,@r0")],
[(MEMX, NAME), ("mov DPL, {1}", "mov DPH, {1}+1", "movx a, @dptr")],

[CONST, ("mov a, #{0}",)],
[NAME, ("mov a, {0}",)],
]

def istree(tree, size=0):
    if type(tree) is not type(()):
        return False
    if size and len(tree) != size:
        return False
    return True

class TreeTiler(object):

    def __init__(self):
        self.subtree_capture = []

    def match_tree_pattern(self, tree, pattern):
        if type(tree) is type(()) and type(pattern) is type(()):
#            print "matching trees:", tree, pattern
            if len(tree) != len(pattern):
                return False
            for node, subpat in zip(tree, pattern):
                if not self.match_tree_pattern(node, subpat):
                    return False
            return True

        # At least one arg is scalar

        if type(pattern) == type(()):
            # Cannot match scalar against tree
            return False

#        print "matching scalars:", tree, pattern
        if pattern is ANY:
            self.subtree_capture.append(tree)
            return True

        if tree == pattern:
            return True

        if type(pattern) is type:
            if isinstance(tree, pattern):
                return True

        return False

    def match_node(self, node, patterns):
        """
        Returns:
            matched node (possibly transformed for commutativity, etc.)
            pattern entry that matched
            captured subtree of a pattern
        """
        for xlat_pat in patterns:
            self.subtree_capture = []
            pat = xlat_pat[0]
            props = {}
            print pat
            if type(pat) is type({}):
                props = pat
                pat = props["pat"]
            match = None
            if self.match_tree_pattern(node, pat):
                match = node, xlat_pat, self.subtree_capture
            elif props.get("commute") and istree(node, size=3):
                # Applicable only to 2-arg operations
                node_c = (node[0], node[2], node[1])
                self.subtree_capture = []
                if self.match_tree_pattern(node_c, pat):
                    match = node_c, xlat_pat, self.subtree_capture
            if match:
                if not "pred" in props:
                    return match
                if props["pred"](match[0]):
                    return match

        return None, None, None


class CodeGen(object):

    def __init__(self, patterns):
        self.patterns = patterns
        self.tiler = TreeTiler()
        self.out = None

    def _gen(self, node):
        node, pat, subtrees = self.tiler.match_node(node, self.patterns)
        if pat is None:
            assert False, "Cannot translate node: %s" % node
        for inst_pattern in pat[1]:
            if isinstance(inst_pattern, EVAL):
                if isinstance(inst_pattern.num, type([])):
                    arg = node
                    for i in inst_pattern.num:
                        arg = arg[i]
                    self._gen(arg)
                else:
                    # Numbering is 1-based for childs
#                    self._gen(subtrees[inst_pattern.num - 1])
                    self._gen(node[inst_pattern.num])
            else:
                if type(node) is not type(()):
                    node = (node,)
                self.out.append(inst_pattern.format(*node))

    def gen(self, node):
        self.out = []
        self._gen(node)
        return self.out


if __name__ == "__main__":
    cg = CodeGen(patterns)
    for i in cg.gen(tree3):
        print i
