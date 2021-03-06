from conans import ConanFile, CMake, tools
from conans.tools import Version
from conans.errors import ConanInvalidConfiguration
import os


class RocksDB(ConanFile):
    name = "rocksdb"
    homepage = "https://github.com/facebook/rocksdb"
    license = "GPL-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    description = "A library that provides an embeddable, persistent key-value store for fast storage"
    topics = ("conan", "rocksdb", "database",
              "leveldb", "facebook", "key-value")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "lite": [True, False],
        "with_gflags": [True, False],
        "with_snappy": [True, False],
        "with_lz4": [True, False],
        "with_zlib": [True, False],
        "with_zstd": [True, False],
        "with_tbb": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "lite": False,
        "with_snappy": False,
        "with_lz4": False,
        "with_zlib": False,
        "with_zstd": False,
        "with_gflags": False,
        "with_tbb": False
    }
    exports_sources = ["CMakeLists.txt"]
    generators = ["cmake"]
    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.settings.os == "Windows" and \
           self.settings.compiler == "Visual Studio" and \
           Version(self.settings.compiler.version) < "15":
            raise ConanInvalidConfiguration("Rocksdb requires Visual Studio 15 or later.")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + os.path.basename(self.conan_data["sources"][self.version]["url"]).split(".")[0]
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_cmake(self):
        if not self._cmake:
            self._cmake = CMake(self)
        self._cmake.definitions["WITH_MD_LIBRARY"] = self.settings.compiler == "Visual Studio" and "MD" in self.settings.compiler.runtime
        self._cmake.definitions["ROCKSDB_INSTALL_ON_WINDOWS"] = self.settings.os == "Windows"
        self._cmake.definitions["ROCKSDB_LITE"] = self.options.lite
        self._cmake.definitions["WITH_TESTS"] = False
        self._cmake.definitions["WITH_TOOLS"] = False
        self._cmake.definitions["WITH_FOLLY_DISTRIBUTED_MUTEX"] = False
        self._cmake.definitions["WITH_GFLAGS"] = self.options.with_gflags
        self._cmake.definitions["WITH_SNAPPY"] = self.options.with_snappy
        self._cmake.definitions["WITH_LZ4"] = self.options.with_lz4
        self._cmake.definitions["WITH_ZLIB"] = self.options.with_zlib
        self._cmake.definitions["WITH_ZSTD"] = self.options.with_zstd
        self._cmake.definitions["WITH_TBB"] = self.options.with_tbb
        self._cmake.definitions["ROCKSDB_BUILD_SHARED"] = self.options.shared
        self._cmake.definitions["WITH_BENCHMARK_TOOLS"] = False
        # not available yet in CCI
        self._cmake.definitions["WITH_JEMALLOC"] = False
        self._cmake.definitions["WITH_NUMA"] = False

        self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def requirements(self):
        if self.options.with_gflags:
            self.requires("gflags/2.2.2")
        if self.options.with_snappy:
            self.requires("snappy/1.1.7")
        if self.options.with_lz4:
            self.requires("lz4/1.9.2")
        if self.options.with_zlib:
            self.requires("zlib/1.2.11")
        if self.options.with_zstd:
            self.requires("zstd/1.3.8")
        if self.options.with_tbb:
            self.requires("tbb/2019_u9")

    def package(self):
        self.copy("COPYING", dst="licenses", src=self._source_subfolder)
        self.copy("LICENSE*", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
        tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "RocksDB"
        self.cpp_info.names["cmake_find_package_multi"] = "RocksDB"
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Windows":
            self.cpp_info.system_libs = ["Shlwapi.lib", "Rpcrt4.lib"]
            if self.options.shared:
                self.cpp_info.defines = ["ROCKSDB_DLL", "ROCKSDB_LIBRARY_EXPORTS"]
        elif self.settings.os == "Linux":
            self.cpp_info.system_libs = ["pthread", "m"]
        if self.options.lite:
            self.cpp_info.defines.append("ROCKSDB_LITE")
