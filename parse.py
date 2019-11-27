"""
parser : state -> state
capture : state -> (state, ast)
"""

def printState(state):
    (s, i) = state
    print('state:\n' + s[i:i+50])

def transform(f, cap):
    def wrapper(state):
        res = cap(state)
        if res is None:
            return
        state, ast = res
        return state, f(ast)
    return wrapper

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
        state = spaceOptional(state)
        for fn in fns:
            state = fn(state)
            if state is None: return
        state = spaceOptional(state)
        return state
    return wrapper

def captureSubBlock(keyword, f):
    def wrapper(state):
        state = bigSkip(
                spaceOptional,
                pKeyword(keyword),
                pLine,
                spaceOptional
                )(state)
        if not state:
            return

        return twoPass(parseMyLevel, f)(state)

    return wrapper

def parseSameLine(parse):
    return twoPassParse(
            pLine,
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
        subState = (blockText, 0)
        res = f(subState)
        if res is None:
            return None

        _, ast = res
        return (newState, ast)

    return wrapper

def grab(parse):
    def f(state):
        (s, iOrig) = state
        newState = parse(state)
        if newState is None:
            return
        (_, iNew) = newState
        text = s[iOrig:iNew]
        return (newState, text)

    return f

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

        asts = noSkips(asts)
        return (state, asts)
    return wrapper

def noSkips(asts):
    return [a for a in asts if type(a) != Skip]

def fixAsts(asts):
    asts = noSkips(asts)
    if len(asts) == 1:
        return asts[0]
    return asts

def captureSeq(*fns):
    def wrapper(state):
        asts = []
        for fn in fns:
            res = fn(state)
            if res is None:
                return
            state, ast = res
            asts.append(ast)

        ast = fixAsts(asts)
        return (state, ast)
    return wrapper

class Skip:
    pass

def parseOneOf(*fns):
    def wrapper(state):
        for fn in fns:
            res = fn(state)
            if res is not None:
                return res
    return wrapper

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


def pUntil(kw):
    if kw == '\n':
        raise Exception('use pLine for detecting end of line')
    if len(kw) == 1:
        raise Exception('use pUntilIncludingChar for single characters')

    def wrapper(state):
        (s, i) = state
        n = len(kw)
        while i < len(s):
            if s[i:i+n] == kw:
                return (s, i)
            i += 1
    return wrapper

def pUntilChar(c):
    def wrapper(state):
        (s, i) = state
        while i < len(s):
            if s[i] == c:
                return (s, i)
            i += 1
    return wrapper

def pLine(state):
    (s, i) = state
    while i < len(s):
        if s[i] == '\n':
            return (s, i)
        i += 1
    # end of file is equivalent to newline
    return (s, i)

def pUntilIncluding(kw):
    def wrapper(state):
        (s, i) = state
        n = len(kw)
        while i < len(s):
            if s[i:i+n] == kw:
                return (s, i+n)
            i += 1
    return wrapper

def isBeginWord(s, start):
    return start == 0 or s[start-1].isspace()

def isEndWord(s, end):
    return end >= len(s) or s[end].isspace()

def isWord(s, start, end):
    return isBeginWord(s, start) and isEndWord(s, end)

def pKeyword(kw):
    def wrapper(state):
        (s, i) = state
        iEnd = i + len(kw)
        if s[i : iEnd] == kw:
            if isWord(s, i, iEnd):
                return (s, iEnd)
    return wrapper

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


def parseMyLevel(state):
    (s, i) = state
    level = indentLevel(s, i)

    i = readline(s, i)

    while i < len(s) and indentLevel(s, i) >= level:
        i = readline(s, i)

    return (s, i)

def parseBlock(state):
    (s, i) = state
    level = indentLevel(s, i)

    i = readline(s, i)

    while i < len(s) and indentLevel(s, i) > level:
        i = readline(s, i)

    return (s, i)

def onlyIf(parse1, parse2):
    def wrapper(state):
        if parse1(state) is None:
            return
        return parse2(state)
    return wrapper

def parseKeywordBlock(keyword):
    def wrapper(state):
        state = spaceOptional(state)
        if state is None:
            return
        return onlyIf(
            pKeyword(keyword),
            parseBlock
            )(state)
    return wrapper

def captureKeywordBlock(keyword):
    return captureSeq(
        grab(parseKeywordBlock(keyword)),
        skip(spaceOptional))

def parseRange(start, end):
    return bigSkip(
            spaceOptional,
            parseOneOf(
                pKeyword(start + ' '),
                pKeyword(start + '\n'),
                ),
            parseOneOf(
                pUntilIncluding(' ' + end),
                pUntilIncluding('\n' + end),
                ),
            spaceOptional
            )

