module Main exposing (main)

import Browser
import DictDotDot as Dict
import DictInternal
import Html



-- MODEL / INIT


main : Program () Model Msg
main =
    Browser.document
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }


type alias Model =
    { title : String
    }


type Msg
    = Never


init : () -> ( Model, Cmd Msg )
init _ =
    let
        model =
            { title = "simple demo"
            }
    in
    ( model, Cmd.none )



-- UPDATE


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    ( model, Cmd.none )



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions _ =
    Sub.none



-- VIEW


view : Model -> Browser.Document Msg
view model =
    let
        {- repro bug reported https://github.com/elm/core/pull/1033
        -}
        d1 =
            Dict.empty
                |> Dict.insert 0 Nothing
                |> Dict.insert 5 Nothing
                |> Dict.insert 6 Nothing
                |> Dict.insert 4 Nothing
                |> Dict.insert 2 Nothing
                |> Dict.insert 3 Nothing
                |> Dict.insert 1 Nothing
                |> Dict.insert 7 Nothing
                |> Dict.remove 0
                |> Dict.remove 5
                |> Dict.remove 6
                |> Dict.remove 4
                |> Dict.remove 2

        d2 =
            Dict.empty
                |> Dict.insert 3 Nothing
                |> Dict.insert 1 Nothing
                |> Dict.insert 7 Nothing


        s1 =
            d1
                |> DictInternal.toInternalRepresentation
                |> Debug.toString
                |> String.replace "}," "},\n "
        s2 =
            d2
                |> DictInternal.toInternalRepresentation
                |> Debug.toString
                |> String.replace "}," "},\n "
    in
    { title = model.title
    , body = [ Html.pre [] [ Html.text s1, Html.text "\n\n", Html.text s2 ] ]
    }
