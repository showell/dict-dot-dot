module DictInternal exposing (toInternalRepresentation)

{-| helper(s) to see Dict internal

@docs toInternalRepresentation

-}

import DictDotDot exposing (..)


type alias InternalNode k v =
    { k : k
    , v : v
    , color : String
    , path : String
    }


{-| Reveal internal representation of Dict for advanced testing/debugging.
This returns a list of nodes in sorted order. Each node has k/v, plus
a path to the node that looks something like "llr", and the color of
the node ("R" or "B").

Example output is something like this:

        [{ color = "B", k = 1, path = "l", v = "one" },
         { color = "B", k = 2, path = "", v = "two" },
         { color = "R", k = 3, path = "rl", v = "three" },
         { color = "B", k = 4, path = "r", v = "four" }]

-}
toInternalRepresentation : Dict k v -> List (InternalNode k v)
toInternalRepresentation dict =
    let
        nodeList : String -> Dict k v -> List (InternalNode k v)
        nodeList path d =
            case d of
                RBNode_elm_builtin c k v left right ->
                    let
                        color =
                            case c of
                                Red ->
                                    "R"

                                Black ->
                                    "B"

                        node =
                            { k = k
                            , v = v
                            , color = color
                            , path = path
                            }
                    in
                    nodeList (path ++ "l") left
                        ++ (node :: nodeList (path ++ "r") right)

                _ ->
                    []
    in
    nodeList "" dict
