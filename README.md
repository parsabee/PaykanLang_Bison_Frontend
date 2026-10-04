# PaykanLang_Bison_Frontend

[![CI](https://github.com/parsabee/PaykanLang_Bison_Frontend/actions/workflows/ci.yml/badge.svg)](https://github.com/parsabee/PaykanLang_Bison_Frontend/actions/workflows/ci.yml)

The Bison/Flex frontend for [PaykanLang](https://github.com/parsabee/PaykanLang), as an
out-of-tree frontend plugin. It is an LALR(1) parser (Bison's `lalr1.cc`) and a Flex scanner
that implement PaykanLang's grammar ([`docs/grammar.md`](https://github.com/parsabee/PaykanLang/blob/develop/docs/grammar.md))
and build exactly the same AST as PaykanLang's built-in recursive-descent frontend. It is also
the reference example of a frontend plugin
([`docs/writing-a-frontend.md`](https://github.com/parsabee/PaykanLang/blob/develop/docs/writing-a-frontend.md)).

The plugin is built against an **installed** PaykanLang with `find_package(Paykan)`; it uses
only the installation's headers, libraries and CMake package. The build produces a `paykan`
driver that has every frontend and backend of the installation plus this one:

```sh
paykan --frontend=bison program.pkn   # run a program, parsed by the Bison frontend
paykan --list-frontends               # bison, recursive-descent (default)
```

The default frontend stays `recursive-descent`; `--frontend=bison` selects this one.
`--trace-parser` and `--trace-scanner` turn on Bison's parse trace and Flex's debug output.

## Prerequisites

- An installed PaykanLang of the **0.1** series with the plugin compatibility check
  (`paykan_add_frontend_plugin`, [PaykanLang#103](https://github.com/parsabee/PaykanLang/issues/103))
  and the frontend test support (`paykan_add_frontend_tests`, installed by default). See
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

Then build the plugin against it and run its tests:

```sh
git clone https://github.com/parsabee/PaykanLang_Bison_Frontend.git
cd PaykanLang_Bison_Frontend
cmake -B build -DCMAKE_PREFIX_PATH="$HOME/paykan"
cmake --build build --parallel
ctest --test-dir build --output-on-failure
build/bin/paykan --frontend=bison program.pkn
```

An installation built with the LLVM backend (`-DPAYKAN_BACKENDS="llvm;c"`) also needs
`-DLLVM_DIR=<llvm>/lib/cmake/llvm` here, the LLVM it was built with.
`cmake --install build --prefix <dir>` installs the `paykan` driver (with the Bison frontend)
to `<dir>/bin`; it finds its runtime in the PaykanLang installation it was built against.
`-DPAYKAN_BISON_BUILD_TESTS=OFF` skips the tests and GoogleTest.

## Tests

| Test | What it checks |
|---|---|
| `ParserTests.bison`, `SemaTests.bison` | PaykanLang's frontend-parameterized parser and Sema suites, parsed with `bison`; every input is also parsed with `recursive-descent` and the ASTs compared. Includes the nesting-limit tests (`GrammarEdge.Nesting*`). |
| `FrontendTests.bison` | The fuzz smoke test (random and mutated input never crashes, hangs or leaks) and the in-process differential check over the samples corpus. |
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

The library is built with PaykanLang's `paykan_add_frontend_plugin`, so the plugin records the
version of the PaykanLang it was built against, and configure fails unless that installation
accepts it (`PAYKAN_PLUGIN_COMPATIBLE_VERSIONS`). At run time `paykan --version` and
`paykan --list-frontends` show whether `bison` is compatible; an incompatible build is listed
as `bison (incompatible: ...)` and `--frontend=bison` refuses it (exit status 2). Rebuild the
plugin against each PaykanLang release. `-DPAYKAN_BISON_BUILT_WITH=<version>` checks another
build version at configure time (for testing the check).

CI builds PaykanLang from source at a pinned commit (`PAYKAN_REF` in
[`.github/workflows/ci.yml`](.github/workflows/ci.yml)) on Linux and macOS, installs it, removes
its source and build trees, and builds and tests the plugin against the installation. A nightly
run does the same against PaykanLang's `develop` and opens an issue when it fails, so a grammar
or interface change in PaykanLang shows up here within a day. When PaykanLang's grammar
changes, `docs/grammar.md` and the recursive-descent frontend change first; this frontend
follows.

## Layout

```
CMakeLists.txt              find_package(Paykan), the plugin, the paykan driver
cmake/BisonFlexSetup.cmake  downloads and builds Bison and Flex (needs m4)
src/                        Parser.ypp, Lexer.lpp, BisonFrontend.{h,cpp} (the yylex wrapper:
                            type-argument disambiguation and the nesting limit)
tests/CMakeLists.txt        the test suites above
scripts/                    diff_frontends.py, samples_frontends.py
```

The library is the only code built with `-fexceptions -frtti` (Bison's `lalr1.cc` skeleton needs
them); no exception crosses the frontend interface.

## License

MIT, like PaykanLang; see [LICENSE](LICENSE).
