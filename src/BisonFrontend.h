// Copyright (c) 2026 Parsa Bagheri
// SPDX-License-Identifier: MIT
// The Bison/Flex frontend plugin: internals shared by the grammar actions,
// the scanner, BisonFrontend.cpp and Plugin.cpp.  Private to this library.
//
// Inside the plugin the parser builds PaykanLang's own AST (ast::ASTContext,
// from the installed headers and static libraries linked into the module);
// Plugin.cpp prints it in the AST interchange format for paykan.  Across the
// boundary to paykan there is only the C interface of paykan/plugin_api.h
// and that text.

#pragma once

#include "AST.h"
#include "ASTContext.h"
#include "DiagEngine.h"
#include "Parser.ypp.h"
#include "paykan/Frontend.h"

#include <string>
#include <string_view>
#include <vector>

namespace paykan::frontend::bison {
class BisonFrontend;
}

// Flex needs this macro for our custom driver.  The Flex scanner is exposed as
// yylex_raw; the parser calls yylex (BisonFrontend.cpp), which hands it each
// token exactly as Flex scanned it, in order, after counting it towards the
// nesting limit.  There is no token lookahead or re-lexing: the scanner is
// plain Flex and the grammar plain LALR(1).
#define YY_DECL                                                                \
  yy::parser::symbol_type yylex_raw(paykan::frontend::bison::BisonFrontend &drv)
YY_DECL;

/// Parser entry point: yylex_raw, with each token counted by trackNesting.
yy::parser::symbol_type yylex(paykan::frontend::bison::BisonFrontend &drv);

using namespace paykan::ast;

namespace paykan::frontend::bison {

/// The Bison/Flex parser.  One parse at a time per instance; the members
/// are the state the generated parser and scanner actions reach through
/// `drv`.  Plugin.cpp exposes it to paykan through the C plugin interface.
class BisonFrontend {
public:
  /// Parse @p source (the text of @p filename) into @p ctx, reporting every
  /// syntax error through @p diag.  Nothing escapes: exceptions become
  /// diagnostics.
  ParseResult parse(std::string_view filename, std::string_view source,
                    ast::ASTContext &ctx, sema::DiagEngine &diag,
                    const Options &opts);

  // -- State used by the generated parser and scanner ----------------------

  /// Arena that owns all AST nodes created during parsing (the caller's).
  ast::ASTContext *Ctx = nullptr;

  /// Root of the parsed AST (owned by *Ctx).
  TranslationUnit *Root = nullptr;

  /// The token's location used by the scanner.
  yy::location Location;

  /// The name of the file being parsed (Location points at it).
  std::string CurFile;

  /// Number of syntax errors encountered during parsing.
  unsigned ErrorCount = 0;

  /// Diagnostic engine every syntax error is routed through.
  sema::DiagEngine *Diags = nullptr;

  /// Whether to generate parser / scanner debug traces.
  bool TraceParsing = false;
  bool TraceScanning = false;

  /// The nesting tracker (BisonFrontend.cpp): enforces frontend::kMaxNesting
  /// over the token stream the parser reads, counting what the
  /// recursive-descent parser counts.  One NestLevel per open bracket (the
  /// file itself is the outermost).
  struct NestLevel {
    yy::parser::symbol_kind_type Closer; ///< the token that closes it
    unsigned Weight; ///< 1 for a bracket, 0 for an if/while condition
    unsigned Prefix; ///< prefix operators of the operand being read
    /// Conditional expressions open at this level, innermost last: 'c' in
    /// the condition, 't' in the then-branch, 'e' in the else-branch.
    std::string Ternaries;
  };
  std::vector<NestLevel> Nesting;
  /// Sum of the levels' Weight + Prefix + Ternaries.size().
  unsigned NestDepth = 0;
  /// The kind of the previous token (S_YYEOF before the first), and whether
  /// it was an `else` of an if statement.
  yy::parser::symbol_kind_type PrevKind = yy::parser::symbol_kind::S_YYEOF;
  bool PrevWasStmtElse = false;
  /// Whether the last `if` began a conditional expression.
  bool LastIfWasTernary = false;
  /// Thrown by the yylex wrapper when the input nests too deeply; parse()
  /// reports it and gives up (Bison's error recovery cannot resynchronise
  /// inside such a construct).
  struct NestingTooDeep {
    yy::location Loc;
  };
  /// Account for @p tok, the next token the parser reads; throws
  /// NestingTooDeep past the limit.
  void trackNesting(const yy::parser::symbol_type &tok);

  /// Scanner setup over @p source (Lexer.lpp) and teardown.
  void scanBegin(std::string_view source);
  void scanEnd();
};

/// The diagnostic for a generic declaration, type or call (Parser.ypp,
/// "Unsupported constructs"; README, "Generics and `mov` are not supported").
inline constexpr const char *kGenericsUnsupported =
    "generics are not supported by the bison frontend; use "
    "--frontend=recursive-descent";

/// Build the ImportDecl for `import [::]a::b::name [as alias];`.  The path is
/// split at its last "::" into the base path ("a::b", empty when there is no
/// separator) and the module name ("name").
inline ImportDecl *makeSingleImport(ASTContext &C, SourceLocation loc,
                                    const std::string &path,
                                    const std::string &alias, bool isSystem) {
  auto sep = path.rfind("::");
  std::string base = (sep == std::string::npos) ? "" : path.substr(0, sep);
  std::string name = (sep == std::string::npos) ? path : path.substr(sep + 2);
  return C.make<ImportDecl>(
      loc, C.intern(base), isSystem,
      std::vector<ImportDecl::Module>{{&C.intern(name), &C.intern(alias)}});
}

/// Build the ImportDecl for `import [::]base::{a, b as c};` (base may be
/// empty for `import ::{...};`).  Each (name, alias) pair becomes one module.
inline ImportDecl *
makeImportList(ASTContext &C, SourceLocation loc, const std::string &base,
               const std::vector<std::pair<std::string, std::string>> &mods,
               bool isSystem) {
  std::vector<ImportDecl::Module> ms;
  ms.reserve(mods.size());
  for (const auto &[name, alias] : mods)
    ms.push_back({&C.intern(name), &C.intern(alias)});
  return C.make<ImportDecl>(loc, C.intern(base), isSystem, std::move(ms));
}

} // namespace paykan::frontend::bison
