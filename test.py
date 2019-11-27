import parseElm
import parse
import types

def succeed(res):
    if res is None:
        raise Exception('parse failure')
    state, ast = res
    (s, i) = state
    if i != len(s):
        parse.printState(state)
        raise Exception('partial parse')
    print("\n---")

    if type(ast) == types.UnParsed:
        raise Exception('did not really parse')

    print(ast)


def st(s):
    return (s, 0)

succeed(parseElm.skip(parseElm.parseDocs)(
    st("""
    {-|
       bla bla bla
    -}
    """)))

succeed(parseElm.skip(parseElm.parseImport)(
    st("""
import foo exposing (
    foo, bar
    )
    """)))

succeed(parseElm.skip(parseElm.parseModule)(
    st("""
    module foo exposing (
        foo, bar
        )
    """)))

succeed(parseElm.captureType(
    st("""
    type Value =
        = Int
        | String
    """)))

succeed(parseElm.captureDef(
    st("""
    x =
    """)))

succeed(parseElm.captureBinding(
    st("""
    x =
        5""")))

succeed(parseElm.captureOneCase(
    st("""
    foo bar ->
        hello
        world

        """)))

succeed(parseElm.captureCaseOf(
    st("""
    case fred of
        """)))

succeed(parseElm.captureCase(
    st("""
    case fred of
        foo ->
            f foo
                bla

        bar ->
            f bar
                bla
        """)))

succeed(parseElm.captureLet(
    st("""
    let
        foo a b c =
            one

        bar x y z =
            two
    in
    foo bar""")))

succeed(parseElm.captureIf(
    st("""
    if cond then
        if cond2 then
            a
        else
            b

    else
        false_val
            stuff
        """)))

# tuples are dumb now
succeed(parseElm.captureTuple(
    st("""
        ( foo, bar )
        """)))

succeed(parseElm.captureExpr(
    st("""
        add 5 7
        """)))

succeed(parseElm.captureAnnotation(
    st("""
foo : List String ->
   String ->
   Int""")))
