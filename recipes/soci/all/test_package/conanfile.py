from conans.model.conan_file import ConanFile, tools
from conans import CMake
import os
import sys


class DefaultNameConan(ConanFile):
    settings = "os", "compiler", "arch", "build_type"
    generators = "cmake"

    def build(self):
        cmake = CMake(self)

        cmake.definitions["CMAKE_CXX_STANDARD"] = self.settings.compiler.cppstd

        if self.options["soci"].with_sqlite3:
            cmake.definitions["WITH_SQLITE3"] = "TRUE"

        cmake.configure()
        cmake.build()


    def test(self):
        if tools.cross_building(self.settings):
            return
        bt = self.settings.build_type
        self.run('ctest --output-on-error -C %s' % bt, run_environment=True)
