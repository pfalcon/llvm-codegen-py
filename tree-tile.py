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

patterns = [
#[(ADD, CONST, CONST), ("mov a, #{1}", "add a, #{2}")],
[(ADD, NAME, CONST), ("mov a, {1}", "add a, #{2}")],
[(ADD, ANY, ANY), (EVAL(0), "mov @r1, a", "inc r1", EVAL(1), "pop r2", "add a, r2")],

# Fallback nodes
[CONST, ("mov a, #{0}",)],
[NAME, ("mov a, {0}",)],
]

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
        for p in patterns:
            self.subtree_capture = []
            if self.match_tree_pattern(node, p[0]):
                return p, self.subtree_capture
        return None, None


class CodeGen(object):

    def __init__(self, patterns):
        self.patterns = patterns
        self.tiler = TreeTiler()

    def gen(self, node):
        pat, subtrees = self.tiler.match_node(node, self.patterns)
        if pat is None:
            assert False, "Cannot translate node: %s" % node
        for inst_pattern in pat[1]:
            if isinstance(inst_pattern, EVAL):
                self.gen(subtrees[inst_pattern.num])
            else:
                if type(node) is not type(()):
                    node = (node,)
                print inst_pattern.format(*node)

cg = CodeGen(patterns)

cg.gen(tree2)
