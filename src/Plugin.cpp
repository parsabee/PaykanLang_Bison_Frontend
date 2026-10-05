// Copyright (c) 2026 Parsa Bagheri
// SPDX-License-Identifier: MIT
//
// The plugin's C interface (PaykanLang's paykan/plugin_api.h): the one entry
// point `paykan_plugin_init` and the `bison` frontend's callbacks.  paykan
// loads the module at run time; a parse hands it the source text, and it
// returns the program in the AST interchange format
// (docs/plugins/ast-format.md in PaykanLang), printed from the AST the
// Bison parser built with the installed writer.  Syntax errors go through
// the host's diagnostics.  No exception leaves a callback.

#include "BisonFrontend.h"

#include "paykan/ast/Interchange.h"
#include "paykan/plugin_api.h"

#include <cstdlib>
#include <cstring>
#include <sstream>
#include <string>
#include <string_view>

namespace {

using namespace paykan;

const PaykanHost *host;

void report(PaykanSession *s, uint32_t level, size_t line, size_t column,
            const std::string &msg) {
  host->diagnostic(s, level, nullptr, static_cast<uint32_t>(line),
                   static_cast<uint32_t>(column), msg.data(), msg.size());
}

/// The parser's diagnostics, through the host.
void forward(PaykanSession *s, const sema::DiagEngine &diag) {
  for (const sema::Diagnostic &d : diag.getDiagnostics()) {
    uint32_t level = d.Level == sema::Diagnostic::Error ? PAYKAN_DIAG_ERROR
                     : d.Level == sema::Diagnostic::Warning
                         ? PAYKAN_DIAG_WARNING
                         : PAYKAN_DIAG_NOTE;
    report(s, level, d.Loc.getLineStart(), d.Loc.getColumnStart(), d.Message);
  }
}

int parse(void *, PaykanSession *s, const PaykanFrontendInput *in,
          PaykanFrontendOutput *out) {
  try {
    if (in->ast_format_version != PAYKAN_AST_FORMAT_VERSION) {
      report(s, PAYKAN_DIAG_ERROR, 0, 0,
             "the bison frontend writes AST format " +
                 std::to_string(PAYKAN_AST_FORMAT_VERSION) +
                 ", this paykan reads " +
                 std::to_string(in->ast_format_version));
      out->error_count = 1;
      return PAYKAN_ERROR;
    }
    ast::ASTContext ctx;
    std::ostringstream quiet; // reported through the host instead
    sema::DiagEngine diag(quiet);
    frontend::Options opts;
    opts.TraceParsing = in->trace_parsing != 0;
    opts.TraceScanning = in->trace_scanning != 0;
    frontend::bison::BisonFrontend parser;
    frontend::ParseResult r = parser.parse(
        in->filename, std::string_view(in->source, in->source_size), ctx, diag,
        opts);
    forward(s, diag);
    out->error_count = r.ErrorCount;
    if (r.ErrorCount || !r.Root)
      return PAYKAN_OK;
    std::ostringstream text;
    std::string error;
    if (!ast::interchange::write(*r.Root, text, error)) {
      report(s, PAYKAN_DIAG_ERROR, 0, 0, "cannot write the AST: " + error);
      out->error_count = 1;
      return PAYKAN_ERROR;
    }
    std::string ast = text.str();
    auto *buf = static_cast<char *>(std::malloc(ast.size() + 1));
    if (!buf)
      return PAYKAN_ERROR;
    std::memcpy(buf, ast.c_str(), ast.size() + 1);
    out->ast = buf;
    out->ast_size = ast.size();
    return PAYKAN_OK;
  } catch (...) { // nothing may unwind into paykan
    report(s, PAYKAN_DIAG_ERROR, 0, 0, "internal error in the bison frontend");
    out->error_count = 1;
    return PAYKAN_ERROR;
  }
}

void freeMemory(void *ptr) { std::free(ptr); }

const PaykanFrontend kFrontends[] = {{
    sizeof(PaykanFrontend), "bison", "the Bison/Flex LALR(1) parser", nullptr,
    &parse,
    nullptr, // --dump-tokens: not supported
}};

const PaykanPlugin kPlugin = {
    sizeof(PaykanPlugin),
    PAYKAN_PLUGIN_API_VERSION,
    PAYKAN_PLUGIN_BUILD_VERSION,
    "PaykanLang_Bison_Frontend",
    PAYKAN_BISON_VERSION,
    &freeMemory,
    0,
    nullptr,
    1,
    kFrontends,
};

} // namespace

PAYKAN_PLUGIN_EXPORT const PaykanPlugin *
paykan_plugin_init(const PaykanHost *h) {
  host = h;
  return &kPlugin;
}
