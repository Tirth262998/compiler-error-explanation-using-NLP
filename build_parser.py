from tree_sitter import Language

Language.build_library(
    "build/languages.so",
    ["tree-sitter-c"]
)