import types

from parse import (
        advanceState,
        bigSkip,
        captureMany,
        captureOneOf,
        captureSeq,
        captureSubBlock,
        optional,
        parseBlock,
        parseSameLine,
        peek,
        pKeyword,
        pUntil,
        skip,
        spaceOptional,
        spaceRequired,
        token,
        twoPass,
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
            pKeyword('module'),
            spaceRequired,
            token,
            spaceRequired,
            pKeyword('exposing'),
            spaceOptional,
            pKeyword('('),
            spaceOptional,
            )(state)

    if state is None: return

    while True:
        state = bigSkip(
                token,
                optional(pKeyword('(..)')),
                spaceOptional
                )(state)
        if state is None: return

        if peek(state, ')'):
            state = advanceState(state, 1)
            break

        state = bigSkip(
                pKeyword(','),
                spaceOptional
                )(state)
        if state is None: return

    state = spaceOptional(state)

    return state

def parseDocs(state):
    state = bigSkip(
            pKeyword('{-| '),
            pUntil('-}'),
            pKeyword('-}'),
            spaceRequired
            )(state)
    return state

def parseLineComment(state):
    return bigSkip(
            pKeyword('--'),
            pUntil('\n'),
            spaceOptional,
            )(state)

def parseImport(state):
    return bigSkip(
            pKeyword('import'),
            pUntil('\n'),
            spaceOptional,
            )(state)

def parseDef(state):
    return parseSameLine(
            bigSkip(
                token,
                spaceOptional,
                parseParams,
                spaceOptional,
                pKeyword('='),
                spaceOptional,
            )
            )(state)

def captureLet(state):
    res = captureSeq(
            captureSubBlock('let', captureLetBindings),
            captureSubBlock('in', capturePunt),
            )(state)

    if not res:
        return

    state, asts = res
    bindings, expr = asts

    ast = types.Let(bindings=bindings, in_=expr)
    return state, ast

def captureLetBindings(state):
    (s, i) = state
    res = captureMany(captureBinding)(state)
    if res is None:
        printState(state)
        raise Exception('could not get binding')
    return res

def captureExpr(state):
    return captureOneOf(
            captureLet,
            captureIf,
            capturePunt,
            )(state)

def captureIf(state):
    res = captureSeq(
            skip(spaceOptional),
            skip(pKeyword('if')),
            skip(spaceRequired),
            twoPass(pUntil('then'), captureExpr),
            skip(pKeyword('then')),
            twoPass(pUntil('else'), captureExpr),
            captureSubBlock('else', captureExpr)
            )(state)
    if res is None:
        return
    state, ast = res

    ast = 'if:\n' + str(ast[0]) + '\nthen:\n' + str(ast[1]) + '\nelse:\n' + str(ast[2])
    return (state, ast)

def captureBindingBlock(state):
    newState = parseDef(state)

    if newState is None:
        printState(state)
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
            spaceOptional,
            pKeyword('('),
            pUntil(')'),
            pKeyword(')'),
            spaceOptional
            )(state)

def parseParam(state):
    return bigSkip(
            token,
            spaceOptional
            )(state)

def parseParams(state):
    while True:
        res = captureOneOf(
                skip(parseParam),
                skip(parseTuple),
                )(state)

        if res is None:
            return state
        state, _ = res

def parseAnnotation(state):
    newState = bigSkip(
            token,
            spaceOptional,
            pKeyword(':'),
            pUntil('\n'),
            )(state)
    if newState is None:
        return
    state = parseBlock(state)
    return state

def captureNoise(state):
    return captureOneOf(
            skip(spaceRequired),
            skip(parseModule),
            skip(parseImport),
            skip(parseLineComment),
            skip(parseDocs),
            skip(parseAnnotation),
            )(state)

def skipNoise(state):
    (state, _) = captureMany(captureNoise)(state)
    return state

def captureStuff(state):
    return captureOneOf(
            captureType,
            captureBinding,
            captureNoise,
            )(state)

def parseGeneral(state):
    state = skipNoise(state)
    (state, ast) = captureMany(captureStuff)(state)
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
