# PaykanLang_Bison_Frontend
# ----------------------------------------------------------------------------
# The Bison/Flex frontend for PaykanLang, as an out-of-tree plugin built
# against an installed PaykanLang (find_package(Paykan)).  Produces:
#
#   paykan_frontend_bison   the frontend plugin (a static library that
#                           registers the `bison` frontend)
#   bin/paykan              a paykan driver with every plugin of the
#                           installation plus this one: --frontend=bison
#
# Only the installed PaykanLang headers, libraries and CMake package are used.
#
#   cmake -B build -DCMAKE_PREFIX_PATH=<paykan-prefix>
#   cmake --build build
#   ctest --test-dir build
# ----------------------------------------------------------------------------
cmake_minimum_required(VERSION 3.24)

project(PaykanLang_Bison_Frontend
    VERSION 0.1.0
    DESCRIPTION "The Bison/Flex frontend plugin for PaykanLang"
    LANGUAGES C CXX
)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Debug CACHE STRING "Build type" FORCE)
endif()
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# -- PaykanLang ---------------------------------------------------------------
# The plugin interfaces are not yet stable across PaykanLang minor releases,
# so the plugin is built against the 0.1 series only (PaykanConfigVersion is
# SameMinorVersion).  -DCMAKE_PREFIX_PATH=<prefix> names the installation;
# one built with the llvm backend also needs -DLLVM_DIR.
find_package(Paykan 0.1 REQUIRED)
message(STATUS "Paykan ${Paykan_VERSION}: frontends ${PAYKAN_FRONTENDS}, backends ${PAYKAN_BACKENDS}")

# Plugin compatibility (parsabee/PaykanLang#103): the library is built with
# paykan_add_frontend_plugin, which fails here unless the installed PaykanLang
# accepts plugins built with this version (PAYKAN_PLUGIN_COMPATIBLE_VERSIONS);
# the registration macro records the same version for the check paykan makes
# at run time.  PAYKAN_BISON_BUILT_WITH pins the version checked at configure
# time (default: the installation's own, PAYKAN_TOOLCHAIN_VERSION).
if(NOT COMMAND paykan_add_frontend_plugin)
    message(FATAL_ERROR "The installed PaykanLang (${Paykan_DIR}) has no "
                        "paykan_add_frontend_plugin: it predates the plugin "
                        "compatibility check (parsabee/PaykanLang#103)")
endif()
set(PAYKAN_BISON_BUILT_WITH "" CACHE STRING
    "The PaykanLang version the plugin is checked as built with (default: the installation's)")
message(STATUS "PaykanLang ${PAYKAN_TOOLCHAIN_VERSION} accepts plugins built with "
               "${PAYKAN_PLUGIN_COMPATIBLE_VERSIONS}")

# -- Bison and Flex -----------------------------------------------------------
# Built from source into <build>/third-party on the first configure (needs
# GNU m4 and a C compiler); reused afterwards.
set(BISON_VERSION "3.8")
set(FLEX_VERSION  "2.6.4")
set(GTEST_VERSION "1.15.2")
set(THIRD_PARTY_DIR   ${CMAKE_BINARY_DIR}/third-party)
set(BISON_INSTALL_DIR ${THIRD_PARTY_DIR}/bison)
set(FLEX_INSTALL_DIR  ${THIRD_PARTY_DIR}/flex)
set(GTEST_INSTALL_DIR ${THIRD_PARTY_DIR}/gtest)
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
include(BisonFlexSetup)     # -> BISON_EXECUTABLE, FLEX_EXECUTABLE, bison_ext, flex_ext

# -- The plugin and the driver ------------------------------------------------
add_subdirectory(src)

# The installation's driver plus the bison frontend.  Its default frontend
# stays the installation's (recursive-descent); --frontend=bison selects this
# one.
paykan_add_driver(paykan PLUGINS paykan_frontend_bison)

include(GNUInstallDirs)
install(TARGETS paykan RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})

# -- Tests ----------------------------------------------------------------------
option(PAYKAN_BISON_BUILD_TESTS "Build the test suite (needs GoogleTest)" ${PROJECT_IS_TOP_LEVEL})
if(PAYKAN_BISON_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
