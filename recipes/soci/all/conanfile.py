import os
from collections import namedtuple
from conans import ConanFile, CMake, tools

class SociConan(ConanFile):
    name = "soci"
    settings = "os", "arch", "compiler", "build_type"
    description = "SOCI - The C++ Database Access Library"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://soci.sourceforge.net/"
    license = "BSL-1.0"
    topics = ("conan", "soci", "libraries", "cpp")

    backends = [
#     "db2",
      "empty",
#     "firebird",
      "mysql",
#     "odbc",
#     "oracle",
#     "postgresql",
      "sqlite3"
    ]

    options = {
        "shared": [True, False],
        "with_boost": [True, False],
    }
    options.update({"with_%s" % backend: [True, False] for backend in backends})

    default_options = {
        "shared": True,
        "with_boost": False
    }

    default_options.update({
      "with_empty"  : False,
      
      "with_sqlite3": True,
      "with_mysql": True
    })

    short_paths = True
    no_copy_source = True

    def requirements(self):
        if self.options.with_sqlite3:
            self.requires("sqlite3/3.30.1")
        if self.options.with_mysql:
            self.requires("mysql-connector-c/6.1.11")
        if self.options.with_boost:
            self.requires("boost/1.72.0")

    _source_subfolder = "source_subfolder"

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        url = self.conan_data["sources"][self.version]["url"]
        archive_name = os.path.basename(url)
        archive_name = os.path.splitext(archive_name)[0]
        os.rename("soci-%s" % archive_name, self._source_subfolder)
        
    def _dependency(self, name):
        return namedtuple('Dependency', ['root'])(
          root          = self.deps_cpp_info[name].rootpath,
        )

    def configure(self):
        if self.options.with_mysql:
            self.options["mysql-connector-c"].shared = True

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions["SOCI_SHARED"] = self.options.shared
        cmake.definitions["SOCI_STATIC"] = not self.options.shared

        cmake.definitions["CMAKE_CXX_STANDARD"] = self.settings.compiler.cppstd

        cmake.definitions["WITH_EMPTY"] = self.options.with_empty

        if self.options.with_sqlite3:
            sqlite3 = self._dependency('sqlite3')
            cmake.definitions["WITH_SQLITE3"] = "ON"
            cmake.definitions["SQLITE_ROOT_DIR"] = sqlite3.root

        if self.options.with_mysql:
            mysql = self._dependency('mysql-connector-c')
            cmake.definitions["WITH_MYSQL"] = "ON"
            os.environ["MYSQL_DIR"] = mysql.root

        cmake.configure(source_folder=self._source_subfolder)
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package_info(self):
        self.cpp_info.build_modules.append("cmake/SOCI.cmake")
        
        if self.options.with_boost:
          self.cpp_info.defines.append("-DSOCI_USE_BOOST")


    def package(self):
        cmake = self._configure_cmake()
        cmake.install()

