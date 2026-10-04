# PaykanLang_Bison_Frontend
# ----------------------------------------------------------------------------
# The Bison/Flex frontend for PaykanLang, as a plugin that the INSTALLED
# `paykan` loads at run time (PaykanLang#141).  Produces:
#
#   libpaykan_frontend_bison.so (.dylib)   the `bison` frontend: a loadable
#                           module with PaykanLang's C plugin interface;
#                           `cmake --install` puts it into the installation's
#                           plugin directory (PAYKAN_PLUGIN_INSTALL_DIR)
#
#   cmake -B build -DCMAKE_PREFIX_PATH=<paykan-prefix>
#   cmake --build build
#   ctest --test-dir build
#   cmake --install build          # then: paykan --frontend=bison program.pkn
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

# Plugin compatibility (parsabee/PaykanLang#103): the module is built with
# paykan_add_frontend_plugin, which fails here unless the installed PaykanLang
# accepts plugins built with this version (PAYKAN_PLUGIN_COMPATIBLE_VERSIONS);
# the plugin's descriptor declares the same version for the check paykan
# makes when it loads the module.  PAYKAN_BISON_BUILT_WITH pins the version
# (default: the installation's own, PAYKAN_TOOLCHAIN_VERSION).
if(NOT COMMAND paykan_add_frontend_plugin OR NOT PAYKAN_PLUGIN_API_VERSION)
    message(FATAL_ERROR "The installed PaykanLang (${Paykan_DIR}) predates "
                        "loadable plugins (parsabee/PaykanLang#141): it has no "
                        "C plugin interface (PAYKAN_PLUGIN_API_VERSION)")
endif()
message(STATUS "PaykanLang plugin API ${PAYKAN_PLUGIN_API_VERSION}; plugins "
               "install into ${PAYKAN_PLUGIN_INSTALL_DIR}")
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

# -- The plugin -----------------------------------------------------------------
add_subdirectory(src)

# Into the installation's plugin directory, where its `paykan` finds it:
# `paykan --frontend=bison`.  (The default frontend stays recursive-descent.)
paykan_install_plugin(paykan_frontend_bison)

# -- Tests ----------------------------------------------------------------------
option(PAYKAN_BISON_BUILD_TESTS "Build the test suite (needs GoogleTest)" ${PROJECT_IS_TOP_LEVEL})
if(PAYKAN_BISON_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
