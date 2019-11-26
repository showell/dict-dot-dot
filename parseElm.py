import types

from parse import (
        twoPass,
        captureMany,
        captureOneOf,
        skip,
        spaceRequired,
        spaceOptional,
        bigSkip,
        pKeyword,
        token,
        optional,
        peek,
        advanceState,
        pUntil,
        parseBlock,
        captureSeq,
        captureSubBlock,
        )

def capturePunt(state):
    (s, i) = state
    newState = ('', 0)
    ast = 'unparsed: ' + s[i:]
    return (newState, ast)

def parseType(state):
    if peek(state, 'type'):
        return parseBlock(state)

captureType = twoPass(parseType, capturePunt)

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
    res = captureSeq(
            state,
            captureSubBlock('let', captureLetBindings),
            captureSubBlock('in', capturePunt),
            )

    if not res:
        return

    state, asts = res
    bindings, expr = asts

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
    res = captureSeq(
            state,
            skip(spaceOptional),
            skip(pKeyword('if')),
            skip(spaceRequired),
            twoPass(pUntil('then'), captureExpr),
            skip(pKeyword('then')),
            twoPass(pUntil('else'), captureExpr),
            captureSubBlock('else', captureExpr)
            )
    if res is None:
        return
    state, ast = res

    ast = 'if:\n' + str(ast[0]) + '\nthen:\n' + str(ast[1]) + '\nelse:\n' + str(ast[2])
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

captureBinding = twoPass(parseBinding, captureBindingBlock)

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
            skip(spaceRequired),
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
