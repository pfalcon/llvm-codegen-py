ADD = 1

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
[(ADD, CONST, CONST),
 ("mov a, #{1}", "add a, #{2}")],
[(ADD, NAME, NAME),
 ("mov a, {1}", "add a, {2}")],
[{"pat": (ADD, NAME, CONST), "commute": True},
 ("mov a, {1}", "add a, #{2}")],
[(ADD, ANY, ANY),
 (EVAL(0), "mov @r1, a", "inc r1", EVAL(1), "pop r2", "add a, r2")],

# Fallback nodes
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
            for node, subpat in zip(tree[1:], pattern[1:]):
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
            if not isinstance(tree, pattern):
                return False
        else:
                raise NotImplementedError

        return True

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
            if self.match_tree_pattern(node, pat):
                return node, xlat_pat, self.subtree_capture
            elif props.get("commute") and istree(node, size=3):
                # Applicable only to 2-arg operations
                node_c = (node[0], node[2], node[1])
                if self.match_tree_pattern(node_c, pat):
                    return node_c, xlat_pat, self.subtree_capture

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
                self._gen(subtrees[inst_pattern.num])
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
