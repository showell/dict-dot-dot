import parseElm
import parse

def succeed(res):
    if res is None:
        raise Exception('parse failure')
    state, ast = res
    (s, i) = state
    if i != len(s):
        parse.printState(state)
        raise Exception('partial parse')
    print("\n---")
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

        bar ->
            f bar
        """)))

succeed(parseElm.captureLet(
    st("""
    let
        foo =
            one

        bar =
            two
    in
    foo bar""")))

succeed(parseElm.captureIf(
    st("""
    if cond then
        true_val

    else
        false_val
        """)))

