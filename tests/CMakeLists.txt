# tests/CMakeLists.txt
# ----------------------------------------------------------------------------
# The bison plugin against the installed PaykanLang.  Everything runs the
# plugin MODULE the way users get it: loaded by the installed `paykan`
# (PAYKAN_EXECUTABLE) with `--no-plugins --plugin=<module>`, or in process by
# that installation's own plugin loader.
#
#   ParserTests.bison, SemaTests.bison, FrontendTests.bison
#       PaykanLang's frontend-parameterized parser and Sema suites (the
#       nesting-limit tests included, GrammarEdgeTests) and its fuzz smoke
#       test, built from the installation's test support
#       (paykan_add_frontend_tests), with the module loaded.  Every parse is
#       compared with the recursive-descent frontend's.  The tests whose
#       programs use generics, or syntax outside this frontend's grammar,
#       are filtered out (tests/UnsupportedTests.cmake), and so is the
#       suite's in-process differential check over the whole samples corpus
#       (FrontendDifferential replaces it).
#   InstalledPaykan.bison
#       (from paykan_add_frontend_tests) the installed paykan's --dump-ast
#       with bison equals recursive-descent's over the WHOLE samples corpus:
#       disabled, as it cannot skip the samples this frontend leaves out;
#       PluginListed and FrontendDifferential check the same.
#   PluginListed
#       the installed paykan lists bison as compatible, with its file.
#   FrontendDifferential
#       `paykan --dump-ast` with recursive-descent and with bison over the
#       installed samples corpus but tests/unsupported_samples.txt
#       (scripts/diff_frontends.py).
#   UnsupportedSamples
#       each sample of tests/unsupported_samples.txt, and each program of
#       tests/generics (one per generic construct), is accepted by
#       recursive-descent and rejected by bison: a program using generics
#       with the generics diagnostic alone, at a '<'; one outside the
#       grammar with a syntax error (scripts/check_unsupported.py).
#   NestingLimit
#       the nesting limit is the same as recursive-descent's for every
#       construct but generics (scripts/nesting_limit.py).
#   SamplesFrontendParity
#       every runnable sample but tests/unsupported_samples.txt run on the c
#       backend with each frontend: same stdout, stderr and exit code, zero
#       live heap blocks (scripts/samples_frontends.py).
#   BuiltWithMismatch
#       configuring with a build version the installation does not accept
#       fails (tests/BuiltWithMismatch.cmake).
# ----------------------------------------------------------------------------

# -- GoogleTest ---------------------------------------------------------------
# FETCHCONTENT_SOURCE_DIR_GOOGLETEST=<dir> (no download), an installed GTest,
# or the pinned release.
include(FetchContent)
FetchContent_Declare(googletest
    URL                        "https://github.com/google/googletest/archive/refs/tags/v${GTEST_VERSION}.tar.gz"
    URL_HASH                   SHA256=7b42b4d6ed48810c5362c265a17faebe90dc2373c885e5216439d37927f02926
    SOURCE_DIR                 ${GTEST_INSTALL_DIR}
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    FIND_PACKAGE_ARGS          1.11 CONFIG NAMES GTest
)
set(INSTALL_GTEST OFF)
FetchContent_MakeAvailable(googletest)

if(NOT COMMAND paykan_add_frontend_tests)
    message(FATAL_ERROR "The Paykan installation has no frontend test support "
                        "(paykan_add_frontend_tests); build PaykanLang with "
                        "-DPAYKAN_INSTALL_TEST_SUPPORT=ON (the default), or "
                        "configure with -DPAYKAN_BISON_BUILD_TESTS=OFF")
endif()
if(NOT "recursive-descent" IN_LIST PAYKAN_FRONTENDS)
    message(FATAL_ERROR "The tests compare the bison frontend with the "
                        "installation's recursive-descent frontend, which it lacks")
endif()

paykan_add_frontend_tests(bison PLUGIN paykan_frontend_bison)

