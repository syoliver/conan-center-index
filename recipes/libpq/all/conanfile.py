from conans import ConanFile, AutoToolsBuildEnvironment, tools
from conans.tools import os_info
import os
import glob


class LibpqConan(ConanFile):
    name = "libpq"
    description = "The library used by all the standard PostgreSQL tools."
    topics = ("conan", "libpq", "postgresql", "database", "db")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.postgresql.org/docs/current/static/libpq.html"
    license = "PostgreSQL"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_zlib": [True, False],
        "with_openssl": [True, False],
        "disable_rpath": [True, False]}
    default_options = {'shared': False, 'fPIC': True, 'with_zlib': True, 'with_openssl': False, 'disable_rpath': False}
    _autotools = None

    def build_requirements(self):
        if self.settings.compiler == "Visual Studio":
            self.build_requires("strawberryperl/5.30.0.1")
        elif tools.os_info.is_windows:
            if "CONAN_BASH_PATH" not in os.environ and os_info.detect_windows_subsystem() != 'msys2':
                self.build_requires("msys2/20190524")
    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _is_clang8_x86(self):
        return self.settings.os == "Linux" and \
               self.settings.compiler == "clang" and \
               self.settings.compiler.version == "8" and \
               self.settings.arch == "x86"

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC
            del self.options.disable_rpath

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def requirements(self):
        if self.options.with_zlib:
            self.requires("zlib/1.2.11")
        if self.options.with_openssl:
            self.requires("openssl/1.1.1g")


    @property
    def _is_mingw(self):
        return self.settings.os == "Windows" and self.settings.compiler == "gcc"

    def _patch_mingw_files(self):
        if not self._is_mingw:
            return

        # patch for zlib naming in mingw
        tools.replace_in_file(os.path.join(self._source_subfolder, "configure"), '-lz ', '-lzlib ')

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = "postgresql-" + self.version
        os.rename(extracted_dir, self._source_subfolder)
        self._patch_mingw_files()


    def _construct_ldflags(self, dependency):
        dep = self.deps_cpp_info[dependency]
        return (["-I{}".format(include_dir) for include_dir in dep.include_paths]
               +["-L{}".format(link_dir)    for link_dir    in dep.lib_paths    ])

    def _configure_autotools(self):
        if not self._autotools:
            self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
            args = ["--without-readline"]
            if self.options.with_zlib:
                args.append("--with-zlib")
                self._autotools.flags.extend(self._construct_ldflags("zlib"))
            else:
                args.append("--without-zlib")

            if self.options.with_openssl:
                args.append("--with-openssl")
                self._autotools.flags.extend(self._construct_ldflags("openssl"))
            else:
                args.append("--without-openssl")

            if tools.cross_building(self.settings) and not self.options.with_openssl:
                args.append("--disable-strong-random")
            if self.settings.os != "Windows" and self.options.disable_rpath:
                args.append("--disable-rpath")
            if self._is_clang8_x86:
                self._autotools.flags.append("-msse2")

            # if self._is_mingw:
            #    self._autotools.flags.append("-lmingwex")

            with tools.chdir(self._source_subfolder):
                self._autotools.configure(args=args)
        return self._autotools

    def build(self):
        if self.settings.compiler == "Visual Studio":
            # https://www.postgresql.org/docs/8.3/install-win32-libpq.html
            # https://github.com/postgres/postgres/blob/master/src/tools/msvc/README
            if not self.options.shared:
                tools.replace_in_file(os.path.join(self._source_subfolder, "src", "tools", "msvc", "MKvcbuild.pm"),
                                      "$libpq = $solution->AddProject('libpq', 'dll', 'interfaces',",
                                      "$libpq = $solution->AddProject('libpq', 'lib', 'interfaces',")
            runtime = {'MT': 'MultiThreaded',
                       'MTd': 'MultiThreadedDebug',
                       'MD': 'MultiThreadedDLL',
                       'MDd': 'MultiThreadedDebugDLL'}.get(str(self.settings.compiler.runtime))
            msbuild_project_pm = os.path.join(self._source_subfolder, "src", "tools", "msvc", "MSBuildProject.pm")
            tools.replace_in_file(msbuild_project_pm, "'MultiThreadedDebugDLL'", "'%s'" % runtime)
            tools.replace_in_file(msbuild_project_pm, "'MultiThreadedDLL'", "'%s'" % runtime)
            config_default_pl = os.path.join(self._source_subfolder, "src", "tools", "msvc", "config_default.pl")
            solution_pm = os.path.join(self._source_subfolder, "src", "tools", "msvc", "Solution.pm")
            if self.options.with_zlib:
                tools.replace_in_file(solution_pm,
                                      "zdll.lib", "%s.lib" % self.deps_cpp_info["zlib"].libs[0])
                tools.replace_in_file(config_default_pl,
                                      "zlib      => undef",
                                      "zlib      => '%s'" % self.deps_cpp_info["zlib"].rootpath.replace("\\", "/"))
            if self.options.with_openssl:
                for ssl in ["VC\libssl32", "VC\libssl64", "libssl"]:
                    tools.replace_in_file(solution_pm,
                                          "%s.lib" % ssl,
                                          "%s.lib" % self.deps_cpp_info["openssl"].libs[0])
                for crypto in ["VC\libcrypto32", "VC\libcrypto64", "libcrypto"]:
                    tools.replace_in_file(solution_pm,
                                          "%s.lib" % crypto,
                                          "%s.lib" % self.deps_cpp_info["openssl"].libs[1])
                tools.replace_in_file(config_default_pl,
                                      "openssl   => undef",
                                      "openssl   => '%s'" % self.deps_cpp_info["openssl"].rootpath.replace("\\", "/"))
            with tools.vcvars(self.settings):
                config = "DEBUG" if self.settings.build_type == "Debug" else "RELEASE"
                with tools.environment_append({"CONFIG": config}):
                    with tools.chdir(os.path.join(self._source_subfolder, "src", "tools", "msvc")):
                        self.run("perl build.pl libpq")
                        if not self.options.shared:
                            self.run("perl build.pl libpgport")
        else:
            autotools = self._configure_autotools()
            with tools.chdir(os.path.join(self._source_subfolder, "src", "backend")):
                autotools.make(target="generated-headers")
            with tools.chdir(os.path.join(self._source_subfolder, "src", "common")):
                autotools.make()
            if tools.Version(self.version) >= "12":
                with tools.chdir(os.path.join(self._source_subfolder, "src", "port")):
                    autotools.make()
            with tools.chdir(os.path.join(self._source_subfolder, "src", "include")):
                autotools.make()
            with tools.chdir(os.path.join(self._source_subfolder, "src", "interfaces", "libpq")):
                autotools.make()
            with tools.chdir(os.path.join(self._source_subfolder, "src", "bin", "pg_config")):
                autotools.make()

    def _remove_unused_libraries_from_package(self, is_shared):
        path = None
        if is_shared:
            path = os.path.join(self.package_folder, "lib", "*.a")
        else:
            path = os.path.join(self.package_folder, "lib", "libpq.so*")
        for file in glob.glob(path):
            os.remove(file)

    def package(self):
        self.copy(pattern="COPYRIGHT", dst="licenses", src=self._source_subfolder)
        if self.settings.compiler == "Visual Studio":
            self.copy("*postgres_ext.h", src=self._source_subfolder, dst="include", keep_path=False)
            self.copy("*pg_config.h", src=self._source_subfolder, dst="include", keep_path=False)
            self.copy("*pg_config_ext.h", src=self._source_subfolder, dst="include", keep_path=False)
            self.copy("*libpq-fe.h", src=self._source_subfolder, dst="include", keep_path=False)
            self.copy("*libpq-events.h", src=self._source_subfolder, dst="include", keep_path=False)
            self.copy("*.h", src=os.path.join(self._source_subfolder, "src", "include", "libpq"), dst=os.path.join("include", "libpq"), keep_path=False)
            self.copy("*genbki.h", src=self._source_subfolder, dst=os.path.join("include", "catalog"), keep_path=False)
            self.copy("*pg_type.h", src=self._source_subfolder, dst=os.path.join("include", "catalog"), keep_path=False)
            if self.options.shared:
                self.copy("**/libpq.dll", src=self._source_subfolder, dst="bin", keep_path=False)
                self.copy("**/libpq.lib", src=self._source_subfolder, dst="lib", keep_path=False)
            else:
                self.copy("*.lib", src=self._source_subfolder, dst="lib", keep_path=False)
        else:
            autotools = self._configure_autotools()
            with tools.chdir(os.path.join(self._source_subfolder, "src", "common")):
                autotools.install()
            with tools.chdir(os.path.join(self._source_subfolder, "src", "include")):
                autotools.install()
            with tools.chdir(os.path.join(self._source_subfolder, "src", "interfaces", "libpq")):
                autotools.install()
            if tools.Version(self.version) >= "12":
                with tools.chdir(os.path.join(self._source_subfolder, "src", "port")):
                    autotools.install()

            self._remove_unused_libraries_from_package(self.options.shared)

            with tools.chdir(os.path.join(self._source_subfolder, "src", "bin", "pg_config")):
                autotools.install()
            tools.rmdir(os.path.join(self.package_folder, "include", "postgresql", "server"))
            self.copy(pattern="*.h", dst=os.path.join("include", "catalog"), src=os.path.join(self._source_subfolder, "src", "include", "catalog"))
        self.copy(pattern="*.h", dst=os.path.join("include", "catalog"), src=os.path.join(self._source_subfolder, "src", "backend", "catalog"))
        tools.rmdir(os.path.join(self.package_folder, "share"))
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))

    def _construct_library_name(self, name):
        if self.settings.compiler == "Visual Studio":
            return "lib{}".format(name)
        return  name

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "PostgreSQL"
        self.cpp_info.names["cmake_find_package_multi"] = "PostgreSQL"
        self.env_info.PostgreSQL_ROOT = self.package_folder
        
        self.cpp_info.components["pq"].libs = [self._construct_library_name("pq")]

        if self.options.with_zlib:
            self.cpp_info.components["pq"].requires.append("zlib::zlib")

        if self.options.with_openssl:
            self.cpp_info.components["pq"].requires.append("openssl::openssl")

        if not self.options.shared:
            if self.settings.compiler == "Visual Studio":
                if tools.Version(self.version) < '12':
                    self.cpp_info.components["pgport"].libs = ["libpgport"]
                    self.cpp_info.components["pq"].requires.extend(["pgport"])
                else:
                    self.cpp_info.components["pgcommon"].libs = ["libpgcommon"]
                    self.cpp_info.components["pgport"].libs = ["libpgport"]
                    self.cpp_info.components["pq"].requires.extend(["pgport", "pgcommon"])
            else:
                if tools.Version(self.version) < '12':
                    self.cpp_info.components["pgcommon"].libs = ["pgcommon"]
                    self.cpp_info.components["pq"].requires.extend(["pgcommon"])
                else:
                    self.cpp_info.components["pgcommon"].libs = ["pgcommon", "pgcommon_shlib"]
                    self.cpp_info.components["pgport"].libs = ["pgport", "pgport_shlib"]
                    self.cpp_info.components["pq"].requires.extend(["pgport", "pgcommon"])


        if self.settings.os == "Linux":
            self.cpp_info.components["pq"].system_libs = ["pthread"]
        elif self.settings.os == "Windows":
            self.cpp_info.components["pq"].system_libs = ["ws2_32", "secur32", "advapi32", "shell32", "crypt32", "wldap32"]
