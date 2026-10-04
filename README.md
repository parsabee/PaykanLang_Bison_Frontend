# PaykanLang_Bison_Frontend

[![CI](https://github.com/parsabee/PaykanLang_Bison_Frontend/actions/workflows/ci.yml/badge.svg)](https://github.com/parsabee/PaykanLang_Bison_Frontend/actions/workflows/ci.yml)

The Bison/Flex frontend for [PaykanLang](https://github.com/parsabee/PaykanLang), as an
out-of-tree frontend plugin. It is an LALR(1) parser (Bison's `lalr1.cc`) and a Flex scanner
that implement PaykanLang's grammar ([`docs/grammar.md`](https://github.com/parsabee/PaykanLang/blob/develop/docs/grammar.md))
and build exactly the same AST as PaykanLang's built-in recursive-descent frontend. It is also
the reference example of a frontend plugin
([`docs/writing-a-frontend-plugin.md`](https://github.com/parsabee/PaykanLang/blob/develop/docs/writing-a-frontend-plugin.md)).

It is a **plugin for the `paykan` you have installed**: a shared library
(`libpaykan_frontend_bison.so`, `.dylib` on macOS) that your system's `paykan` loads at run
time, with no rebuild of PaykanLang
([PaykanLang#141](https://github.com/parsabee/PaykanLang/issues/141)). Install PaykanLang,
install this plugin, and select it:

```sh
paykan --frontend=bison program.pkn   # run a program, parsed by the Bison frontend
paykan --list-frontends               # bison: ... [<prefix>/lib/paykan/plugins/<version>/libpaykan_frontend_bison.so]
```

The default frontend stays `recursive-descent`; `--frontend=bison` selects this one.
`--trace-parser` and `--trace-scanner` turn on Bison's parse trace and Flex's debug output.

The plugin talks to `paykan` only through PaykanLang's C plugin interface
([`plugin_api.h`](https://github.com/parsabee/PaykanLang/blob/develop/docs/plugins/plugin-api.md)):
`paykan` hands it the source text, and it returns the program in the
[AST interchange format](https://github.com/parsabee/PaykanLang/blob/develop/docs/plugins/ast-format.md).
Internally it is C++ and builds PaykanLang's own AST, with the installed PaykanLang's AST,
diagnostics and AST-writer libraries linked into the module; so it is built with a C++
compiler compatible with the one that built the installation (the same family and standard
library).

## Prerequisites

- An installed PaykanLang of the **0.1** series with loadable plugins
  ([PaykanLang#141](https://github.com/parsabee/PaykanLang/issues/141)) and the frontend test
  support (`paykan_add_frontend_tests`, installed by default). See
  [Compatibility](#compatibility).
- CMake 3.24 or newer, a C++20 compiler (GCC or Clang) and a C compiler.
- **GNU m4**, `make` and a network connection on the first configure: Bison 3.8 and Flex 2.6.4
  are downloaded and built from source into `build/third-party` (GNU `configure` + `make`), and
  Bison runs m4 to generate the parser. `apt install m4`; macOS has it with the Command Line
  Tools (`xcode-select --install`).
- Python 3 for the tests; GoogleTest is found installed or downloaded
  (`-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=<dir>` uses a local copy).

## Building

Install PaykanLang first (any configuration; this is the default, core one):

```sh
git clone https://github.com/parsabee/PaykanLang.git
cmake -S PaykanLang -B paykan-build -DPAYKAN_BUILD_TESTS=OFF
cmake --build paykan-build --parallel
cmake --install paykan-build --prefix "$HOME/paykan"
```

Then build the plugin against it, run its tests, and install it into that PaykanLang:

```sh
git clone https://github.com/parsabee/PaykanLang_Bison_Frontend.git
cd PaykanLang_Bison_Frontend
cmake -B build -DCMAKE_PREFIX_PATH="$HOME/paykan"
cmake --build build --parallel
ctest --test-dir build --output-on-failure
cmake --install build       # into $HOME/paykan/lib/paykan/plugins/<version>/
"$HOME/paykan/bin/paykan" --frontend=bison program.pkn
```

`cmake --install` puts the module into the installation's plugin directory
(`PAYKAN_PLUGIN_INSTALL_DIR`), where that `paykan` finds it by itself. To try it without
installing, load the file directly, or put it in a directory on `$PAYKAN_PLUGIN_PATH` or in
`~/.paykan/plugins/<version>/`:

```sh
paykan --plugin=build/src/libpaykan_frontend_bison.so --frontend=bison program.pkn
```

An installation built with the LLVM backend (`-DPAYKAN_BACKENDS="llvm;c"`) also needs
`-DLLVM_DIR=<llvm>/lib/cmake/llvm` here, the LLVM it was built with.
`-DPAYKAN_BISON_BUILD_TESTS=OFF` skips the tests and GoogleTest.

## Tests

Every test uses the plugin module the way users do: loaded by the **installed** `paykan`
(`--no-plugins --plugin=<module>`), or in process by that installation's own plugin loader.

| Test | What it checks |
|---|---|
| `ParserTests.bison`, `SemaTests.bison` | PaykanLang's frontend-parameterized parser and Sema suites, parsed with `bison` (the module, loaded by the installation's plugin loader); every input is also parsed with `recursive-descent` and the ASTs compared. Includes the nesting-limit tests (`GrammarEdge.Nesting*`). |
| `FrontendTests.bison` | The fuzz smoke test (random and mutated input never crashes, hangs or leaks) and the in-process differential check over the samples corpus. |
| `InstalledPaykan.bison` | The installed `paykan` lists the plugin, and its `--dump-ast` with `bison` equals `recursive-descent`'s for every sample. |
| `PluginListed` | The installed `paykan --version` lists `frontend bison (built with PaykanLang <v>, compatible) [<module>]`. |
| `FrontendDifferential` | `paykan --dump-ast` with `recursive-descent` and with `bison` over every sample: same exit status, same AST ([`scripts/diff_frontends.py`](scripts/diff_frontends.py)). |
| `BuiltWithMismatch` | Configuring with `-DPAYKAN_BISON_BUILT_WITH=<a version the installation does not accept>` fails with the compatibility error. |
| `SamplesFrontendParity` | Every runnable sample on the c backend with each frontend: same stdout, stderr and exit code, zero live heap blocks ([`scripts/samples_frontends.py`](scripts/samples_frontends.py)). |

The suites and the samples come from the PaykanLang installation
(`share/paykan/frontend-tests`, `share/paykan/samples`), so they check the frontend against
exactly the grammar that release implements. Parse-error wording is not compared: Bison words
its errors its own way (`syntax error, unexpected X`) and recovers only at `;` inside a block
(grammar.md section 9).

## Compatibility

| Plugin | PaykanLang |
|---|---|
| 0.1.x | 0.1.x (`find_package(Paykan 0.1)`; the plugin interfaces may change between minor releases) |

The module is built with PaykanLang's `paykan_add_frontend_plugin`, so the plugin declares the
version of the PaykanLang it was built against, and configure fails unless that installation
accepts it (`PAYKAN_PLUGIN_COMPATIBLE_VERSIONS`). When `paykan` loads the module it checks the
plugin API version and that build version before calling anything else in it; `paykan
--version` and `paykan --list-frontends` show whether `bison` is compatible, an incompatible
build is listed as `bison (incompatible: ...)` with its file, and `--frontend=bison` refuses it
(exit status 2). Rebuild the plugin against each PaykanLang release. `-DPAYKAN_BISON_BUILT_WITH=<version>` checks another
build version at configure time (for testing the check).

CI builds PaykanLang from source at a pinned commit (`PAYKAN_REF` in
[`.github/workflows/ci.yml`](.github/workflows/ci.yml)) on Linux and macOS, installs it, removes
its source and build trees, builds and tests the plugin against the installation, installs the
plugin into it, removes the plugin's build tree, and runs `paykan --frontend=bison`. A nightly
run does the same against PaykanLang's `develop` and opens an issue when it fails, so a grammar
or interface change in PaykanLang shows up here within a day. When PaykanLang's grammar
changes, `docs/grammar.md` and the recursive-descent frontend change first; this frontend
follows.

## Layout

```
CMakeLists.txt              find_package(Paykan), the plugin module and its install rule
cmake/BisonFlexSetup.cmake  downloads and builds Bison and Flex (needs m4)
src/                        Parser.ypp, Lexer.lpp, BisonFrontend.{h,cpp} (the yylex wrapper:
                            type-argument disambiguation and the nesting limit), Plugin.cpp
                            (the C plugin interface)
tests/CMakeLists.txt        the test suites above
scripts/                    diff_frontends.py, samples_frontends.py
```

The module is built with `-fexceptions -frtti` (Bison's `lalr1.cc` skeleton needs them); no
exception crosses the plugin interface.

## License

MIT, like PaykanLang; see [LICENSE](LICENSE).
