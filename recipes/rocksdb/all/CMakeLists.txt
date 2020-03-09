cmake_minimum_required(VERSION 2.8.12)
PROJECT(conancmakewrapper)

include("conanbuildinfo.cmake")
CONAN_BASIC_SETUP()

if (WIN32 AND MSVC AND BUILD_SHARED_LIBS)
    set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)
    set(WINDOWS_EXPORT_ALL_SYMBOLS ON)
endif()

add_subdirectory("source_subfolder")
