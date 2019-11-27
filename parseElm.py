import types

from parse import (
        advanceState,
        bigSkip,
        captureKeywordBlock,
        captureMany,
        captureOneOf,
        captureSeq,
        captureSubBlock,
        captureUntilKeywordEndsLine,
        grab,
        parseBlock,
        parseKeywordBlock,
        parseMyLevel,
        parseRange,
        parseSameLine,
        peek,
        printState,
        pKeyword,
        pLine,
        pUntil,
        pUntilChar,
        pUntilLineEndsWith,
        skip,
        skipManyCaptures,
        spaceOptional,
        spaceRequired,
        token,
        transform,
        twoPass,
        )

# We declare a few things to avoid circular dependencies
def captureExpr(state):
    return doCaptureExpr(state)

# This should obviously eventually go away!
def capturePunt(state):
    (s, i) = state
    newState = ('', 0)
    ast = 'unparsed: ' + s[i:].strip()
    return (newState, ast)

parseModule = parseKeywordBlock('module')

parseDocs = parseRange('{-|', '-}')

parseLineComment = bigSkip(pKeyword('--'), pLine)

parseImport = parseKeywordBlock('import')

captureType = \
    transform(
        types.Type,
        captureKeywordBlock('type')
        )

captureIf = \
    transform(
        types.If,
        captureSeq(
            skip(pKeyword('if')),
            skip(spaceRequired),
            twoPass(pUntil('then'), captureExpr),
            skip(pKeyword('then')),
            twoPass(pUntil('else'), captureExpr),
            captureSubBlock('else', captureExpr)
            )
        )

captureCaseOf = \
    transform(
        types.CaseOf,
        captureSeq(
            skip(pKeyword('case')),
            captureUntilKeywordEndsLine(
                'of',
                capturePunt
                ),
            )
        )

capturePatternDef = \
    transform(
        types.PatternDef,
        captureSeq(
            captureUntilKeywordEndsLine(
                '->',
                capturePunt
                ),
            ),
        )

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
                twoPass(
                    pUntilLineEndsWith('='),
                    captureSeq(
                        grab(token),
                        skip(spaceOptional),
                        skip(parseParams),
                        ),
                    ),
                skip(pLine),
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

captureLetBindings = \
    captureMany(captureBinding)

captureLet = \
    transform(
        types.Let,
        captureSeq(
            captureSubBlock('let', captureLetBindings),
            captureSubBlock('in', capturePunt),
            )
        )

def parseTuple(state):
    return bigSkip(
            pKeyword('('),
            pUntilChar(')'),
            pKeyword(')'),
            )(state)

def parseParam(state):
    return bigSkip(token)(state)

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
            pLine,
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

skipNoise = skipManyCaptures(captureNoise)

def captureStuff(state):
    return captureOneOf(
            captureNoise,
            captureType,
            captureBinding,
            )(state)

def parseGeneral(state):
    (state, ast) = skipNoise(state)
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

doCaptureExpr = \
    captureSeq(
        skipNoise,
        captureOneOf(
            captureLet,
            captureIf,
            captureCase,
            capturePunt,
            )
        )

if __name__ == '__main__':
    fn = 'src/DictDotDot.elm'
    parse(fn)