# The suites' tests that this frontend leaves out (generics, and inputs
# outside its grammar; README) are filtered out: paykan_add_frontend_tests has
# no exclusion option of its own, so GoogleTest's GTEST_FILTER does it.
include(${CMAKE_CURRENT_SOURCE_DIR}/UnsupportedTests.cmake)
foreach(suite IN ITEMS Parser Sema Frontend)
    string(TOUPPER ${suite} upper)
    set(excluded ${PAYKAN_BISON_GENERICS_${upper}_TESTS}
                 ${PAYKAN_BISON_SYNTAX_${upper}_TESTS}
                 ${PAYKAN_BISON_CORPUS_${upper}_TESTS})
    if(excluded)
        list(JOIN excluded ":" filter)
        set_property(TEST ${suite}Tests.bison APPEND PROPERTY
            ENVIRONMENT "GTEST_FILTER=-${filter}")
    endif()
endforeach()
# Over the whole corpus, with no way to skip a sample; FrontendDifferential
# and PluginListed check the same.
set_tests_properties(InstalledPaykan.bison PROPERTIES DISABLED TRUE)

# The samples this frontend leaves out.
set(UNSUPPORTED_SAMPLES ${CMAKE_CURRENT_SOURCE_DIR}/unsupported_samples.txt)

find_package(Python3 REQUIRED COMPONENTS Interpreter)

# The installed paykan with only this plugin loaded.
set(PAYKAN_WITH_BISON --paykan-arg=--no-plugins
    --paykan-arg=--plugin=$<TARGET_FILE:paykan_frontend_bison>)

add_test(NAME PluginListed
    COMMAND ${PAYKAN_EXECUTABLE} --no-plugins
            --plugin=$<TARGET_FILE:paykan_frontend_bison> --version)
set_tests_properties(PluginListed PROPERTIES
    PASS_REGULAR_EXPRESSION
    "\nfrontend bison \\(built with PaykanLang [^,\n]+, compatible\\) \\[[^]\n]*libpaykan_frontend_bison[^]\n]*\\]\n"
    FAIL_REGULAR_EXPRESSION "rejected plugin|incompatible")

add_test(NAME FrontendDifferential
    COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/scripts/diff_frontends.py
            --paykan ${PAYKAN_EXECUTABLE} ${PAYKAN_WITH_BISON}
            --frontends recursive-descent,bison
            --exclude ${UNSUPPORTED_SAMPLES}
            ${PAYKAN_SAMPLES_DIR})

add_test(NAME UnsupportedSamples
    COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/scripts/check_unsupported.py
            --paykan ${PAYKAN_EXECUTABLE} ${PAYKAN_WITH_BISON}
            --samples ${PAYKAN_SAMPLES_DIR}
            --list ${UNSUPPORTED_SAMPLES}
            --generics ${CMAKE_CURRENT_SOURCE_DIR}/generics)

add_test(NAME NestingLimit
    COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/scripts/nesting_limit.py
            --paykan ${PAYKAN_EXECUTABLE} ${PAYKAN_WITH_BISON})

if("c" IN_LIST PAYKAN_BACKENDS)
    add_test(NAME SamplesFrontendParity
        COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/scripts/samples_frontends.py
                --paykan ${PAYKAN_EXECUTABLE} ${PAYKAN_WITH_BISON}
                --samples ${PAYKAN_SAMPLES_DIR}
                --exclude ${UNSUPPORTED_SAMPLES}
                --backend c
                --frontend recursive-descent --frontend bison)
endif()

# The configure-time compatibility check: a plugin checked as built with a
# version the installation does not accept fails to configure.
add_test(NAME BuiltWithMismatch
    COMMAND ${CMAKE_COMMAND}
            -DSOURCE_DIR=${PROJECT_SOURCE_DIR}
            -DWORK_DIR=${CMAKE_CURRENT_BINARY_DIR}/built-with-mismatch
            -DGENERATOR=${CMAKE_GENERATOR}
            "-DPREFIX_PATH=${CMAKE_PREFIX_PATH}"
            "-DLLVM_DIR=${LLVM_DIR}"
            -P ${CMAKE_CURRENT_SOURCE_DIR}/BuiltWithMismatch.cmake)
