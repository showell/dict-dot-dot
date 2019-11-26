import types

"""
parser : state -> state
capture : state -> (state, ast)
"""

def tokenChar(s, i):
    if i >= len(s):
        return False

    c = s[i]

    if c.isspace():
        return False

    if c in '(),[]=':
        return False

    return True

def bigSkip(state, *fns):
    for fn in fns:
        state = fn(state)
        if state is None: return
    return state

def capture(f, parse):
    def f_(state):
        (s, iOrig) = state
        newState = parse(state)
        if newState is None:
            return None
        (s, i) = newState
        subState = (s[iOrig:i], 0)
        _, ast = f(subState)
        if ast is None:
            return None

        return (newState, ast)

    return f_

def skip(parse):
    def f(state):
        newState = parse(state)
        if newState is None:
            return
        return (newState, Skip())

    return f

def captureMany(capture, state):
    asts = []
    while True:
        res = capture(state)
        if res is None: break
        state, ast = res
        asts.append(ast)

    asts = [a for a in asts if type(a) != Skip]
    return (state, asts)

def capturePunt(state):
    (s, i) = state
    newState = ('', 0)
    ast = 'unparsed: ' + s[i:]
    return (newState, ast)

class Skip:
    pass

def captureOneOf(state, *fns):
    for fn in fns:
        res = fn(state)
        if res is not None:
            return res

def peek(state, kw):
    (s, i) = state
    return s[i:i+len(kw)] == kw

def peekOneOf(state, *kws):
    return any(peek(state, kw) for kw in kws)

def advanceState(state, n):
    (s, i) = state
    return (s, i + n)

def optional(f):
    def f_(state, *args):
        origState = state
        res = f(state, *args)
        if res is None:
            return origState
        return res

    return f_

def spaceOptional(state):
    (s, i) = state
    while i < len(s) and s[i].isspace():
        i += 1

    return (s, i)

def spaceRequired(state):
    (s, i) = state

    iOrig = i

    while i < len(s) and s[i].isspace():
        i += 1

    if i == iOrig:
        return

    return (s, i)

def parseUntil(kw, state):
    (s, i) = state
    n = len(kw)
    while i < len(s):
        if s[i:i+n] == kw:
            return (s, i)
        i += 1

def pUntil(kw):
    return lambda state: parseUntil(kw, state)

def parseKeyword(kw, state):
    (s, i) = state
    if s[i : i + len(kw)] == kw:
        i += len(kw)
        return (s, i)

def pKeyword(kw):
    return lambda state: parseKeyword(kw, state)

def token(state):
    (s, i) = state

    if not tokenChar(s, i):
        return

    while tokenChar(s, i):
        i += 1
    return (s, i)

def readline(s, i):
    while i < len(s) and s[i] != '\n':
        i += 1

    # skip over blank lines
    while i < len(s) and s[i].isspace():
        i += 1
    return i

def indentLevel(s, i):
    if s[i].isspace():
        raise Exception('expected nonspace')
    i -= 1
    n = 0
    while i >= 0 and s[i] != '\n':
        n += 1
        if not s[i].isspace():
            raise Exception('expected space')
        i -= 1

    return n


def parseBlock(state):
    (s, i) = state
    level = indentLevel(s, i)

    i = readline(s, i)

    while i < len(s) and indentLevel(s, i) > level:
        i = readline(s, i)

    return (s, i)

def parseType(state):
    if peek(state, 'type'):
        return parseBlock(state)

captureType = capture(capturePunt, parseType)

def parseModule(state):
    state = bigSkip(
            state,
            pKeyword('module'),
            spaceRequired,
            token,
            spaceRequired,
            pKeyword('exposing'),
            spaceOptional,
            pKeyword('('),
            spaceOptional,
            )

    if state is None: return

    while True:
        state = bigSkip(
                state,
                token,
                optional(pKeyword('(..)')),
                spaceOptional
                )
        if state is None: return

        if peek(state, ')'):
            state = advanceState(state, 1)
            break

        state = bigSkip(
                state,
                pKeyword(','),
                spaceOptional
                )
        if state is None: return

    state = bigSkip(state, spaceOptional)

    return state

