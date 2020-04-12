PROJECT(SociTest)
cmake_minimum_required(VERSION 3.0)
enable_testing()

set(CMAKE_BUILD_TYPE "Debug")

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)

CONAN_BASIC_SETUP()

conan_include_build_modules()

if (WITH_EMPTY)
    add_executable(empty_exe soci.cpp)
    target_compile_definitions(empty_exe PUBLIC BACKEND_EMPTY)
    target_link_libraries(empty_exe SOCI::soci_core SOCI::soci_empty)
    add_test(
        NAME TestSociEmpty
        COMMAND empty_exe
    )

endif()

if (WITH_SQLITE3)
    add_executable(sqlite3_exe soci.cpp)
    target_compile_definitions(sqlite3_exe PUBLIC BACKEND_SQLITE3)
    target_link_libraries(sqlite3_exe SOCI::soci_core SOCI::soci_sqlite3)
    add_test(
        NAME TestSociSqlite3
        COMMAND sqlite3_exe
    )
endif()

