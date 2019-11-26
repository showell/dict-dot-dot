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

def bigSkip(*fns):
    def wrapper(state):
        for fn in fns:
            state = fn(state)
            if state is None: return
        return state
    return wrapper

def captureSubBlock(keyword, f):
    def wrapper(state):
        state = bigSkip(
                spaceOptional,
                pKeyword(keyword),
                pUntil('\n'),
                spaceOptional
                )(state)
        if not state:
            return

        return twoPass(parseBlock, f)(state)

    return wrapper

def parseSameLine(parse):
    return twoPassParse(
            pUntil('\n'),
            parse)

def twoPassParse(parse1, parse2):
    def wrapper(state):
        (s, iOrig) = state
        state1 = parse1(state)
        if state1 is None:
            return None
        (s, iEnd) = state1
        lineText = s[iOrig:iEnd]
        subState = (lineText, 0)

        state2 = parse2(subState)
        if state2 is None:
            return None

        (_, n) = state2
        return (s, iOrig + n)

    return wrapper

def twoPass(parse, f):
    def wrapper(state):
        (s, iOrig) = state
        newState = parse(state)
        if newState is None:
            return None
        (s, i) = newState
        blockText = s[iOrig:i]
        print('blockText', blockText)
        subState = (blockText, 0)
        _, ast = f(subState)
        if ast is None:
            return None

        return (newState, ast)

    return wrapper

def skip(parse):
    def f(state):
        newState = parse(state)
        if newState is None:
            return
        return (newState, Skip())

    return f

def captureMany(f):
    def wrapper(state):
        asts = []
        while True:
            if peek(state, 'STOP'):
                break

            res = f(state)
            if res is None: break
            state, ast = res
            asts.append(ast)

        asts = [a for a in asts if type(a) != Skip]
        return (state, asts)
    return wrapper

def captureSeq(*fns):
    def wrapper(state):
        asts = []
        for fn in fns:
            res = fn(state)
            if res is None:
                return
            state, ast = res
            asts.append(ast)

        asts = [a for a in asts if type(a) != Skip]
        return (state, asts)
    return wrapper

class Skip:
    pass

def captureOneOf(*fns):
    def wrapper(state):
        for fn in fns:
            res = fn(state)
            if res is not None:
                return res
    return wrapper

def peek(state, kw):
    (s, i) = state
    return s[i:i+len(kw)] == kw

def peekOneOf(state, *kws):
    return any(peek(state, kw) for kw in kws)

def advanceState(state, n):
    (s, i) = state
    return (s, i + n)

def optional(f):
    def wrapper(state, *args):
        origState = state
        res = f(state, *args)
        if res is None:
            return origState
        return res

    return wrapper

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

