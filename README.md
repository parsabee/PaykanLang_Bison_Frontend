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

It is plain Flex and plain Bison: the Flex scanner feeds the LALR(1) parser directly, with no
hand-written token lookahead or re-lexing in between, and Bison reports no conflicts (there is
no `%expect`). To stay that way it implements PaykanLang's grammar **without generics** (next
section); every other program is parsed exactly as `recursive-descent` parses it.

## Generics are not supported

**Generics.** User-defined generics are not supported: generic classes and functions
(`class Box<T>`, `fn first<T>`), generic types (`x: Box<int>`, `lib::Box<int>`) and generic
calls and constructions (`max<int>(a, b)`, `Box<int>(1)`, `lib::Box<int>(1)`). In an
expression, `name <` is either a comparison or the start of type arguments, which an LALR(1)
parser cannot tell apart with one token of lookahead. A program that uses generics is rejected
with one diagnostic, at the `<`, and nothing else:

```
prog.pkn:3:12: error: generics are not supported by the bison frontend; use --frontend=recursive-descent
```

Parse generic code with the default frontend, `--frontend=recursive-descent`.

The diagnostic comes from grammar rules that recognise a type-argument list by a shape no
comparison has (`<` after a declaration's name or in a type; `f < X > (`; `f < int,`,
`f < int[`, `f < int?`, `f < (int,` and the like). A generic call whose first type argument
has none of these shapes, such as `f<lib::T, U>(x)`, gets Bison's own syntax error instead,
and `f(a < b, c > (d))`, which `recursive-descent` reads as the generic call `a<b, c>(d)`, is
parsed as a call with two comparisons. A program that declares or uses a generic type first
gets the generics diagnostic there.

**Conversions are supported.** The builtin conversions keep their generic-call form,
`Str<int>(n)`, `int<Str>(s)`, `float<int>(i)`, ... (PaykanLang's `docs/grammar.md`,
"Conversion constructors"), as do `Str(x)`-style constructors and inferred conversions. The
scanner returns the names of the builtin types a conversion can target (`Str`, `int`, `Int`,
`float`, `Float`, `bool`, `Bool`, `char`) as a token of their own, so
`BUILTIN_TYPE '<' type '>' '(' arguments ')'` is an ordinary LALR(1) production: none of those
names can be a value (Sema rejects them as variable names), so their `<` is never a
comparison. They are still accepted wherever `recursive-descent` accepts them as names
(`class Str {}`, `fn int()`, `Str: int = 1`), so Sema reports those programs alike.

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
| `ParserTests.bison`, `SemaTests.bison` | PaykanLang's frontend-parameterized parser and Sema suites, parsed with `bison` (the module, loaded by the installation's plugin loader); every input is also parsed with `recursive-descent` and the ASTs compared. Includes the nesting-limit tests (`GrammarEdge.Nesting*`) but `NestingLimitIsTheSameOnEveryFrontend`, which nests a generic type (`NestingLimit` checks its other constructs). The tests that use generics, or inputs outside this frontend's grammar, are filtered out (below). |
| `FrontendTests.bison` | The fuzz smoke test (random and mutated input never crashes, hangs or leaks). Its in-process differential check over the whole samples corpus is filtered out; `FrontendDifferential` does the same check without the unsupported samples. |
| `InstalledPaykan.bison` | Disabled: it compares `--dump-ast` over the whole samples corpus and cannot skip a sample; `PluginListed` and `FrontendDifferential` check the same. |
| `PluginListed` | The installed `paykan --version` lists `frontend bison (built with PaykanLang <v>, compatible) [<module>]`. |
| `FrontendDifferential` | `paykan --dump-ast` with `recursive-descent` and with `bison` over every sample but the unsupported ones: same exit status, same AST ([`scripts/diff_frontends.py`](scripts/diff_frontends.py)). |
| `UnsupportedSamples` | Each unsupported sample, and each program of [`tests/generics`](tests/generics) (one per generic construct), is accepted by `recursive-descent` and rejected by `bison`: with generics, by the generics diagnostic alone, at a `<`; the others, by a syntax error first, never a crash ([`scripts/check_unsupported.py`](scripts/check_unsupported.py)). |
| `NestingLimit` | The nesting limit is `recursive-descent`'s for every construct of `GrammarEdge.NestingLimitIsTheSameOnEveryFrontend` but its generic type, and for conversions ([`scripts/nesting_limit.py`](scripts/nesting_limit.py)). |
| `BuiltWithMismatch` | Configuring with `-DPAYKAN_BISON_BUILT_WITH=<a version the installation does not accept>` fails with the compatibility error. |
| `SamplesFrontendParity` | Every runnable sample but the unsupported ones on the c backend with each frontend: same stdout, stderr and exit code, zero live heap blocks ([`scripts/samples_frontends.py`](scripts/samples_frontends.py)). |

The programs that use generics, or syntax outside this frontend's grammar, are left out of
the comparisons with `recursive-descent`, by explicit lists made from the files and tests on
which the two frontends differ:
[`tests/unsupported_samples.txt`](tests/unsupported_samples.txt) for the samples corpus (21
using generics, 8 outside the grammar), and
[`tests/UnsupportedTests.cmake`](tests/UnsupportedTests.cmake) for the tests of the
parser, Sema and frontend suites, which are filtered out with `GTEST_FILTER` because
`paykan_add_frontend_tests` has no exclusion option. When PaykanLang's corpus or suites
change, a listed sample that no longer exists fails the tests, and a new program using
generics or syntax outside the grammar shows up as a difference to add to a list.

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
src/                        Parser.ypp, Lexer.lpp, BisonFrontend.{h,cpp} (the driver and the
                            nesting limit), Plugin.cpp (the C plugin interface)
tests/CMakeLists.txt        the test suites above
tests/unsupported_samples.txt, tests/UnsupportedTests.cmake
                            the samples and suite tests this frontend leaves out
tests/generics/             one program per generic construct
scripts/                    diff_frontends.py, samples_frontends.py, check_unsupported.py,
                            nesting_limit.py, unsupported.py
```

The module is built with `-fexceptions -frtti` (Bison's `lalr1.cc` skeleton needs them); no
exception crosses the plugin interface.

## License

MIT, like PaykanLang; see [LICENSE](LICENSE).
