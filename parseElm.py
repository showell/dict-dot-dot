import types

from parse import (
        advanceState,
        bigSkip,
        captureMany,
        captureOneOf,
        captureSeq,
        captureSubBlock,
        grab,
        optional,
        parseBlock,
        parseMyLevel,
        parseSameLine,
        peek,
        printState,
        pKeyword,
        pUntil,
        skip,
        spaceOptional,
        spaceRequired,
        token,
        transform,
        twoPass,
        )

def capturePunt(state):
    (s, i) = state
    newState = ('', 0)
    ast = 'unparsed: ' + s[i:].strip()
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
            captureCase,
            capturePunt,
            )(state)

def captureIf(state):
    return \
        transform(
            types.If,
            captureSeq(
                skip(spaceOptional),
                skip(pKeyword('if')),
                skip(spaceRequired),
                twoPass(pUntil('then'), captureExpr),
                skip(pKeyword('then')),
                twoPass(pUntil('else'), captureExpr),
                captureSubBlock('else', captureExpr)
                )
            )(state)

def captureCaseOf(state):
    return \
        transform(
            types.CaseOf,
            captureSeq(
                skip(spaceOptional),
                twoPass(
                    pUntil('\n'),
                    captureSeq(
                        skip(pKeyword('case ')),
                        twoPass(
                            pUntil(' of'),
                            capturePunt,
                            ),
                        ),
                    ),
                skip(spaceOptional),
                ),
            )(state)

def capturePatternDef(state):
    return \
        transform(
            types.PatternDef,
            captureSeq(
                skip(spaceOptional),
                twoPass(
                    pUntil('\n'),
                    twoPass(
                        pUntil(' ->'),
                        capturePunt,
                        ),
                    ),
                skip(spaceOptional)
                ),
            )(state)

def captureOneCase(state):
    return \
        transform(
            types.OneCase,
            captureSeq(
                capturePatternDef,
                skip(spaceOptional),
                twoPass(
                    parseMyLevel,
                    captureExpr,
                    ),
                ),
            )(state)

def captureCaseRaw(state):
    return captureSeq(
            captureCaseOf,
            skip(spaceOptional),
            twoPass(
                parseMyLevel,
                captureMany(captureOneCase),
                )
            )(state)

def captureCase(state):
    res = captureCaseRaw(state)
    if res is None:
        return

    state, ast = res
    return state, types.Case(ast)

def captureDef(state):
    return \
        transform(
            types.Def,
            captureSeq(
                skip(spaceOptional),
                twoPass(
                    pUntil(' =\n'),
                    captureSeq(
                        grab(token),
                        skip(spaceOptional),
                        skip(parseParams),
                        ),
                    ),
                skip(pKeyword(' =')),
                skip(spaceOptional),
                )
            )(state)

def captureBinding(state):
    return \
        transform(
            types.Binding,
            captureSeq(
                captureDef,
                skip(spaceOptional),
                twoPass(
                    parseMyLevel,
                    captureExpr
                    ),
                skip(spaceOptional),
                ),
            )(state)

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
            captureNoise,
            captureType,
            captureBinding,
            )(state)

def parseGeneral(state):
    state = skipNoise(state)
    (state, ast) = captureMany(captureStuff)(state)
    return (state, ast)

def parse(fn):
    with open(fn) as f:
        s = f.read()

    state = (s, 0)
    (state, asts) = parseGeneral(state)

    for ast in asts:
        print('==')
        print(ast)

    printState(state)

if __name__ == '__main__':
    fn = 'src/DictDotDot.elm'
    parse(fn)
