# tests/CMakeLists.txt
# ----------------------------------------------------------------------------
# The bison frontend against the installed PaykanLang:
#
#   ParserTests.bison, SemaTests.bison, FrontendTests.bison
#       PaykanLang's frontend-parameterized parser and Sema suites (the
#       nesting-limit tests included, GrammarEdgeTests), its fuzz smoke test
#       and its in-process differential check over the samples corpus, built
#       from the installation's test support (paykan_add_frontend_tests).
#       Every parse is compared with the recursive-descent frontend's.
#   FrontendDifferential
#       `paykan --dump-ast` with recursive-descent and with bison over the
#       installed samples corpus (scripts/diff_frontends.py).
#   SamplesFrontendParity
#       every runnable sample run on the c backend with each frontend: same
#       stdout, stderr and exit code, zero live heap blocks
#       (scripts/samples_frontends.py).
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

paykan_add_frontend_tests(bison PLUGINS paykan_frontend_bison)

find_package(Python3 REQUIRED COMPONENTS Interpreter)

add_test(NAME FrontendDifferential
    COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/scripts/diff_frontends.py
            --paykan $<TARGET_FILE:paykan>
            --frontends recursive-descent,bison
            ${PAYKAN_SAMPLES_DIR})

if("c" IN_LIST PAYKAN_BACKENDS)
    add_test(NAME SamplesFrontendParity
        COMMAND ${Python3_EXECUTABLE} ${PROJECT_SOURCE_DIR}/scripts/samples_frontends.py
                --paykan $<TARGET_FILE:paykan>
                --samples ${PAYKAN_SAMPLES_DIR}
                --backend c
                --frontend recursive-descent --frontend bison)
endif()
