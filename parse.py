import types

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

def identity(s):
    return s

def capture(f, parse):
    def f_(state):
        (s, iOrig) = state
        newState = parse(state)
        if newState is None:
            return None
        (s, i) = newState
        ast = f(s[iOrig:i])
        return (newState, ast)

    return f_

def skip(parse):
    return capture(Skip, parse)

def captureMany(parse, state):
    asts = []
    while True:
        res = parse(state)
        if res is None: break
        state, ast = res
        asts.append(ast)

    asts = [a for a in asts if type(a) != Skip]
    return (state, asts)

class Skip:
    def __init__(self, s):
        pass

def oneOf(state, *fns):
    for fn in fns:
        res = fn(state)
        if res is not None:
            return res

def peek(state, kw):
    (s, i) = state
    return s[i:i+len(kw)] == kw

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

captureType = capture(identity, parseType)

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

def parseBinding(state):
    origState = state
    newState = parseDef(state)
    if newState is None:
        return
    return parseBlock(origState)

def transformBinding(s):
    # MAJOR HACK -- trying to make progress
    if s.startswith('partition'):
        state = (s, 0)
        state = parseDef(state)

        if not peek(state, "let"):
            raise Exception('expected let')

        state, let = capture(identity, parseBlock)(state)

        state = spaceOptional(state)

        state = bigSkip(
                state,
                spaceOptional,
                pKeyword("in"),
                spaceOptional,
                )

        if not state:
            raise Exception("expected in")

        _, expr = capture(identity, parseBlock)(state)
        return types.Let(let=let, in_=expr)

    return Skip(s)

captureBinding = capture(transformBinding, parseBinding)

def parseParams(state):
    while True:
        newState = bigSkip(
                state,
                token,
                spaceOptional
                )
        if newState is None:
            return state
        state = newState

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
    return oneOf(
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
    return oneOf(
            state,
            captureNoise,
            captureType,
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
