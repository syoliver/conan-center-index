import os
from conans import ConanFile, tools, CMake


class LibRdKafka(ConanFile):
    name = "librdkafka"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/edenhill/librdkafka"
    description = "The Apache Kafka C/C++ library"
    topics = ("conan", "apache", "kafka", "protocol", "producer", "consumer")
    settings = "os", "arch", "compiler", "build_type"
    license = "BSD 2-Clause"
    generators = "cmake", "cmake_find_package"
    exports_sources = ["CMakeLists.txt", "patches/**"]

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_ssl": [True, False],
        "with_lz4": [True, False],
        "with_zlib": [True, False],
        "with_zstd": [True, False],
        "with_plugins": [True, False],
        "with_sasl": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_ssl": True,
        "with_lz4": True,
        "with_zlib": True,
        "with_zstd": True,
        "with_plugins": True,
        "with_sasl": True
    }

    _cmake = None

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename(
            "librdkafka-{}".format(self.version),
            self._source_subfolder
        )

    def requirements(self):
        if self.options.with_zlib:
            self.requires("zlib/1.2.11")
        if self.options.with_zstd:
            self.requires("zstd/1.4.4")
        self.requires("lz4/1.9.2")
        self.requires("openssl/1.1.1g")
          

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake
        self._cmake = CMake(self)
        self._cmake.definitions["WITHOUT_OPTIMIZATION"] = self.settings.build_type == "Debug"
        self._cmake.definitions["WITH_ZLIB"] = self.options.with_zlib
        self._cmake.definitions["WITH_ZSTD"] = self.options.with_zstd
        self._cmake.definitions["WITH_PLUGINS"] = self.options.with_plugins
        self._cmake.definitions["WITH_SASL"] = self.options.with_sasl
        self._cmake.definitions["ENABLE_LZ4_EXT"] = "YES"

        self._cmake.definitions["RDKAFKA_BUILD_STATIC"] = not self.options.shared
        self._cmake.definitions["RDKAFKA_BUILD_EXAMPLES"] = "NO"
        self._cmake.definitions["RDKAFKA_BUILD_TESTS"] = "NO"

        self._cmake.configure()
        return self._cmake

    def _patch_sources(self):
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)

    def build(self):
        self._patch_sources()
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=_source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "RdKafka"
        self.cpp_info.names["cmake_find_package_multi"] = "RdKafka"
        self.cpp_info.requires = ["openssl::SSL", "zlib::zlib", "lz4::lz4", "zstd::zstd"]