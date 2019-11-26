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

def captureSubBlock(keyword, f):
    def wrapper(state):
        state = bigSkip(
                state,
                spaceOptional,
                pKeyword(keyword),
                pUntil('\n'),
                spaceOptional
                )
        if not state:
            return

        return twoPass(parseBlock, f)(state)

    return wrapper

def twoPass(parse, f):
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

def captureMany(f, state):
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

def captureSeq(state, *fns):
    asts = []
    for fn in fns:
        res = fn(state)
        if res is None:
            return
        state, ast = res
        asts.append(ast)

    asts = [a for a in asts if type(a) != Skip]
    return (state, asts)

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

