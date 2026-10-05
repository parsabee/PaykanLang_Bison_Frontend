# tests/CMakeLists.txt
# ----------------------------------------------------------------------------
# The bison plugin against the installed PaykanLang.  Everything runs the
# plugin MODULE the way users get it: loaded by the installed `paykan`
# (PAYKAN_EXECUTABLE) with `--no-plugins --plugin=<module>`, or in process by
# that installation's own plugin loader.
#
#   ParserTests.bison, SemaTests.bison, FrontendTests.bison
#       PaykanLang's frontend-parameterized parser and Sema suites (the
#       nesting-limit tests included, GrammarEdgeTests), its fuzz smoke test
#       and its in-process differential check over the samples corpus, built
#       from the installation's test support (paykan_add_frontend_tests),
#       with the module loaded.  Every parse is compared with the
#       recursive-descent frontend's.
#   InstalledPaykan.bison
#       the installed paykan lists the plugin, and its --dump-ast with bison
#       equals recursive-descent's over the samples corpus (from
#       paykan_add_frontend_tests).
#   PluginListed
#       the installed paykan lists bison as compatible, with its file.
#   FrontendDifferential
#       `paykan --dump-ast` with recursive-descent and with bison over the
#       installed samples corpus (scripts/diff_frontends.py).
#   SamplesFrontendParity
#       every runnable sample run on the c backend with each frontend: same
#       stdout, stderr and exit code, zero live heap blocks
#       (scripts/samples_frontends.py).
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
            ${PAYKAN_SAMPLES_DIR})

if("c" IN_LIST PAYKAN_BACKENDS)
    add_test(NAME SamplesFrontendParity
        COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/scripts/samples_frontends.py
                --paykan ${PAYKAN_EXECUTABLE} ${PAYKAN_WITH_BISON}
                --samples ${PAYKAN_SAMPLES_DIR}
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
