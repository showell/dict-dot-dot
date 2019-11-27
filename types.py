def indent(s):
    return '\n'.join(
            '    ' + line
            for line in str(s).split('\n'))

def j(*lst):
    return '\n'.join(str(item) for item in lst)

def jj(lst):
    return '\n\n'.join(str(item) for item in lst)

class Type:
    def __init__(self, ast):
        self.ast = ast

    def __str__(self):
        return j(
            'TYPE',
            self.ast)

class Binding:
    def __init__(self, ast):
        self.def_ = ast[0]
        self.expr = ast[1]

    def __str__(self):
        return j(
            self.def_,
            indent(self.expr))

class If:
    def __init__(self, ast):
        self.cond = ast[0]
        self.thenExpr = ast[1]
        self.elseExpr = ast[2]

    def __str__(self):
        return j(
            'IF',
            indent(self.cond),
            'THEN',
            indent(self.thenExpr),
            'ELSE',
            indent(self.elseExpr))

class Def:
    def __init__(self, ast):
        self.var = ast

    def __str__(self):
        return 'ASSIGN: ' + self.var

class Let:
    def __init__(self, bindings, in_):
        self.bindings = bindings
        self.in_ = in_

    def __str__(self):
        return j(
            'LET',
            indent(jj(self.bindings)),
            'IN',
            indent(str(self.in_)))

class Case:
    def __init__(self, ast):
        self.pred = ast[0]
        self.cases = ast[1]

    def __str__(self):
        return j(
            self.pred,
            indent(jj(self.cases))
            )

class CaseOf:
    def __init__(self, ast):
        self.expr = ast

    def __str__(self):
        return 'CASE OF: ' + str(self.expr)

class PatternDef:
    def __init__(self, ast):
        self.expr = ast

    def __str__(self):
        return str(self.expr)

class OneCase:
    def __init__(self, ast):
        self.patternDef = ast[0]
        self.body = ast[1]

    def __str__(self):
        return '\n'.join([
            'PATTERN',
            indent(self.patternDef),
            'BODY',
            indent(self.body)
            ])


