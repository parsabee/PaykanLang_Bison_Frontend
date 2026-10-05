# Changelog

All notable changes to PaykanLang_Bison_Frontend are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **A loadable plugin for the installed `paykan`
  ([parsabee/PaykanLang#141](https://github.com/parsabee/PaykanLang/issues/141)).** The
  frontend is now a shared module, `libpaykan_frontend_bison.so` (`.dylib` on macOS), with
  PaykanLang's C plugin interface (`src/Plugin.cpp`): the user's own `paykan` loads it
  (`--plugin=<file>`, `$PAYKAN_PLUGIN_PATH`, or the installation's plugin directory, where
  `cmake --install` puts it) and `paykan --frontend=bison` selects it. The project no longer
  builds a `paykan` driver of its own. Internally the parser still builds PaykanLang's AST
  (the installed AST and diagnostics libraries are linked into the module) and returns it to
  `paykan` in the AST interchange format; only the C interface and that text cross the
  boundary.
- Every test runs the module through the installed `paykan` or its plugin loader:
  `paykan_add_frontend_tests(bison PLUGIN ...)` (the suites load the module, and
  `InstalledPaykan.bison` runs the installed `paykan` over the corpus), a new `PluginListed`
  test, and the scripts' new `--paykan-arg` option for `FrontendDifferential` and
  `SamplesFrontendParity`.
- Requires a PaykanLang with loadable plugins (#141); CI pins that PaykanLang branch for now.

### Added

- The Bison/Flex frontend, moved out of PaykanLang
  ([parsabee/PaykanLang#60](https://github.com/parsabee/PaykanLang/issues/60)) with its
  history: `Parser.ypp`, `Lexer.lpp`, `BisonFrontend.{h,cpp}` (the `yylex` wrapper with the
  type-argument scan and the 512-level nesting limit), `cmake/BisonFlexSetup.cmake` and
  `scripts/diff_frontends.py`.
- A CMake project that builds the plugin and a `paykan` driver against an installed
  PaykanLang 0.1 (`find_package(Paykan)`, `paykan_add_frontend_plugin` with its
  compatibility check from PaykanLang#103, `paykan_add_driver`).
- Tests: PaykanLang's parser and Sema suites, fuzz smoke and differential tests through
  `paykan_add_frontend_tests`, the `--dump-ast` differential check and a samples run against
  the recursive-descent frontend on the c backend.
- CI on Linux and macOS against a pinned PaykanLang commit, plus a nightly run against
  PaykanLang `develop`.
