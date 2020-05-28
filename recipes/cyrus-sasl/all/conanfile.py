from conans import ConanFile, AutoToolsBuildEnvironment, tools
from conans.errors import ConanInvalidConfiguration
import os
import glob


class CyrusSASLConan(ConanFile):
    name = "cyrus-sasl"
    description = "This is the Cyrus SASL API implementation. It can be used on the client or server side to provide authentication and authorization services. See RFC 4422 for more information."
    topics = ("conan", "cyrus", "SASL", "authentication", "authorization")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.cyrusimap.org/sasl/"
    license = "BSD-with-attribution"
    exports_sources = ["patches/**"]

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_cram": [True, False],
        "with_digest": [True, False],
        "with_scram": [True, False],
        "with_otp": [True, False],
        "with_krb4": [True, False],
        "with_gssapi": [True, False],
        "with_plain": [True, False],
        "with_anon": [True, False],
        "with_postgresql": [True, False],
        "with_mysql": [True, False],
        "with_ldapdb": [True, False],
        "with_bdb": [True, False]
    }

    default_options = {
        "shared": False,
        "fPIC": True,
        "with_cram": True,
        "with_digest": True,
        "with_scram": True,
        "with_otp": True,
        "with_krb4": True,
        "with_gssapi": True,
        "with_plain": True,
        "with_anon": True,

        "with_postgresql": False,
        "with_mysql": False,
        "with_ldapdb": False,
        "with_bdb": False,
    }


    _autotools = None
    _source_subfolder = "source_subfolder"

    def requirements(self):
        if self.options.with_postgresql:
            self.requires("libpq/11.5")
        if self.options.with_mysql:
            self.requires("libmysqlclient/8.0.17")

    def build_requirements(self):
        if tools.os_info.is_windows and "CONAN_BASH_PATH" not in os.environ:
            self.build_requires("msys2/20190524")

        self.build_requires("autoconf/2.69")
        self.build_requires("m4/1.4.18")
        self.build_requires("libtool/2.4.6")
        

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = glob.glob(self.name + "-*/")[0]
        os.rename(extracted_dir, self._source_subfolder)

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd
        if self.settings.os == "Windows":
            raise ConanInvalidConfiguration("Cyrus SASL package is not compatible with Windows.")

    def _configure_autotools(self):
        if self._autotools:
            return self._autotools

        self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)

        configure_args = []

        if self.options.shared:
            configure_args.extend(["--enable-shared", "--disable-static"])
        else:
            configure_args.extend(["--disable-shared", "--enable-static"])

        if not self.options.with_cram:
            configure_args.append("--disable-cram")
            
        if not self.options.with_digest:
            configure_args.append("--disable-digest")

        if not self.options.with_scram:
            configure_args.append("--disable-scram")
             
        if not self.options.with_otp:
            configure_args.append("--disable-otp")

        if not self.options.with_krb4:
            configure_args.append("--disable-krb4")

        if not self.options.with_gssapi:
            configure_args.append("--disable-gssapi")

        if not self.options.with_plain:
            configure_args.append("--disable-plain")

        if not self.options.with_anon:
            configure_args.append("--disable-anon")
            
        if self.options.with_postgresql:
            configure_args.extend(["--with-pgsql={}".format(self.deps_cpp_info['libpq'].rootpath)])

        if self.options.with_mysql:
            configure_args.extend(["--with-mysql={}".format(self.deps_cpp_info['libmysqlclient'].rootpath)])

        if self.options.with_ldapdb:
            configure_args.append("--enable-ldapdb")

        if self.options.with_ldapdb:
            # LDAPDB auxprop plugin (and LDAP enabled saslauthd) introduces a circular dependency
            # between OpenLDAP and SASL.  I.e., you must have OpenLDAP already built when
            # building LDAPDB in SASL.  In order for LDAPDB to work at runtime, you must have
            # OpenLDAP already built with SASL support. One way to solve this issue is to
            # build Cyrus SASL first without ldap support, then build OpenLDAP, and then come
            # back to SASL and build LDAPDB.
            # configure_args.extend(["--enable-ldapdb", "--with-ldapdb=PATH"])
            raise ConanInvalidConfiguration("LDAPDB not implemented yet")

        if self.options.with_bdb:
            # configure_args.extend(["--with-bdb-libdir", "--with-bdb-incdir"])
            raise ConanInvalidConfiguration("Berkeley DB not implemented yet")

        with tools.chdir(self._source_subfolder):
            
            with tools.environment_append({"NOCONFIGURE": "YES"}):
                self.run("./autogen.sh", win_bash=tools.os_info.is_windows)
            self._autotools.configure(args=configure_args)

        return self._autotools

    def _patch_files(self):
        for patch in self.conan_data["patches"][self.version]:
            tools.patch(**patch)

    def build(self):
        self._patch_files()
        autotools = self._configure_autotools()
        with tools.chdir(self._source_subfolder):
            autotools.make()

    def package(self):
        autotools = self._configure_autotools()
        with tools.chdir(self._source_subfolder):
            autotools.install()
            
        self.copy('COPYING', src=self._source_subfolder, dst="licenses")
        tools.rmdir(os.path.join(self.package_folder, "share"))
        tools.rmdir(os.path.join(self.package_folder, "etc"))
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))


        for file in glob.glob(os.path.join(self.package_folder, "lib", "sasl2", "*.la")):
            os.remove(file)

        for file in glob.glob(os.path.join(self.package_folder, "lib", "*.la")):
            os.remove(file)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
