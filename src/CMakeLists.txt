# src/CMakeLists.txt
# ----------------------------------------------------------------------------
# paykan_frontend_bison -- the Bison/Flex frontend plugin.
#
# This is the ONLY target that compiles with -fexceptions and -frtti, which
# are required by Bison's lalr1.cc skeleton (throw/catch + typeid).  No
# exception crosses the frontend interface: BisonFrontend::parse catches
# everything and reports a diagnostic.  The test executables and the driver
# use PaykanLang's flags (Paykan::compile_options: -fno-exceptions -fno-rtti).
# ----------------------------------------------------------------------------

# -- Generated source paths ---------------------------------------------------
# Bison and Flex write into the binary dir so the source tree stays clean.
set(PARSER_YPP   ${CMAKE_CURRENT_SOURCE_DIR}/Parser.ypp)
set(LEXER_LPP    ${CMAKE_CURRENT_SOURCE_DIR}/Lexer.lpp)

set(PARSER_GEN_DIR ${CMAKE_CURRENT_BINARY_DIR})
file(MAKE_DIRECTORY ${PARSER_GEN_DIR})

set(PARSER_CPP   ${PARSER_GEN_DIR}/Parser.ypp.cpp)
set(PARSER_HPP   ${PARSER_GEN_DIR}/Parser.ypp.h)
set(LOCATION_HPP ${PARSER_GEN_DIR}/location.hh)

set(LEXER_CPP    ${PARSER_GEN_DIR}/Lexer.lpp.cpp)

# -- Bison --------------------------------------------------------------------
add_custom_command(
    OUTPUT  ${PARSER_CPP} ${PARSER_HPP} ${LOCATION_HPP}
    COMMAND ${BISON_EXECUTABLE}
            --defines=${PARSER_HPP}
            --output=${PARSER_CPP}
            ${PARSER_YPP}
    DEPENDS ${PARSER_YPP} bison_ext
    COMMENT "Bison: Parser.ypp -> Parser.ypp.cpp + Parser.ypp.h"
    VERBATIM
)

# -- Flex ---------------------------------------------------------------------
add_custom_command(
    OUTPUT  ${LEXER_CPP}
    COMMAND ${FLEX_EXECUTABLE}
            --outfile=${LEXER_CPP}
            ${LEXER_LPP}
    DEPENDS ${LEXER_LPP} flex_ext ${PARSER_HPP}   # lexer includes the parser header
    COMMENT "Flex: Lexer.lpp -> Lexer.lpp.cpp"
    VERBATIM
)

# -- Plugin library -----------------------------------------------------------
# TODO(#103): build this with PaykanLang's plugin helper once it ships (see
# the top-level CMakeLists.txt).
add_library(paykan_frontend_bison STATIC
    ${PARSER_CPP}
    ${LEXER_CPP}
    BisonFrontend.cpp
)

target_include_directories(paykan_frontend_bison
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}     # BisonFrontend.h (private)
            ${PARSER_GEN_DIR}               # Parser.ypp.h, location.hh (private)
)

# The installed frontend interface: paykan/Frontend.h, AST.h, ASTContext.h,
# DiagEngine.h (include/paykan/compiler of the installation).
target_link_libraries(paykan_frontend_bison
    PUBLIC  Paykan::frontend
)

# Bison's lalr1.cc uses throw/catch and typeid: RTTI and exceptions here
# only.  Our own flags instead of Paykan::compile_options (which carries
# -fno-rtti -fno-exceptions).
target_compile_options(paykan_frontend_bison PRIVATE
    -Wall -Wextra -Wpedantic -Werror
    -fexceptions -frtti
    $<$<CONFIG:Debug>:-g -O0>
    $<$<CONFIG:Release>:-O3>
)
# Bison's lalr1.cc skeleton sets-but-never-reads yynerrs_ (it tracks error
# count internally but only uses the value to set the return code).
# Suppress the resulting warning on the generated source only.
set_source_files_properties(${PARSER_CPP} PROPERTIES
    COMPILE_OPTIONS "-Wno-unused-but-set-variable"
)