def parseDocs(state):
    state = bigSkip(
            state,
            pKeyword('{-| '),
            pUntil('-}'),
            pKeyword('-}'),
            spaceRequired
            )
    return state

def parseLineComment(state):
    return bigSkip(
            state,
            pKeyword('--'),
            pUntil('\n'),
            spaceOptional,
            )

def parseImport(state):
    return bigSkip(
            state,
            pKeyword('import'),
            pUntil('\n'),
            spaceOptional,
            )

def parseDef(state):
    return bigSkip(
            state,
            token,
            spaceOptional,
            parseParams,
            spaceOptional,
            pKeyword('='),
            spaceOptional,
            )

def captureLet(state):
    state = bigSkip(
            state,
            spaceOptional,
            pKeyword('let'),
            spaceOptional
            )
    if not state:
        return

    state, bindings = capture(captureLetBindings, parseBlock)(state)

    state = bigSkip(
            state,
            spaceOptional,
            pKeyword("in"),
            spaceOptional,
            )

    if not state:
        return

    state, expr = capture(capturePunt, parseBlock)(state)
    ast = types.Let(bindings=bindings, in_=expr)
    return state, ast

def captureLetBindings(state):
    (s, i) = state
    res = captureMany(captureBinding, state)
    if res is None:
        printState(state)
        raise Exception('could not get binding')
    return res

def captureExpr(state):
    return captureOneOf(
            state,
            captureLet,
            captureIf,
            capturePunt,
            )

def captureIf(state):
    state = bigSkip(
            state,
            spaceOptional,
            pKeyword('if'),
            spaceRequired
            )
    if state is None:
        return

    def parseCond(state):
        return bigSkip(
                state,
                pUntil('then')
                )

    res = capture(captureExpr, parseCond)(state)
    if res is None:
        return

    state, cond = res
    ast = 'if: ' + str(cond)
    return (state, ast)

def captureBindingBlock(state):
    newState = parseDef(state)

    if newState is None:
        raise Exception('bad definition')
    return captureExpr(newState)

def parseBinding(state):
    origState = state
    newState = parseDef(state)
    if newState is None:
        return
    return parseBlock(origState)

captureBinding = capture(captureBindingBlock, parseBinding)

def parseTuple(state):
    return bigSkip(
            state,
            spaceOptional,
            pKeyword('('),
            pUntil(')'),
            pKeyword(')'),
            spaceOptional
            )

def parseParam(state):
    return bigSkip(
            state,
            token,
            spaceOptional
            )

def parseParams(state):
    while True:
        res = captureOneOf(
                state,
                skip(parseParam),
                skip(parseTuple),
                )

        if res is None:
            return state
        state, _ = res

def parseAnnotation(state):
    newState = bigSkip(
            state,
            token,
            spaceOptional,
            pKeyword(':')
            )
    if newState is None:
        return
    return parseBlock(state)

def captureNoise(state):
    return captureOneOf(
            state,
            skip(parseModule),
            skip(parseImport),
            skip(parseLineComment),
            skip(parseDocs),
            skip(parseAnnotation),
            )

def skipNoise(state):
    (state, _) = captureMany(captureNoise, state)
    return state

def captureStuff(state):
    return captureOneOf(
            state,
            captureType,
            captureNoise,
            captureBinding,
            )

def parseGeneral(state):
    state = skipNoise(state)
    (state, ast) = captureMany(captureStuff, state)
    return (state, ast)

def printState(state):
    (s, i) = state
    print('state:\n' + s[i: i+30])

def parse(fn):
    with open(fn) as f:
        s = f.read()

    state = (s, 0)
    (state, asts) = parseGeneral(state)

    for ast in asts:
        print('==')
        print(ast)

    printState(state)

fn = 'src/DictDotDot.elm'
parse(fn)
