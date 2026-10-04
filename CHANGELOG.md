# Changelog

All notable changes to PaykanLang_Bison_Frontend are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- The Bison/Flex frontend, moved out of PaykanLang
  ([parsabee/PaykanLang#60](https://github.com/parsabee/PaykanLang/issues/60)) with its
  history: `Parser.ypp`, `Lexer.lpp`, `BisonFrontend.{h,cpp}` (the `yylex` wrapper with the
  type-argument scan and the 512-level nesting limit), `cmake/BisonFlexSetup.cmake` and
  `scripts/diff_frontends.py`.
- A CMake project that builds the plugin and a `paykan` driver against an installed
  PaykanLang 0.1 (`find_package(Paykan)`, `paykan_add_driver`).
- Tests: PaykanLang's parser and Sema suites, fuzz smoke and differential tests through
  `paykan_add_frontend_tests`, the `--dump-ast` differential check and a samples run against
  the recursive-descent frontend on the c backend.
- CI on Linux and macOS against a pinned PaykanLang commit, plus a nightly run against
  PaykanLang `develop`.
