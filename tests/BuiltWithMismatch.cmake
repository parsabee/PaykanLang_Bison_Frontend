# Configure this project in a scratch directory with PAYKAN_BISON_BUILT_WITH
# set to a version the installed PaykanLang does not accept: the configure
# must fail with paykan_add_frontend_plugin's incompatibility error
# (parsabee/PaykanLang#103).
#
#   cmake -DSOURCE_DIR=... -DWORK_DIR=... -DGENERATOR=...
#         -DPREFIX_PATH=... [-DLLVM_DIR=...] -P tests/BuiltWithMismatch.cmake
cmake_minimum_required(VERSION 3.24)

file(REMOVE_RECURSE ${WORK_DIR})
set(args -S ${SOURCE_DIR} -B ${WORK_DIR} -G ${GENERATOR}
    "-DCMAKE_PREFIX_PATH=${PREFIX_PATH}"
    -DPAYKAN_BISON_BUILT_WITH=0.0.0-never
    -DPAYKAN_BISON_BUILD_TESTS=OFF)
if(LLVM_DIR)
    list(APPEND args -DLLVM_DIR=${LLVM_DIR})
endif()
execute_process(COMMAND ${CMAKE_COMMAND} ${args}
    RESULT_VARIABLE rc OUTPUT_VARIABLE out ERROR_VARIABLE err)
file(REMOVE_RECURSE ${WORK_DIR})
if(rc EQUAL 0)
    message(FATAL_ERROR "configure accepted a plugin built with 0.0.0-never")
endif()
if(NOT err MATCHES "is incompatible: built with[ \n]+PaykanLang 0.0.0-never")
    message(FATAL_ERROR "configure failed, but not with the incompatibility error:\n${err}")
endif()
message(STATUS "a plugin built with 0.0.0-never is rejected at configure time")
