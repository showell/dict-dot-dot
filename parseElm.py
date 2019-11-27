import types

from parse import (
        advanceState,
        bigSkip,
        captureKeywordBlock,
        captureOneOrMore,
        captureZeroOrMore,
        captureOneOf,
        captureSeq,
        captureSubBlock,
        captureUntilKeywordEndsLine,
        grab,
        onlyIf,
        parseAll,
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
capturePunt = \
    transform(
        types.UnParsed,
        grab(parseAll)
    )

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
            captureUntilKeywordEndsLine(
                'then',
                captureExpr
                ),
            twoPass(
                parseMyLevel,
                captureExpr
                ),
            captureSubBlock(
                'else',
                captureExpr
                ),
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

captureOneCase = \
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
        )

captureCase = \
    transform(
        types.Case,
        captureSeq(
            captureCaseOf,
            skip(spaceOptional),
            twoPass(
                parseMyLevel,
                captureOneOrMore(captureOneCase),
                )
            )
        )

captureTuple = \
    transform(
        types.Tuple,
        captureSeq(
            skip(pKeyword('(')),
            twoPass(
                pUntilChar(')'),
                capturePunt,
                ),
            skip(pKeyword(')')),
            skip(spaceOptional)
            ),
        )

captureParams = \
    transform(
        types.Params,
        captureZeroOrMore(
            captureOneOf(
                grab(token),
                captureTuple,
                )
            )
        )

captureDef = \
    transform(
        types.Def,
        captureUntilKeywordEndsLine(
            '=',
            captureSeq(
                grab(token),
                skip(spaceOptional),
                captureParams,
                ),
            ),
        )

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
    captureOneOrMore(captureBinding)

captureLet = \
    transform(
        types.Let,
        captureSeq(
            captureSubBlock('let', captureLetBindings),
            captureSubBlock('in', capturePunt),
            )
        )

captureAnnotation = \
    transform(
        types.Annotation,
        captureSeq(
            onlyIf(
                captureSeq(
                    skip(token),
                    skip(spaceOptional),
                    pKeyword(':'),
                    ),
                grab(parseBlock),
                ),
            ),
        )

def captureNoise(state):
    return captureOneOf(
            skip(spaceRequired),
            skip(parseModule),
            skip(parseImport),
            skip(parseLineComment),
            skip(parseDocs),
            captureAnnotation,
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
    (state, ast) = captureOneOrMore(captureStuff)(state)
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

captureCall = \
    transform(
        types.Call,
        captureOneOrMore(
            grab(token),
            )
        )

doCaptureExpr = \
    captureSeq(
        skipNoise,
        captureOneOf(
            captureLet,
            captureIf,
            captureCase,
            captureCall,
            capturePunt,
            )
        )

if __name__ == '__main__':
    fn = 'src/DictDotDot.elm'
    parse(fn)
