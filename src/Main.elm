module Main exposing (main)

import Browser
import DictInternal
import Html
import MyDict as Dict



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
        d =
            Dict.empty
                |> Dict.insert 1 "one"
                |> Dict.insert 2 "two"
                |> Dict.insert 3 "three"
                |> Dict.insert 4 "four"

        s =
            d
                |> DictInternal.toInternalRepresentation
                |> Debug.toString
                |> String.replace "}," "},\n "
    in
    { title = model.title
    , body = [ Html.pre [] [ Html.text s ] ]
    }
