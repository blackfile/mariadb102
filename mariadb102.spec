# Prefix that is used for patches
%global pkg_name mariadb
%global pkgnamepatch mariadb

# Regression tests may take a long time (many cores recommended), skip them by
%{!?runselftest:%global runselftest 1}

# Set this to 1 to see which tests fail, but 0 on production ready build
%global ignore_testsuite_result 0

# The last version on which the full testsuite has been run
# In case of further rebuilds of that version, don't require full testsuite to be run
# run only "main" suite
%global last_tested_version 10.2.22
# Set to 1 to force run the testsuite even if it was already tested in current version
%global force_run_testsuite 0

# In f20+ use unversioned docdirs, otherwise the old versioned one
%if 0%{?fedora} >= 20 || 0%{?rhel} >= 8
%global _pkgdocdirname %{name}
%else
%global _pkgdocdirname %{name}-%{version}
%endif

# By default, patch(1) creates backup files when chunks apply with offsets.
# Turn that off to ensure such files don't get included in RPMs (cf bz#884755).
%global _default_patch_flags --no-backup-if-mismatch



# TokuDB engine
#   https://mariadb.com/kb/en/mariadb/tokudb/
#   TokuDB engine is available only for x86_64
# * There's a problem currently with jemalloc, which tokudb use.
#   TokuDB does not yet support new Jemalloc 5, but on F>=28, there's only Jemalloc 5. Not a supported configuration. https://jira.percona.com/browse/PS-4393
#   Also build of TokuDB without Jemalloc is not supported.
# * It is better to build TokuDB without jemalloc than not at all. So far, this configuration works for users and they want the TokuDB.
# Mroonga engine
#   https://mariadb.com/kb/en/mariadb/about-mroonga/
#   Current version in MariaDB, 7.07, only supports the x86_64
#   Mroonga upstream warns about using 32-bit package: http://mroonga.org/docs/install.html
# RocksDB engine
#   https://mariadb.com/kb/en/library/myrocks-supported-platforms/
#   RocksB engine is available only for x86_64
#   RocksDB may be built with jemalloc, if specified in CMake
# Cassandra engine
#   Experimental version of the Cassandra storage engine
#   The tests needs running cassandra server
#   Do not build it for now
%if %_arch == x86_64 && 0%{?fedora}
%bcond_without tokudb
%bcond_without mroonga
%bcond_without rocksdb
%bcond_with cassandra
%else
%bcond_with tokudb
%bcond_with mroonga
%bcond_with rocksdb
%bcond_with cassandra
%endif

# The Open Query GRAPH engine (OQGRAPH) is a computation engine allowing
# hierarchies and more complex graph structures to be handled in a relational fashion
%bcond_without oqgraph

# Other plugins
%if 0%{?fedora}
%bcond_without cracklib
%bcond_without connect
%bcond_without sphinx
%else
%bcond_with cracklib
%bcond_with connect
%bcond_with sphinx
%endif
%bcond_without gssapi

# For some use cases we do not need some parts of the package. Set to "...with" to exclude
%if 0%{?fedora} >= 28 || 0%{?rhel} > 7
%bcond_with    clibrary
%else
%bcond_without clibrary
%endif
%bcond_without embedded
%bcond_without devel
%bcond_without client
%bcond_without common
%bcond_without errmsg
%bcond_without bench
%bcond_without test
%bcond_without galera
%bcond_without backup

# When there is already another package that ships /etc/my.cnf,
# rather include it than ship the file again, since conflicts between
# those files may create issues
%bcond_with    config

# In RHEL7, the stock mariadb-libs package contains both my.cnf and
# libmysqlclient.  In MariaDB 10.2 libmysqlclient was renamed to libmariadb.
# In order to re-use the stock my.cnf file from mariadb-libs, we must make
# %%{name}-libs parallel installable with stock mariadb-libs by removing all
# references to libmysqlclient.  This avoids the need for a separate compat
# libmysqlclient package.
%if %{defined rhel} && %{without config}
%bcond_without parallel_libs
%endif

# For deep debugging we need to build binaries with extra debug info
%bcond_with    debug

# Page compression algorithms for InnoDB & XtraDB
# lz4 currently cannot be turned off by CMake, only by not having lz4-devel package in the buildroot
#   https://jira.mariadb.org/browse/MDEV-15932
%bcond_without lz4



# MariaDB 10.0 and later requires pcre >= 8.35, otherwise we need to use
# the bundled library, since the package cannot be build with older version
%if 0%{?fedora} || 0%{?rhel} > 7
%bcond_without unbundled_pcre
%else
%bcond_with unbundled_pcre
%global pcre_bundled_version 8.43
%endif

# Include systemd files
%global daemon_name mariadb
%global daemon_no_prefix %{pkg_name}
%global mysqld_pid_dir mariadb

# We define some system's well known locations here so we can use them easily
# later when building to another location (like SCL)
%global logrotateddir %{_sysconfdir}/logrotate.d
%global logfiledir %{_localstatedir}/log/%{daemon_name}
%global logfile %{logfiledir}/%{daemon_name}.log
# Directory for storing pid file
%global pidfiledir %{_rundir}/%{mysqld_pid_dir}
# Defining where database data live
%global dbdatadir %{_localstatedir}/lib/mysql
# Home directory of mysql user should be same for all packages that create it
%global mysqluserhome /var/lib/mysql


# Provide mysql names for compatibility
%if 0%{?fedora}
%bcond_without mysql_names
%bcond_without conflicts
%else
%bcond_with    mysql_names
%bcond_with    conflicts
%endif

# Make long macros shorter
%global sameevr   %{epoch}:%{version}-%{release}

Name:             mariadb102
Version:          10.2.27
Release:          2%{?with_debug:.debug}%{?dist}
Epoch:            3

Summary:          A community developed branch of MySQL
URL:              http://mariadb.org
# Exceptions allow client libraries to be linked with most open source SW, not only GPL code.  See README.mysql-license
License:          GPLv2 with exceptions and LGPLv2 and BSD

Source0:          https://mirrors.osuosl.org/pub/mariadb/mariadb-%{version}/source/mariadb-%{version}.tar.gz
Source2:          mysql_config_multilib.sh
Source3:          my.cnf.in
Source5:          README.mysql-cnf
Source6:          README.mysql-docs
Source7:          README.mysql-license
Source10:         mysql.tmpfiles.d.in
Source11:         mysql.service.in
Source12:         mysql-prepare-db-dir.sh
Source14:         mysql-check-socket.sh
Source15:         mysql-scripts-common.sh
Source16:         mysql-check-upgrade.sh
Source18:         mysql@.service.in
Source50:         rh-skipped-tests-base.list
Source51:         rh-skipped-tests-arm.list
Source52:         rh-skipped-tests-s390.list
Source53:         rh-skipped-tests-ppc.list
# Proposed upstream: https://jira.mariadb.org/browse/MDEV-12442
# General upstream response was slightly positive
Source70:         clustercheck.sh
Source71:         LICENSE.clustercheck
# Upstream said: "Generally MariaDB has more allows to allow for xtradb sst mechanism".
# https://jira.mariadb.org/browse/MDEV-12646
Source72:         mariadb-server-galera.te

#   Patch4: Red Hat distributions specific logrotate fix
#   it would be big unexpected change, if we start shipping it now. Better wait for MariaDB 10.2
Patch4:           %{pkgnamepatch}-logrotate.patch
#   Patch7: add to the CMake file all files where we want macros to be expanded
Patch7:           %{pkgnamepatch}-scripts.patch
#   Patch9: pre-configure to comply with guidelines
Patch9:           %{pkgnamepatch}-ownsetup.patch

# Patches specific for this mysql package
#   Patch37: don't create a test DB: https://jira.mariadb.org/browse/MDEV-12645
Patch37:          %{pkgnamepatch}-notestdb.patch

BuildRequires:    cmake gcc-c++
BuildRequires:    multilib-rpm-config
BuildRequires:    selinux-policy-devel
BuildRequires:    systemd systemd-devel

# Page compression algorithms for InnoDB & XtraDB
BuildRequires:    zlib-devel
%{?with_lz4:BuildRequires:    lz4-devel}

# asynchornous operations stuff
BuildRequires:    libaio-devel
# commands history features
BuildRequires:    readline-devel
# CLI graphic
BuildRequires:    ncurses-devel
# debugging stuff
BuildRequires:    systemtap-sdt-devel
# Bison SQL parser
BuildRequires:    bison bison-devel

# auth_pam.so plugin will be build if pam-devel is installed
BuildRequires:    pam-devel
# use either new enough version of pcre or provide bundles(pcre)
%{?with_unbundled_pcre:BuildRequires: pcre-devel >= 8.35 pkgconf}
%{!?with_unbundled_pcre:Provides: bundled(pcre) = %{pcre_bundled_version}}
# Few utilities needs Perl
%if 0%{?fedora} || 0%{?rhel} > 7
BuildRequires:    perl-interpreter
BuildRequires:    perl-generators
%endif
# Tests requires time and ps and some perl modules
BuildRequires:    procps
BuildRequires:    time
BuildRequires:    perl(Env)
BuildRequires:    perl(Exporter)
BuildRequires:    perl(Fcntl)
BuildRequires:    perl(File::Temp)
BuildRequires:    perl(Data::Dumper)
BuildRequires:    perl(Getopt::Long)
BuildRequires:    perl(IPC::Open3)
BuildRequires:    perl(Memoize)
BuildRequires:    perl(Socket)
BuildRequires:    perl(Sys::Hostname)
BuildRequires:    perl(Test::More)
BuildRequires:    perl(Time::HiRes)
BuildRequires:    perl(Symbol)
# for running some openssl tests rhbz#1189180
BuildRequires:    openssl openssl-devel

Requires:         bash coreutils grep

Requires:         %{name}-common%{?_isa} = %{sameevr}

%if %{with clibrary}
# Explicit EVR requirement for -libs is needed for RHBZ#1406320
Requires:         %{name}-libs%{?_isa} = %{sameevr}
%else
# If not built with client library in this package, use connector-c
Requires:         mariadb-connector-c >= 3.0
%endif

%if %{with mysql_names}
Provides:         mysql = %{sameevr}
Provides:         mysql%{?_isa} = %{sameevr}
Provides:         mysql-compat-client = %{sameevr}
Provides:         mysql-compat-client%{?_isa} = %{sameevr}
%endif

# MySQL (with caps) is upstream's spelling of their own RPMs for mysql
%{?with_conflicts:Conflicts:        community-mysql}

# safe replacement
Provides:         mariadb = %{sameevr}
Provides:         mariadb%{?_isa} = %{sameevr}
Conflicts:        mariadb < %{sameevr}

# Filtering: https://fedoraproject.org/wiki/Packaging:AutoProvidesAndRequiresFiltering
%global __requires_exclude ^perl\\((hostnames|lib::mtr|lib::v1|mtr_|My::)
%global __provides_exclude_from ^(%{_datadir}/(mysql|mysql-test)/.*|%{_libdir}/%{pkg_name}/plugin/.*\\.so)$


%description
MariaDB is a community developed branch of MySQL.
MariaDB is a multi-user, multi-threaded SQL database server.
It is a client/server implementation consisting of a server daemon (mysqld)
and many different client programs and libraries. The base package
contains the standard MariaDB/MySQL client programs and generic MySQL files.


%if %{with clibrary}
%package          libs
Summary:          The shared libraries required for MariaDB/MySQL clients
Requires:         %{name}-common%{?_isa} = %{sameevr}
%if %{with mysql_names}
Provides:         mysql-libs = %{sameevr}
Provides:         mysql-libs%{?_isa} = %{sameevr}
%endif # mysql_names

%description      libs
The mariadb-libs package provides the essential shared libraries for any
MariaDB/MySQL client program or interface. You will need to install this
package to use any other MariaDB package or any clients that need to connect
to a MariaDB/MySQL server.
%endif #clibrary


# At least main config file /etc/my.cnf is shared for client and server part
# Since we want to support combination of different client and server
# implementations (e.g. mariadb library and community-mysql server),
# we need the config file(s) to be in a separate package, so no extra packages
# are pulled, because these would likely conflict.
# More specifically, the dependency on the main configuration file (/etc/my.cnf)
# is supposed to be defined as Requires: /etc/my.cnf rather than requiring
# a specific package, so installer app can choose whatever package fits to
# the transaction.
%if %{with config}
%package          config
Summary:          The config files required by server and client

%description      config
The package provides the config file my.cnf and my.cnf.d directory used by any
MariaDB or MySQL program. You will need to install this package to use any
other MariaDB or MySQL package if the config files are not provided in the
package itself.
%endif


%if %{with common}
%package          common
Summary:          The shared files required by server and client
%if %{with parallel_libs}
# ensure we build with stock mariadb-libs
Requires:         mariadb-libs%{?_isa} < 1:10
%else
Requires:         %{_sysconfdir}/my.cnf
%endif

%description      common
The package provides the essential shared files for any MariaDB program.
You will need to install this package to use any other MariaDB package.
%endif


%if %{with errmsg}
%package          errmsg
Summary:          The error messages files required by server and embedded
Requires:         %{name}-common%{?_isa} = %{sameevr}

%description      errmsg
The package provides error messages files for the MariaDB daemon and the
embedded server. You will need to install this package to use any of those
MariaDB packages.
%endif


%if %{with galera}
%package          server-galera
Summary:          The configuration files and scripts for galera replication
Requires:         %{name}-common%{?_isa} = %{sameevr}
Requires:         %{name}-server%{?_isa} = %{sameevr}
Requires:         galera >= 25.3.3
Requires(post):   libselinux-utils
%if 0%{?fedora} >= 23 || 0%{?rhel} >= 8
Requires(post):   policycoreutils-python-utils
%else
Requires(post):   policycoreutils-python
%endif
# wsrep requirements
Requires:         lsof
Requires:         rsync

%description      server-galera
MariaDB is a multi-user, multi-threaded SQL database server. It is a
client/server implementation consisting of a server daemon (mysqld)
and many different client programs and libraries. This package contains
the MariaDB server and some accompanying files and directories.
MariaDB is a community developed branch of MySQL.
%endif


%package          server
Summary:          The MariaDB server and related files

# note: no version here = %%{version}-%%{release}
%if %{with mysql_names}
Requires:         mysql-compat-client%{?_isa}
Requires:         mysql%{?_isa}
%else
Requires:         %{name}%{?_isa}
%endif
Requires:         %{name}-common%{?_isa} = %{sameevr}
Requires:         %{name}-errmsg%{?_isa} = %{sameevr}

%if %{with parallel_libs}
# ensure we build with stock mariadb-libs
Requires:         mariadb-libs%{?_isa} < 1:10
%else
Requires:         %{_sysconfdir}/my.cnf
Requires:         %{_sysconfdir}/my.cnf.d
%endif

# for fuser in mysql-check-socket
Requires:         psmisc

Requires:         coreutils
Requires(pre):    /usr/sbin/useradd
# We require this to be present for %%{_tmpfilesdir}
Requires:         systemd
# Make sure it's there when scriptlets run, too
%{?systemd_requires}
# RHBZ#1496131; use 'iproute' instead of 'net-tools'
Requires:         iproute
%if %{with mysql_names}
Provides:         mysql-server = %{sameevr}
Provides:         mysql-server%{?_isa} = %{sameevr}
Provides:         mysql-compat-server = %{sameevr}
Provides:         mysql-compat-server%{?_isa} = %{sameevr}
%endif
%{?with_conflicts:Conflicts:        community-mysql-server}
# safe replacement
Provides:         mariadb-server = %{sameevr}
Provides:         mariadb-server%{?_isa} = %{sameevr}
Conflicts:        mariadb-server < %{sameevr}

%description      server
MariaDB is a multi-user, multi-threaded SQL database server. It is a
client/server implementation consisting of a server daemon (mysqld)
and many different client programs and libraries. This package contains
the MariaDB server and some accompanying files and directories.
MariaDB is a community developed branch of MySQL.


%if %{with oqgraph}
%package          oqgraph-engine
Summary:          The Open Query GRAPH engine for MariaDB
Requires:         %{name}-server%{?_isa} = %{sameevr}
# boost and Judy required for oograph
BuildRequires:    boost-devel Judy-devel

%description      oqgraph-engine
The package provides Open Query GRAPH engine (OQGRAPH) as plugin for MariaDB
database server. OQGRAPH is a computation engine allowing hierarchies and more
complex graph structures to be handled in a relational fashion. In a nutshell,
tree structures and friend-of-a-friend style searches can now be done using
standard SQL syntax, and results joined onto other tables.
%endif


%if %{with connect}
%package          connect-engine
Summary:          The CONNECT storage engine for MariaDB
Requires:         %{name}-server%{?_isa} = %{sameevr}

%description      connect-engine
The CONNECT storage engine enables MariaDB to access external local or
remote data (MED). This is done by defining tables based on different data
types, in particular files in various formats, data extracted from other DBMS
or products (such as Excel), or data retrieved from the environment
(for example DIR, WMI, and MAC tables).
%endif


%if %{with backup}
%package          backup
Summary:          The mariabackup tool for physical online backups
Requires:         %{name}-server%{?_isa} = %{sameevr}
BuildRequires:    libarchive-devel

%description      backup
MariaDB Backup is an open source tool provided by MariaDB for performing
physical online backups of InnoDB, Aria and MyISAM tables.
For InnoDB, "hot online" backups are possible.
%endif


%if %{with rocksdb}
%package          rocksdb-engine
Summary:          The RocksDB storage engine for MariaDB
Requires:         %{name}-server%{?_isa} = %{sameevr}
Provides:         bundled(rocksdb)

%description      rocksdb-engine
The RocksDB storage engine is used for high performance servers on SSD drives.
%endif


%if %{with tokudb}
%package          tokudb-engine
Summary:          The TokuDB storage engine for MariaDB
Requires:         %{name}-server%{?_isa} = %{sameevr}
BuildRequires:    jemalloc-devel
Requires:         jemalloc

%description      tokudb-engine
The TokuDB storage engine from Percona.
%endif


%if %{with cracklib}
%package          cracklib-password-check
Summary:          The password strength checking plugin
Requires:         %{name}-server%{?_isa} = %{sameevr}
BuildRequires:    cracklib-dicts cracklib-devel
Requires:         cracklib-dicts

%description      cracklib-password-check
CrackLib is a password strength checking library. It is installed by default
in many Linux distributions and is invoked automatically (by pam_cracklib.so)
whenever the user login password is modified.
Now, with the cracklib_password_check password validation plugin, one can
also use it to check MariaDB account passwords.
%endif


%if %{with gssapi}
%package          gssapi-server
Summary:          GSSAPI authentication plugin for server
Requires:         %{name}-server%{?_isa} = %{sameevr}
BuildRequires:    krb5-devel

%description      gssapi-server
GSSAPI authentication server-side plugin for MariaDB for passwordless login.
This plugin includes support for Kerberos on Unix.
%endif


%if %{with sphinx}
%package          sphinx-engine
Summary:          The Sphinx storage engine for MariaDB
Requires:         %{name}-server%{?_isa} = %{sameevr}
BuildRequires:    sphinx libsphinxclient libsphinxclient-devel
Requires:         sphinx libsphinxclient

%description      sphinx-engine
The Sphinx storage engine for MariaDB.
%endif

%if %{with cassandra}
%package          cassandra-engine
Summary:          The Cassandra storage engine for MariaDB - EXPERIMENTAL VERSION
Requires:         %{name}-server%{?_isa} = %{sameevr}
BuildRequires:    cassandra thrift-devel

%description      cassandra-engine
The Cassandra storage engine for MariaDB. EXPERIMENTAL VERSION!
%endif


%package          server-utils
Summary:          Non-essential server utilities for MariaDB/MySQL applications
Requires:         %{name}-server%{?_isa} = %{sameevr}
%if %{with mysql_names}
Provides:         mysql-perl = %{sameevr}
%endif
# mysqlhotcopy needs DBI/DBD support
Requires:         perl(DBI) perl(DBD::mysql)

%description      server-utils
This package contains all non-essential server utilities and scripts for
managing databases. It also contains all utilities requiring Perl and it is
the only MariaDB sub-package, except test subpackage, that depends on Perl.


%if %{with devel}
%package          devel
Summary:          Files for development of MariaDB/MySQL applications
%{?with_clibrary:Requires:         %{name}-libs%{?_isa} = %{sameevr}}
# avoid issues with openssl1.0 / openssl1.1 / compat
Requires:         pkgconfig(openssl)
%if %{without clibrary}
Requires:         mariadb-connector-c-devel >= 3.0
%endif
%if %{with mysql_names}
Provides:         mysql-devel = %{sameevr}
Provides:         mysql-devel%{?_isa} = %{sameevr}
%endif
%{?with_conflicts:Conflicts:        community-mysql-devel}
# safe replacement
Provides:         mariadb-devel = %{sameevr}
Provides:         mariadb-devel%{?_isa} = %{sameevr}
Conflicts:        mariadb-devel < %{sameevr}

%description      devel
MariaDB is a multi-user, multi-threaded SQL database server.
MariaDB is a community developed branch of MySQL.
%if %{with clibrary}
This package contains everything needed for developing MariaDB/MySQL client
and server applications.
%else
This package contains everything needed for developing MariaDB/MySQL server
applications. For developing client applications, use mariadb-connector-c
package.
%endif
%endif


%if %{with embedded}
%package          embedded
Summary:          MariaDB as an embeddable library
Requires:         %{name}-common%{?_isa} = %{sameevr}
Requires:         %{name}-errmsg%{?_isa} = %{sameevr}
%if %{with mysql_names}
Provides:         mysql-embedded = %{sameevr}
Provides:         mysql-embedded%{?_isa} = %{sameevr}
%endif
# safe replacement
Provides:         mariadb-embedded = %{sameevr}
Provides:         mariadb-embedded%{?_isa} = %{sameevr}
Conflicts:        mariadb-embedded < %{sameevr}

%description      embedded
MariaDB is a multi-user, multi-threaded SQL database server. This
package contains a version of the MariaDB server that can be embedded
into a client application instead of running as a separate process.
MariaDB is a community developed branch of MySQL.


%package          embedded-devel
Summary:          Development files for MariaDB as an embeddable library
Requires:         %{name}-embedded%{?_isa} = %{sameevr}
Requires:         %{name}-devel%{?_isa} = %{sameevr}
# embedded-devel should require libaio-devel (rhbz#1290517)
Requires:         libaio-devel
%if %{with mysql_names}
Provides:         mysql-embedded-devel = %{sameevr}
Provides:         mysql-embedded-devel%{?_isa} = %{sameevr}
%endif
%{?with_conflicts:Conflicts:        community-mysql-embedded-devel}
# safe replacement
Provides:         mariadb-embedded-devel = %{sameevr}
Provides:         mariadb-embedded-devel%{?_isa} = %{sameevr}
Conflicts:        mariadb-embedded-devel < %{sameevr}

%description      embedded-devel
MariaDB is a multi-user, multi-threaded SQL database server.
MariaDB is a community developed branch of MySQL.
This package contains files needed for developing and testing with
the embedded version of the MariaDB server.
%endif


%if %{with bench}
%package          bench
Summary:          MariaDB benchmark scripts and data
Requires:         %{name}%{?_isa} = %{sameevr}
%if %{with mysql_names}
Provides:         mysql-bench = %{sameevr}
Provides:         mysql-bench%{?_isa} = %{sameevr}
%endif
%{?with_conflicts:Conflicts:        community-mysql-bench}
# safe replacement
Provides:         mariadb-bench = %{sameevr}
Provides:         mariadb-bench%{?_isa} = %{sameevr}
Conflicts:        mariadb-bench < %{sameevr}

%description      bench
MariaDB is a multi-user, multi-threaded SQL database server.
MariaDB is a community developed branch of MySQL.
This package contains benchmark scripts and data for use when benchmarking
MariaDB.
%endif


%if %{with test}
%package          test
Summary:          The test suite distributed with MariaDB
Requires:         %{name}%{?_isa} = %{sameevr}
Requires:         %{name}-common%{?_isa} = %{sameevr}
Requires:         %{name}-server%{?_isa} = %{sameevr}
Requires:         perl(Env)
Requires:         perl(Exporter)
Requires:         perl(Fcntl)
Requires:         perl(File::Temp)
Requires:         perl(Data::Dumper)
Requires:         perl(Getopt::Long)
Requires:         perl(IPC::Open3)
Requires:         perl(Socket)
Requires:         perl(Sys::Hostname)
Requires:         perl(Test::More)
Requires:         perl(Time::HiRes)
%{?with_conflicts:Conflicts:        community-mysql-test}
%if %{with mysql_names}
Provides:         mysql-test = %{sameevr}
Provides:         mysql-test%{?_isa} = %{sameevr}
%endif
# safe replacement
Provides:         mariadb-test = %{sameevr}
Provides:         mariadb-test%{?_isa} = %{sameevr}
Conflicts:        mariadb-test < %{sameevr}

%description      test
MariaDB is a multi-user, multi-threaded SQL database server.
MariaDB is a community developed branch of MySQL.
This package contains the regression test suite distributed with the MariaDB
sources.
%endif


%prep
%setup -q -n mariadb-%{version}

# Remove JAR files that upstream puts into tarball
find . -name "*.jar" -type f -exec rm --verbose -f {} \;

%patch4 -p1
%patch7 -p1
%patch9 -p1
%patch37 -p1

sed -i -e 's/2.8.7/2.6.4/g' cmake/cpack_rpm.cmake
# workaround to deploy mariadb@.service on EL7
sed -i 's/IF(NOT CMAKE_VERSION VERSION_LESS 3.3.0 OR NOT RPM)/IF(TRUE)/g' support-files/CMakeLists.txt

# workaround for upstream bug #56342
rm mysql-test/t/ssl_8k_key-master.opt

# generate a list of tests that fail, but are not disabled by upstream
cat %{SOURCE50} | tee -a mysql-test/unstable-tests

# disable some tests failing on different architectures
%ifarch %{arm} aarch64
cat %{SOURCE51} | tee -a mysql-test/unstable-tests
%endif

%ifarch s390 s390x
cat %{SOURCE52} | tee -a mysql-test/unstable-tests
%endif

%ifarch ppc ppc64 ppc64p7 ppc64le
cat %{SOURCE53} | tee -a mysql-test/unstable-tests
%endif

cp %{SOURCE2} %{SOURCE3} %{SOURCE10} %{SOURCE11} %{SOURCE12} \
   %{SOURCE14} %{SOURCE15} %{SOURCE16} %{SOURCE18} %{SOURCE70} scripts

%if %{with galera}
# prepare selinux policy
mkdir selinux
sed 's/mariadb-server-galera/%{name}-server-galera/' %{SOURCE72} > selinux/%{name}-server-galera.te
%endif


# Get version of PCRE, that upstream use
pcre_maj=`grep '^m4_define(pcre_major' pcre/configure.ac | sed -r 's/^m4_define\(pcre_major, \[([0-9]+)\]\)/\1/'`
pcre_min=`grep '^m4_define(pcre_minor' pcre/configure.ac | sed -r 's/^m4_define\(pcre_minor, \[([0-9]+)\]\)/\1/'`

%if %{without unbundled_pcre}
# Check if the PCRE version in macro 'pcre_bundled_version', used in Provides: bundled(...), is the same version as upstream actually bundles
if [ %{pcre_bundled_version} != "$pcre_maj.$pcre_min" ]
then
  echo "\n Error: Bundled PCRE version is not correct. \n\tBundled version number:%{pcre_bundled_version} \n\tUpstream version number: $pcre_maj.$pcre_min\n"
  exit 1
fi
%else
# Check if the PCRE version that upstream use, is the same as the one present in system
pcre_system_version=`pkgconf %{_libdir}/pkgconfig/libpcre.pc --modversion 2>/dev/null `
if [ "$pcre_system_version" != "$pcre_maj.$pcre_min" ]
then
  echo "\n Warning: Error: Bundled PCRE version is not correct. \n\tSystem version number:$pcre_system_version \n\tUpstream version number: $pcre_maj.$pcre_min\n"
fi
%endif # PCRE


%if %{without rocksdb}
rm -r storage/rocksdb/
%endif

# Remove python scripts remains from tokudb upstream (those files are not used anyway)
rm -r storage/tokudb/mysql-test/tokudb/t/*.py



%build

# fail quickly and obviously if user tries to build as root
%if %runselftest
    if [ x"$(id -u)" = "x0" ]; then
        echo "mysql's regression tests fail if run as root."
        echo "If you really need to build the RPM as root, use"
        echo "--nocheck to skip the regression tests."
        exit 1
    fi
%endif

CFLAGS="%{optflags} -D_GNU_SOURCE -D_FILE_OFFSET_BITS=64 -D_LARGEFILE_SOURCE"
# force PIC mode so that we can build libmysqld.so
CFLAGS="$CFLAGS -fPIC"
# Use -ldl for some plugins #1538990
CFLAGS="$CFLAGS -ldl"
# gcc seems to have some bugs on sparc as of 4.4.1, back off optimization; rhbz#529298
# Note: sparc = s390
%ifarch sparc sparcv9 sparc64
CFLAGS=`echo $CFLAGS| sed -e "s|-O2|-O1|g" `
%endif

# Override all optimization flags when making a debug build
%{?with_debug: CFLAGS="$CFLAGS -O0 -g"}

CXXFLAGS="$CFLAGS"
export CFLAGS CXXFLAGS


# The INSTALL_xxx macros have to be specified relative to CMAKE_INSTALL_PREFIX
# so we can't use %%{_datadir} and so forth here.
%cmake . \
         -DBUILD_CONFIG=mysql_release \
         -DFEATURE_SET="community" \
         -DINSTALL_LAYOUT=RPM \
         -DDAEMON_NAME="%{daemon_name}" \
         -DDAEMON_NO_PREFIX="%{daemon_no_prefix}" \
         -DLOG_LOCATION="%{logfile}" \
         -DPID_FILE_DIR="%{pidfiledir}" \
         -DNICE_PROJECT_NAME="MariaDB" \
         -DRPM="%{?rhel:rhel%{rhel}}%{!?rhel:fedora%{fedora}}" \
         -DCMAKE_INSTALL_PREFIX="%{_prefix}" \
         -DINSTALL_SYSCONFDIR="%{_sysconfdir}" \
         -DINSTALL_SYSCONF2DIR="%{_sysconfdir}/my.cnf.d" \
         -DINSTALL_DOCDIR="share/doc/%{_pkgdocdirname}" \
         -DINSTALL_DOCREADMEDIR="share/doc/%{_pkgdocdirname}" \
         -DINSTALL_INCLUDEDIR=include/mysql \
         -DINSTALL_INFODIR=share/info \
         -DINSTALL_LIBDIR="%{_lib}" \
         -DINSTALL_MANDIR=share/man \
         -DINSTALL_MYSQLSHAREDIR=share/%{pkg_name} \
         -DINSTALL_MYSQLTESTDIR=%{?with_test:share/mysql-test}%{!?with_test:} \
         -DINSTALL_PLUGINDIR="%{_lib}/%{pkg_name}/plugin" \
         -DINSTALL_SBINDIR=libexec \
         -DINSTALL_SCRIPTDIR=bin \
         -DINSTALL_SQLBENCHDIR=share \
         -DINSTALL_SUPPORTFILESDIR=share/%{pkg_name} \
         -DINSTALL_PCDIR=%{_lib}/pkgconfig \
         -DMYSQL_DATADIR="%{dbdatadir}" \
         -DMYSQL_UNIX_ADDR="/var/lib/mysql/mysql.sock" \
         -DTMPDIR=/var/tmp \
         -DENABLED_LOCAL_INFILE=ON \
         -DENABLE_DTRACE=ON \
         -DSECURITY_HARDENED=ON \
         -DWITH_EMBEDDED_SERVER=%{?with_embedded:ON}%{!?with_embedded:OFF} \
         -DWITH_READLINE=ON \
         -DWITH_MARIABACKUP=%{?with_backup:ON}%{!?with_backup:NO} \
         -DWITH_UNIT_TESTS=%{?with_test:ON}%{!?with_test:NO} \
         -DCONC_WITH_SSL=%{?with_clibrary:ON}%{!?with_clibrary:NO} \
         -DWITH_SSL=system \
         -DWITH_ZLIB=system \
         -DWITH_JEMALLOC=no \
         -DLZ4_LIBS=%{_libdir}/liblz4.so \
         -DWITH_INNODB_LZ4=%{?with_lz4:ON}%{!?with_lz4:OFF} \
         -DPLUGIN_MROONGA=%{?with_mroonga:DYNAMIC}%{!?with_mroonga:NO} \
         -DPLUGIN_OQGRAPH=%{?with_oqgraph:DYNAMIC}%{!?with_oqgraph:NO} \
         -DPLUGIN_CRACKLIB_PASSWORD_CHECK=%{?with_cracklib:DYNAMIC}%{!?with_cracklib:NO} \
         -DPLUGIN_ROCKSDB=%{?with_rocksdb:DYNAMIC}%{!?with_rocksdb:NO} \
         -DPLUGIN_SPHINX=%{?with_sphinx:DYNAMIC}%{!?with_sphinx:NO} \
         -DPLUGIN_TOKUDB=%{?with_tokudb:DYNAMIC}%{!?with_tokudb:NO} \
         -DPLUGIN_CONNECT=%{?with_connect:DYNAMIC}%{!?with_connect:NO} \
         -DWITH_CASSANDRA=%{?with_cassandra:TRUE}%{!?with_cassandra:FALSE} \
         -DPLUGIN_CACHING_SHA2_PASSWORD=%{?with_clibrary:DYNAMIC}%{!?with_clibrary:OFF} \
         -DPLUGIN_AWS_KEY_MANAGEMENT=NO \
         -DCONNECT_WITH_MONGO=OFF \
         -DCONNECT_WITH_JDBC=OFF \
%{?with_debug: -DCMAKE_BUILD_TYPE=Debug -DWITH_ASAN=OFF -DWITH_INNODB_EXTRA_DEBUG=ON -DWITH_VALGRIND=ON}

# Print all Cmake options values
# cmake -LAH for List Advanced Help
cmake -L

make %{?_smp_mflags} VERBOSE=1


# build selinux policy
%if %{with galera}
pushd selinux
make -f /usr/share/selinux/devel/Makefile %{name}-server-galera.pp
%endif

%install
make DESTDIR=%{buildroot} install

# multilib header support #1625157
for header in mysql/server/my_config.h mysql/server/private/config.h; do
%multilib_fix_c_header --file %{_includedir}/$header
done

%if 0%{?fedora} < 28
%multilib_fix_c_header --file %{_includedir}/mysql/mariadb_version.h
%endif


ln -s mysql_config.1.gz %{buildroot}%{_mandir}/man1/mariadb_config.1.gz

# multilib support for shell scripts
# we only apply this to known Red Hat multilib arches, per bug #181335
if [ %multilib_capable ]
then
mv %{buildroot}%{_bindir}/mysql_config %{buildroot}%{_bindir}/mysql_config-%{__isa_bits}
install -p -m 0755 scripts/mysql_config_multilib %{buildroot}%{_bindir}/mysql_config
# Copy manual page for multilib mysql_config; https://jira.mariadb.org/browse/MDEV-11961
ln -s mysql_config.1 %{buildroot}%{_mandir}/man1/mysql_config-%{__isa_bits}.1
fi

# Upstream install this into arch-independent directory
# Reported to upstream as: https://jira.mariadb.org/browse/MDEV-14340
# TODO: check, if it changes location inside that file depending on values passed to Cmake
mkdir -p %{buildroot}/%{_libdir}/pkgconfig
mv %{buildroot}/%{_datadir}/pkgconfig/*.pc %{buildroot}/%{_libdir}/pkgconfig
%if %{without clibrary}
# Client part should be included in package 'mariadb-connector-c'
rm %{buildroot}%{_libdir}/pkgconfig/libmariadb.pc
%endif

# install INFO_SRC, INFO_BIN into libdir (upstream thinks these are doc files,
# but that's pretty wacko --- see also %%{name}-file-contents.patch)
install -p -m 644 Docs/INFO_SRC %{buildroot}%{_libdir}/%{pkg_name}/
install -p -m 644 Docs/INFO_BIN %{buildroot}%{_libdir}/%{pkg_name}/
rm -r %{buildroot}%{_datadir}/doc/%{_pkgdocdirname}/MariaDB-server-%{version}/

# Logfile creation
mkdir -p %{buildroot}%{logfiledir}
chmod 0750 %{buildroot}%{logfiledir}
touch %{buildroot}%{logfile}

# current setting in my.cnf is to use /var/run/mariadb for creating pid file,
# however since my.cnf is not updated by RPM if changed, we need to create mysqld
# as well because users can have odd settings in their /etc/my.cnf
mkdir -p %{buildroot}%{pidfiledir}
install -p -m 0755 -d %{buildroot}%{dbdatadir}

%if %{with config}
install -D -p -m 0644 scripts/my.cnf %{buildroot}%{_sysconfdir}/my.cnf
%else
rm scripts/my.cnf
%endif

# use different config file name for each variant of server (mariadb / mysql)
mv %{buildroot}%{_sysconfdir}/my.cnf.d/server.cnf %{buildroot}%{_sysconfdir}/my.cnf.d/%{pkg_name}-server.cnf

%if 0%{?fedora} >= 21 || 0%{?rhel} >= 8
# Rename sysusers and tmpfiles config files, they should be named after the software they belong to
mv %{buildroot}%{_sysusersdir}/sysusers.conf %{buildroot}%{_sysusersdir}/%{daemon_name}.conf
%else
rm %{buildroot}%{_sysusersdir}/sysusers.conf
%endif

# remove SysV init script and a symlink to that, we pack our very own
rm %{buildroot}%{_sysconfdir}/init.d/mysql
rm %{buildroot}%{_libexecdir}/rcmysql
# install systemd unit files and scripts for handling server startup
install -D -p -m 644 scripts/mysql.service %{buildroot}%{_unitdir}/%{daemon_name}.service
install -D -p -m 644 scripts/mysql@.service %{buildroot}%{_unitdir}/%{daemon_name}@.service
# Remove the upstream version
rm %{buildroot}%{_tmpfilesdir}/tmpfiles.conf
# Install downstream version
install -D -p -m 0644 scripts/mysql.tmpfiles.d %{buildroot}%{_tmpfilesdir}/%{daemon_name}.conf
%if 0%{?mysqld_pid_dir:1}
echo "d %{pidfiledir} 0755 mysql mysql -" >>%{buildroot}%{_tmpfilesdir}/%{daemon_name}.conf
%endif #pid

# helper scripts for service starting
install -p -m 755 scripts/mysql-prepare-db-dir %{buildroot}%{_libexecdir}/mysql-prepare-db-dir
install -p -m 755 scripts/mysql-check-socket %{buildroot}%{_libexecdir}/mysql-check-socket
install -p -m 755 scripts/mysql-check-upgrade %{buildroot}%{_libexecdir}/mysql-check-upgrade
install -p -m 644 scripts/mysql-scripts-common %{buildroot}%{_libexecdir}/mysql-scripts-common

# install aditional galera selinux policy
%if %{with galera}
install -p -m 644 -D selinux/%{name}-server-galera.pp %{buildroot}%{_datadir}/selinux/packages/%{name}/%{name}-server-galera.pp
%endif

%if %{with test}
# mysql-test includes one executable that doesn't belong under /usr/share, so move it and provide a symlink
mv %{buildroot}%{_datadir}/mysql-test/lib/My/SafeProcess/my_safe_process %{buildroot}%{_bindir}
ln -s ../../../../../bin/my_safe_process %{buildroot}%{_datadir}/mysql-test/lib/My/SafeProcess/my_safe_process
# Provide symlink expected by RH QA tests
ln -s unstable-tests %{buildroot}%{_datadir}/mysql-test/rh-skipped-tests.list
%endif


# Client that uses libmysqld embedded server.
# Pretty much like normal mysql command line client, but it doesn't require a running mariadb server.
%{?with_embedded:rm %{buildroot}%{_bindir}/mysql_embedded}
rm %{buildroot}%{_mandir}/man1/mysql_embedded.1*
# Static libraries
rm %{buildroot}%{_libdir}/*.a
# This script creates the MySQL system tables and starts the server.
# Upstream says:
#   It looks like it's just "mysql_install_db && mysqld_safe"
#   I've never heard of anyone using it, I'd say, no need to pack it.
rm %{buildroot}%{_datadir}/%{pkg_name}/binary-configure
# FS files first-bytes recoginiton
# Not updated by upstream since nobody realy use that
rm %{buildroot}%{_datadir}/%{pkg_name}/magic

# Upstream ships them because of, https://jira.mariadb.org/browse/MDEV-10797
# In Fedora we use our own systemd unit files and scripts
rm %{buildroot}%{_datadir}/%{pkg_name}/mysql.server
rm %{buildroot}%{_datadir}/%{pkg_name}/mysqld_multi.server

# Binary for monitoring MySQL performance
# Shipped as a standalona package in Fedora
rm %{buildroot}%{_bindir}/mytop

# put logrotate script where it needs to be
mkdir -p %{buildroot}%{logrotateddir}
mv %{buildroot}%{_datadir}/%{pkg_name}/mysql-log-rotate %{buildroot}%{logrotateddir}/%{daemon_name}
chmod 644 %{buildroot}%{logrotateddir}/%{daemon_name}

# copy additional docs into build tree so %%doc will find them
install -p -m 0644 %{SOURCE5} %{basename:%{SOURCE5}}
install -p -m 0644 %{SOURCE6} %{basename:%{SOURCE6}}
install -p -m 0644 %{SOURCE7} %{basename:%{SOURCE7}}
install -p -m 0644 %{SOURCE16} %{basename:%{SOURCE16}}
install -p -m 0644 %{SOURCE71} %{basename:%{SOURCE71}}

# install galera config file
sed -i -r 's|^wsrep_provider=none|wsrep_provider=%{_libdir}/galera/libgalera_smm.so|' support-files/wsrep.cnf
install -p -m 0644 support-files/wsrep.cnf %{buildroot}%{_sysconfdir}/my.cnf.d/galera.cnf
# install the clustercheck script
mkdir -p %{buildroot}%{_sysconfdir}/sysconfig
touch %{buildroot}%{_sysconfdir}/sysconfig/clustercheck
install -p -m 0755 scripts/clustercheck %{buildroot}%{_bindir}/clustercheck

# remove duplicate logrotate script
rm %{buildroot}%{logrotateddir}/mysql
# Remove AppArmor files
rm -r %{buildroot}%{_datadir}/%{pkg_name}/policy/apparmor

# script without shebang: https://jira.mariadb.org/browse/MDEV-14266
chmod -x %{buildroot}%{_datadir}/sql-bench/myisam.cnf

# Disable plugins
%if %{with gssapi}
sed -i 's/^plugin-load-add/#plugin-load-add/' %{buildroot}%{_sysconfdir}/my.cnf.d/auth_gssapi.cnf
%endif
%if %{with cracklib}
sed -i 's/^plugin-load-add/#plugin-load-add/' %{buildroot}%{_sysconfdir}/my.cnf.d/cracklib_password_check.cnf
%endif

%if %{without embedded}
rm %{buildroot}%{_mandir}/man1/{mysql_client_test_embedded,mysqltest_embedded}.1*
%endif

%if %{without clibrary}
rm %{buildroot}%{_sysconfdir}/my.cnf.d/client.cnf
# Client library and links
rm %{buildroot}%{_libdir}/libmariadb*.so.*
unlink %{buildroot}%{_libdir}/libmysqlclient.so
unlink %{buildroot}%{_libdir}/libmysqlclient_r.so
unlink %{buildroot}%{_libdir}/libmariadb.so
# Client plugins
rm %{buildroot}%{_libdir}/%{pkg_name}/plugin/{dialog.so,mysql_clear_password.so,sha256_password.so,auth_gssapi_client.so}
%endif

%if %{without clibrary} || %{without devel}
rm %{buildroot}%{_bindir}/mysql_config*
rm %{buildroot}%{_bindir}/mariadb_config
rm %{buildroot}%{_mandir}/man1/mysql_config*.1*
unlink %{buildroot}%{_mandir}/man1/mariadb_config.1*
%endif

%if %{without clibrary} && %{with devel}
# This files are already included in mariadb-connector-c
rm %{buildroot}%{_includedir}/mysql/mysql_version.h
rm %{buildroot}%{_includedir}/mysql/{errmsg.h,ma_list.h,ma_pvio.h,mariadb_com.h,\
mariadb_ctype.h,mariadb_dyncol.h,mariadb_stmt.h,mariadb_version.h,ma_tls.h,mysqld_error.h,mysql.h}
rm -r %{buildroot}%{_includedir}/mysql/{mariadb,mysql}
%endif

%if %{without devel}
rm -r %{buildroot}%{_includedir}/mysql
rm %{buildroot}%{_datadir}/aclocal/mysql.m4
rm %{buildroot}%{_libdir}/pkgconfig/mariadb.pc
%if %{with clibrary}
rm %{buildroot}%{_libdir}/libmariadb*.so
unlink %{buildroot}%{_libdir}/libmysqlclient.so
unlink %{buildroot}%{_libdir}/libmysqlclient_r.so
%endif # clibrary
%endif # devel

%if %{with parallel_libs}
unlink %{buildroot}%{_libdir}/libmysqlclient.so
unlink %{buildroot}%{_libdir}/libmysqlclient_r.so
%endif

%if %{without client}
rm %{buildroot}%{_bindir}/{msql2mysql,mysql,mysql_find_rows,\
mysql_plugin,mysql_waitpid,mysqlaccess,mysqladmin,mysqlbinlog,mysqlcheck,\
mysqldump,mysqlimport,mysqlshow,mysqlslap}
rm %{buildroot}%{_mandir}/man1/{msql2mysql,mysql,mysql_find_rows,\
mysql_plugin,mysql_waitpid,mysqlaccess,mysqladmin,mysqlbinlog,mysqlcheck,\
mysqldump,mysqlimport,mysqlshow,mysqlslap}.1*
%endif

%if %{without tokudb}
# because upstream ships manpages for tokudb even on architectures that tokudb doesn't support
rm %{buildroot}%{_mandir}/man1/tokuftdump.1*
rm %{buildroot}%{_mandir}/man1/tokuft_logprint.1*
%else
%if 0%{?fedora} >= 28 || 0%{?rhel} > 7
mkdir -p %{buildroot}%{_unitdir}/mariadb.service.d
echo -e '[Service]\nEnvironment="LD_PRELOAD=%{_libdir}/libjemalloc.so.2"' >> %{buildroot}%{_unitdir}/mariadb.service.d/tokudb.conf
%endif
%endif

%if %{without config}
rm %{buildroot}%{_sysconfdir}/my.cnf
rm %{buildroot}%{_sysconfdir}/my.cnf.d/mysql-clients.cnf
rm %{buildroot}%{_sysconfdir}/my.cnf.d/enable_encryption.preset
%endif

%if %{without common}
rm -r %{buildroot}%{_datadir}/%{pkg_name}/charsets
%endif

%if %{without gssapi}
rm -r %{buildroot}/etc/my.cnf.d/auth_gssapi.cnf
%endif

%if %{without errmsg}
rm %{buildroot}%{_datadir}/%{pkg_name}/errmsg-utf8.txt
rm -r %{buildroot}%{_datadir}/%{pkg_name}/{english,czech,danish,dutch,estonian,\
french,german,greek,hungarian,italian,japanese,korean,norwegian,norwegian-ny,\
polish,portuguese,romanian,russian,serbian,slovak,spanish,swedish,ukrainian,hindi}
%endif

%if %{without bench}
rm -r %{buildroot}%{_datadir}/sql-bench
%endif

%if %{without test}
%if %{with embedded}
rm %{buildroot}%{_bindir}/{mysqltest_embedded,mysql_client_test_embedded}
rm %{buildroot}%{_mandir}/man1/{mysqltest_embedded,mysql_client_test_embedded}.1*
%endif # embedded
rm %{buildroot}%{_bindir}/{mysql_client_test,mysqltest}
rm %{buildroot}%{_mandir}/man1/{mysql_client_test,my_safe_process,mysqltest}.1*
rm %{buildroot}%{_mandir}/man1/{mysql-test-run,mysql-stress-test}.pl.1*
%endif # test

%if %{without galera}
rm %{buildroot}%{_sysconfdir}/my.cnf.d/galera.cnf
rm %{buildroot}%{_sysconfdir}/sysconfig/clustercheck
rm %{buildroot}%{_bindir}/{clustercheck,galera_new_cluster}
rm %{buildroot}%{_bindir}/galera_recovery
rm %{buildroot}%{_datadir}/%{pkg_name}/systemd/use_galera_new_cluster.conf
%endif

%if %{without rocksdb}
rm %{buildroot}%{_mandir}/man1/mysql_ldb.1*
%endif


%check
%if %{with test}
%if %runselftest
# hack to let 32- and 64-bit tests run concurrently on same build machine
export MTR_PARALLEL=1
# builds might happen at the same host, avoid collision
export MTR_BUILD_THREAD=%{__isa_bits}

# The cmake build scripts don't provide any simple way to control the
# options for mysql-test-run, so ignore the make target and just call it
# manually.  Nonstandard options chosen are:
# --force to continue tests after a failure
# no retries please
# test SSL with --ssl
# skip tests that are listed in rh-skipped-tests.list
# avoid redundant test runs with --binlog-format=mixed
# increase timeouts to prevent unwanted failures during mass rebuilds

# Usefull arguments:
#    --do-test=mysql_client_test_nonblock \
#    --skip-rpl
#    --suite=roles

(
  set -ex

  cd mysql-test
  export common_testsuite_arguments=" --parallel=auto --force --retry=1 --suite-timeout=900 --testcase-timeout=30 --mysqld=--binlog-format=mixed --force-restart --shutdown-timeout=60 --max-test-fail=5 "

  # If full testsuite has already been run on this version and we don't explicitly want the full testsuite to be run
  if [[ "%{last_tested_version}" == "%{version}" ]] && [[ %{force_run_testsuite} -eq 0 ]]
  then
    # in further rebuilds only run the basic "main" suite (~800 tests)
    echo "running only base testsuite"
    perl ./mysql-test-run.pl $common_testsuite_arguments --ssl --suite=main --mem --skip-test-list=unstable-tests
  fi

  # If either this version wasn't marked as tested yet or I explicitly want to run the testsuite, run everything we have (~4000 test)
  if [[ "%{last_tested_version}" != "%{version}" ]] || [[ %{force_run_testsuite} -ne 0 ]]
  then
    echo "running advanced testsuite"
    perl ./mysql-test-run.pl $common_testsuite_arguments --ssl --big-test --skip-test=spider \
    %if %{ignore_testsuite_result}
      --max-test-fail=9999 || :
    %else
      --skip-test-list=unstable-tests
    %endif
    # Second run for the SPIDER suites that fail with SCA (ssl self signed certificate)
    perl ./mysql-test-run.pl $common_testsuite_arguments --skip-ssl --big-test --mem --suite=spider,spider/bg \
    %if %{ignore_testsuite_result}
      --max-test-fail=999 || :
    %endif
  # blank line
  fi
)

%endif # if dry run
%endif # with test



%pre server
/usr/sbin/groupadd -g 27 -o -r mysql >/dev/null 2>&1 || :
/usr/sbin/useradd -M -N -g mysql -o -r -d %{mysqluserhome} -s /sbin/nologin \
  -c "MySQL Server" -u 27 mysql >/dev/null 2>&1 || :

%if %{with clibrary}
%ldconfig_scriptlets libs
%endif

%if %{with embedded}
%ldconfig_scriptlets embedded
%endif

%if %{with galera}
%post server-galera
# Do what README at support-files/policy/selinux/README and upstream page
# http://galeracluster.com/documentation-webpages/firewallsettings.html recommend:
semanage port -a -t mysqld_port_t -p tcp 4568 >/dev/null 2>&1 || :
semanage port -a -t mysqld_port_t -p tcp 4567 >/dev/null 2>&1 || :
semanage port -a -t mysqld_port_t -p udp 4567 >/dev/null 2>&1 || :
semodule -i %{_datadir}/selinux/packages/%{name}/%{name}-server-galera.pp >/dev/null 2>&1 || :
%endif

%post server
%systemd_post %{daemon_name}.service

%preun server
%systemd_preun %{daemon_name}.service

%if %{with galera}
%postun server-galera
if [ $1 -eq 0 ]; then
    semodule -r %{name}-server-galera 2>/dev/null || :
fi
%endif

%postun server
%systemd_postun_with_restart %{daemon_name}.service



%if %{with client}
%files
%{_bindir}/msql2mysql
%{_bindir}/mysql
%{_bindir}/mysql_find_rows
%{_bindir}/mysql_plugin
%{_bindir}/mysql_waitpid
%{_bindir}/mysqlaccess
%{_bindir}/mysqladmin
%{_bindir}/mysqlbinlog
%{_bindir}/mysqlcheck
%{_bindir}/mysqldump
%{_bindir}/mysqlimport
%{_bindir}/mysqlshow
%{_bindir}/mysqlslap

%{_mandir}/man1/msql2mysql.1*
%{_mandir}/man1/mysql.1*
%{_mandir}/man1/mysql_find_rows.1*
%{_mandir}/man1/mysql_plugin.1*
%{_mandir}/man1/mysql_waitpid.1*
%{_mandir}/man1/mysqlaccess.1*
%{_mandir}/man1/mysqladmin.1*
%{_mandir}/man1/mysqlbinlog.1*
%{_mandir}/man1/mysqlcheck.1*
%{_mandir}/man1/mysqldump.1*
%{_mandir}/man1/mysqlimport.1*
%{_mandir}/man1/mysqlshow.1*
%{_mandir}/man1/mysqlslap.1*
%endif

%if %{with clibrary}
%files libs
%{_libdir}/libmariadb.so.*
%config(noreplace) %{_sysconfdir}/my.cnf.d/client.cnf
%endif

%if %{with config}
%files config
# although the default my.cnf contains only server settings, we put it in the
# common package because it can be used for client settings too.
%dir %{_sysconfdir}/my.cnf.d
%config(noreplace) %{_sysconfdir}/my.cnf
%config(noreplace) %{_sysconfdir}/my.cnf.d/mysql-clients.cnf
%config(noreplace) %{_sysconfdir}/my.cnf.d/enable_encryption.preset
%endif

%if %{with common}
%files common
%doc %{_datadir}/doc/%{_pkgdocdirname}
%dir %{_datadir}/%{pkg_name}
%{_datadir}/%{pkg_name}/charsets
%if %{with clibrary}
%{_libdir}/%{pkg_name}/plugin/dialog.so
%{_libdir}/%{pkg_name}/plugin/mysql_clear_password.so
%endif # clibrary
%endif # common

%if %{with errmsg}
%files errmsg
%{_datadir}/%{pkg_name}/errmsg-utf8.txt
%{_datadir}/%{pkg_name}/english
%lang(cs) %{_datadir}/%{pkg_name}/czech
%lang(da) %{_datadir}/%{pkg_name}/danish
%lang(nl) %{_datadir}/%{pkg_name}/dutch
%lang(et) %{_datadir}/%{pkg_name}/estonian
%lang(fr) %{_datadir}/%{pkg_name}/french
%lang(de) %{_datadir}/%{pkg_name}/german
%lang(el) %{_datadir}/%{pkg_name}/greek
%lang(hi) %{_datadir}/%{pkg_name}/hindi
%lang(hu) %{_datadir}/%{pkg_name}/hungarian
%lang(it) %{_datadir}/%{pkg_name}/italian
%lang(ja) %{_datadir}/%{pkg_name}/japanese
%lang(ko) %{_datadir}/%{pkg_name}/korean
%lang(no) %{_datadir}/%{pkg_name}/norwegian
%lang(no) %{_datadir}/%{pkg_name}/norwegian-ny
%lang(pl) %{_datadir}/%{pkg_name}/polish
%lang(pt) %{_datadir}/%{pkg_name}/portuguese
%lang(ro) %{_datadir}/%{pkg_name}/romanian
%lang(ru) %{_datadir}/%{pkg_name}/russian
%lang(sr) %{_datadir}/%{pkg_name}/serbian
%lang(sk) %{_datadir}/%{pkg_name}/slovak
%lang(es) %{_datadir}/%{pkg_name}/spanish
%lang(sv) %{_datadir}/%{pkg_name}/swedish
%lang(uk) %{_datadir}/%{pkg_name}/ukrainian
%endif

%if %{with galera}
%files server-galera
%doc Docs/README-wsrep
%license LICENSE.clustercheck
%{_bindir}/clustercheck
%{_bindir}/galera_new_cluster
%{_bindir}/galera_recovery
%{_datadir}/%{pkg_name}/systemd/use_galera_new_cluster.conf
%config(noreplace) %{_sysconfdir}/my.cnf.d/galera.cnf
%attr(0640,root,root) %ghost %config(noreplace) %{_sysconfdir}/sysconfig/clustercheck
%{_datadir}/selinux/packages/%{name}/%{name}-server-galera.pp
%{_mandir}/man1/galera_new_cluster.1*
%{_mandir}/man1/galera_recovery.1*
%endif

%files server
%doc README.mysql-cnf

%{_bindir}/aria_chk
%{_bindir}/aria_dump_log
%{_bindir}/aria_ftdump
%{_bindir}/aria_pack
%{_bindir}/aria_read_log
%{_bindir}/mariadb-service-convert
%{_bindir}/myisamchk
%{_bindir}/myisam_ftdump
%{_bindir}/myisamlog
%{_bindir}/myisampack
%{_bindir}/my_print_defaults
%{_bindir}/mysql_install_db
%{_bindir}/mysql_secure_installation
%{_bindir}/mysql_tzinfo_to_sql
%{_bindir}/mysql_upgrade
%{_bindir}/mysqld_safe
%{_bindir}/mysqld_safe_helper
%{_bindir}/innochecksum
%{_bindir}/replace
%{_bindir}/resolve_stack_dump
%{_bindir}/resolveip
# wsrep_sst_common should be moved to /usr/share/mariadb: https://jira.mariadb.org/browse/MDEV-14296
%{_bindir}/wsrep_*

%config(noreplace) %{_sysconfdir}/my.cnf.d/%{pkg_name}-server.cnf

%{_libexecdir}/mysqld

%{_libdir}/%{pkg_name}/INFO_SRC
%{_libdir}/%{pkg_name}/INFO_BIN
%if %{without common}
%dir %{_datadir}/%{pkg_name}
%endif

%dir %{_libdir}/%{pkg_name}
%dir %{_libdir}/%{pkg_name}/plugin
%{_libdir}/%{pkg_name}/plugin/*
%{?with_oqgraph:%exclude %{_libdir}/%{pkg_name}/plugin/ha_oqgraph.so}
%{?with_connect:%exclude %{_libdir}/%{pkg_name}/plugin/ha_connect.so}
%{?with_cracklib:%exclude %{_libdir}/%{pkg_name}/plugin/cracklib_password_check.so}
%{?with_rocksdb:%exclude %{_libdir}/%{pkg_name}/plugin/ha_rocksdb.so}
%{?with_tokudb:%exclude %{_libdir}/%{pkg_name}/plugin/ha_tokudb.so}
%{?with_gssapi:%exclude %{_libdir}/%{pkg_name}/plugin/auth_gssapi.so}
%{?with_sphinx:%exclude %{_libdir}/%{pkg_name}/plugin/ha_sphinx.so}
%{?with_cassandra:%exclude %{_libdir}/%{pkg_name}/plugin/ha_cassandra.so}
%if %{with clibrary}
%exclude %{_libdir}/%{pkg_name}/plugin/dialog.so
%exclude %{_libdir}/%{pkg_name}/plugin/mysql_clear_password.so
%endif

%{_mandir}/man1/aria_chk.1*
%{_mandir}/man1/aria_dump_log.1*
%{_mandir}/man1/aria_ftdump.1*
%{_mandir}/man1/aria_pack.1*
%{_mandir}/man1/aria_read_log.1*
%{_mandir}/man1/mariadb-service-convert.1*
%{_mandir}/man1/myisamchk.1*
%{_mandir}/man1/myisamlog.1*
%{_mandir}/man1/myisampack.1*
%{_mandir}/man1/myisam_ftdump.1*
%{_mandir}/man1/my_print_defaults.1*
%{_mandir}/man1/mysql.server.1*
%{_mandir}/man1/mysql_install_db.1*
%{_mandir}/man1/mysql_secure_installation.1*
%{_mandir}/man1/mysql_tzinfo_to_sql.1*
%{_mandir}/man1/mysql_upgrade.1*
%{_mandir}/man1/mysqld_safe.1*
%{_mandir}/man1/mysqld_safe_helper.1*
%{_mandir}/man1/innochecksum.1*
%{_mandir}/man1/replace.1*
%{_mandir}/man1/resolveip.1*
%{_mandir}/man1/resolve_stack_dump.1*
%{_mandir}/man8/mysqld.8*
%{_mandir}/man1/wsrep_*.1*

%{_datadir}/%{pkg_name}/fill_help_tables.sql
%{_datadir}/%{pkg_name}/install_spider.sql
%{_datadir}/%{pkg_name}/maria_add_gis_sp.sql
%{_datadir}/%{pkg_name}/maria_add_gis_sp_bootstrap.sql
%{_datadir}/%{pkg_name}/mysql_system_tables.sql
%{_datadir}/%{pkg_name}/mysql_system_tables_data.sql
%{_datadir}/%{pkg_name}/mysql_test_data_timezone.sql
%{_datadir}/%{pkg_name}/mysql_to_mariadb.sql
%{_datadir}/%{pkg_name}/mysql_performance_tables.sql
%{_datadir}/%{pkg_name}/mysql_test_db.sql
%if %{with mroonga}
%{_datadir}/%{pkg_name}/mroonga/install.sql
%{_datadir}/%{pkg_name}/mroonga/uninstall.sql
%license %{_datadir}/%{pkg_name}/mroonga/COPYING
%license %{_datadir}/%{pkg_name}/mroonga/AUTHORS
%license %{_datadir}/groonga-normalizer-mysql/lgpl-2.0.txt
%license %{_datadir}/groonga/COPYING
%doc %{_datadir}/groonga-normalizer-mysql/README.md
%doc %{_datadir}/groonga/README.md
%endif
%{_datadir}/%{pkg_name}/my-*.cnf
%{_datadir}/%{pkg_name}/wsrep.cnf
%{_datadir}/%{pkg_name}/wsrep_notify
%dir %{_datadir}/%{pkg_name}/policy
%dir %{_datadir}/%{pkg_name}/policy/selinux
%{_datadir}/%{pkg_name}/policy/selinux/README
%{_datadir}/%{pkg_name}/policy/selinux/mariadb-server.*
%{_datadir}/%{pkg_name}/policy/selinux/mariadb.*
%{_datadir}/%{pkg_name}/systemd/mariadb.service
%{_datadir}/%{pkg_name}/systemd/mariadb@.service

%{_unitdir}/%{daemon_name}*
%{?with_tokudb:%exclude %{_unitdir}/mariadb.service.d/tokudb.conf}
%{_libexecdir}/mysql-prepare-db-dir
%{_libexecdir}/mysql-check-socket
%{_libexecdir}/mysql-check-upgrade
%{_libexecdir}/mysql-scripts-common

%attr(0755,mysql,mysql) %dir %{pidfiledir}
%attr(0755,mysql,mysql) %dir %{dbdatadir}
%attr(0750,mysql,mysql) %dir %{logfiledir}
# This does what it should.
# RPMLint error "conffile-without-noreplace-flag /var/log/mariadb/mariadb.log" is false positive.
%attr(0640,mysql,mysql) %config %ghost %verify(not md5 size mtime) %{logfile}
%config(noreplace) %{logrotateddir}/%{daemon_name}

%{_tmpfilesdir}/%{daemon_name}.conf
%if 0%{?fedora} >= 21 || 0%{?rhel} >= 8
%{_sysusersdir}/%{daemon_name}.conf
%endif

%if %{with cracklib}
%files cracklib-password-check
%config(noreplace) %{_sysconfdir}/my.cnf.d/cracklib_password_check.cnf
%{_libdir}/%{pkg_name}/plugin/cracklib_password_check.so
%endif

%if %{with backup}
%files backup
%{_bindir}/mariabackup
%{_bindir}/mbstream
%{_mandir}/man1/mariabackup.1*
%{_mandir}/man1/mbstream.1*
%endif

%if %{with rocksdb}
%files rocksdb-engine
%config(noreplace) %{_sysconfdir}/my.cnf.d/rocksdb.cnf
%{_bindir}/myrocks_hotbackup
%{_bindir}/mysql_ldb
%{_bindir}/sst_dump
%{_libdir}/%{pkg_name}/plugin/ha_rocksdb.so
%{_mandir}/man1/mysql_ldb.1*
%endif

%if %{with tokudb}
%files tokudb-engine
%{_bindir}/tokuftdump
%{_bindir}/tokuft_logprint
%{_mandir}/man1/tokuftdump.1*
%{_mandir}/man1/tokuft_logprint.1*
%config(noreplace) %{_sysconfdir}/my.cnf.d/tokudb.cnf
%{_libdir}/%{pkg_name}/plugin/ha_tokudb.so
%{_unitdir}/mariadb.service.d/tokudb.conf
%endif

%if %{with gssapi}
%files gssapi-server
%{_libdir}/%{pkg_name}/plugin/auth_gssapi.so
%config(noreplace) %{_sysconfdir}/my.cnf.d/auth_gssapi.cnf
%endif

%if %{with sphinx}
%files sphinx-engine
%{_libdir}/%{pkg_name}/plugin/ha_sphinx.so
%endif

%if %{with oqgraph}
%files oqgraph-engine
%config(noreplace) %{_sysconfdir}/my.cnf.d/oqgraph.cnf
%{_libdir}/%{pkg_name}/plugin/ha_oqgraph.so
%endif

%if %{with connect}
%files connect-engine
%config(noreplace) %{_sysconfdir}/my.cnf.d/connect.cnf
%{_libdir}/%{pkg_name}/plugin/ha_connect.so
%endif

%if %{with cassandra}
%files cassandra-engine
%config(noreplace) %{_sysconfdir}/my.cnf.d/cassandra.cnf
%{_libdir}/%{pkg_name}/plugin/ha_cassandra.so
%endif

%files server-utils
# Perl utilities
%{_bindir}/mysql_convert_table_format
%{_bindir}/mysql_fix_extensions
%{_bindir}/mysql_setpermission
%{_bindir}/mysqldumpslow
%{_bindir}/mysqld_multi
%{_bindir}/mysqlhotcopy
%{_mandir}/man1/mysql_convert_table_format.1*
%{_mandir}/man1/mysql_fix_extensions.1*
%{_mandir}/man1/mysqldumpslow.1*
%{_mandir}/man1/mysqld_multi.1*
%{_mandir}/man1/mysqlhotcopy.1*
%{_mandir}/man1/mysql_setpermission.1*
# Utilities that can be used remotely
%{_bindir}/perror
%{_mandir}/man1/perror.1*

%if %{with devel}
%files devel
%{_includedir}/*
%{_datadir}/aclocal/mysql.m4
%{_libdir}/pkgconfig/mariadb.pc
%if %{with clibrary}
%{_libdir}/pkgconfig/libmariadb.pc
%if %{without parallel_libs}
%{_libdir}/{libmysqlclient.so.18,libmariadb.so,libmysqlclient.so,libmysqlclient_r.so}
%endif
%{_bindir}/mysql_config*
%{_bindir}/mariadb_config*
%{_libdir}/libmariadb.so
%if %{without parallel_libs}
%{_libdir}/libmysqlclient.so
%{_libdir}/libmysqlclient_r.so
%endif
%{_mandir}/man1/mysql_config*
%{_mandir}/man1/mariadb_config*
%endif
%endif

%if %{with embedded}
%files embedded
%{_libdir}/libmysqld.so.*

%files embedded-devel
%{_libdir}/libmysqld.so
%endif

%if %{with bench}
%files bench
%{_datadir}/sql-bench
%doc %{_datadir}/sql-bench/README
%endif

%if %{with test}
%files test
%if %{with embedded}
%{_bindir}/mysql_client_test_embedded
%{_bindir}/mysqltest_embedded
%{_mandir}/man1/mysql_client_test_embedded.1*
%{_mandir}/man1/mysqltest_embedded.1*
%endif
%{_bindir}/mysql_client_test
%{_bindir}/my_safe_process
%{_bindir}/mysqltest
%attr(-,mysql,mysql) %{_datadir}/mysql-test
%{_mandir}/man1/mysql_client_test.1*
%{_mandir}/man1/my_safe_process.1*
%{_mandir}/man1/mysqltest.1*
%{_mandir}/man1/mysql-stress-test.pl.1*
%{_mandir}/man1/mysql-test-run.pl.1*
%endif

%changelog
* Wed Oct 10 2019 Luis M. Segundo <blackfile@fedoraproject.org> - 3:10.2.27-2
- Add unpackaged file

* Wed Oct 10 2019 Luis M. Segundo <blackfile@fedoraproject.org> - 3:10.2.27-1
- Update upstream to 10.2.27

* Thu Aug 15 2019 Carl George <carl@george.computer> - 3:10.2.26-1
- Latest upstream

* Wed Jul 24 2019 Carl George <carl@george.computer> - 3:10.2.25-1
- Latest upstream

* Mon May 27 2019 Carl George <carl@george.computer> - 3:10.2.24-1
- Latest upstream

* Sat May 04 2019 Carl George <carl@george.computer> - 3:10.2.23-1
- Latest upstream

* Sat May 04 2019 Carl George <carl@george.computer> - 3:10.2.22-2
- Port from Fedora to IUS
- Build with readline instead of libedit
- Enable mariadb@.service
- Move mysql_upgrade to server subpackage
- Move mysqld_safe_helper to server package for mysqld_safe

* Mon Feb 18 2019 Michal Schorm <mschorm@redhat.com> - 3:10.2.22-1
- Rebase to 10.2.22
- CVEs fixed:
  CVE-2019-2510 CVE-2019-2537

* Mon Feb 11 2019 Michal Schorm <mschorm@redhat.com> - 3:10.2.21-3
- Remove PPC64 optimizatation; Add debug build optimization
- Fix gssapi plugin typo
- Tweak the testsuite execution, speed up the testsuite on rebuilds
- Change weak dependency of RocksDB and TokuDB storage engines from Recommends to Suggests
- Add "Suggests" weak dependencies to more storage engines
- Fix TokuDB Jemalloc ld_preload; #1668375 #1671962
- Tweak macros usage

* Thu Jan 03 2019 Michal Schorm <mschorm@redhat.com> - 3:10.2.21-2
- Rebase to 10.2.21
- Disable building of the caching_sha2_password plugin, it is provided
  by 'mariadb-connector-c'
  Resolves: #1663478

* Mon Dec 10 2018 Michal Schorm <mschorm@redhat.com> - 3:10.2.19-2
- Move libmariadb packageconfig file, it should be in 'mariadb-connector-c'

* Wed Nov 14 2018 Michal Schorm <mschorm@redhat.com> - 3:10.2.19-1
- Rebase to 10.2.19
- CVEs fixed:
  CVE-2018-3282 CVE-2016-9843 CVE-2018-3174 CVE-2018-3143 CVE-2018-3156
  CVE-2018-3251 CVE-2018-3185 CVE-2018-3277 CVE-2018-3162 CVE-2018-3173
  CVE-2018-3200 CVE-2018-3284

* Fri Oct 19 2018 Michal Schorm <mschorm@redhat.com> - 3:10.2.18-2
- Fix parallel installability for x86_64 and i686 devel packages on F<=27

* Wed Sep 26 2018 Michal Schorm <mschorm@redhat.com> - 3:10.2.18-1
- Rebase to 10.2.18

* Tue Sep 04 2018 Michal Schorm <mschorm@redhat.com> - 3:10.2.17-2
- Fix parallel installability of x86_64 and i686 devel packages

* Mon Aug 20 2018 Michal Schorm <mschorm@redhat.com> - 3:10.2.17-1
- Rebase to 10.2.17
- CVEs fixed: #1602428
  CVE-2018-3060 CVE-2018-3064 CVE-2018-3063 CVE-2018-3058 CVE-2018-3066
- CVEs fixed: #1564966
  CVE-2018-2767
- CVEs fixed: #1616261
  CVE-2018-3081

* Sat Jun 30 2018 Michal Schorm <mschorm@redhat.com> - 3:10.2.16-1
- Rebase to 10.2.16
  MyRocks is now Stable (GA)

* Tue Jun 05 2018 Honza Horak <hhorak@redhat.com> - 3:10.2.15-2
- Use mysqladmin for checking the socket
- Jemalloc dependency moved to the TokuDB subpackage.
  CMake jemalloc option removed, not used anymore.
  The server doesn't need jemalloc since 10.2: https://jira.mariadb.org/browse/MDEV-11059
- Build MariaDB with TokuDB without Jemalloc.

* Wed May 23 2018 Michal Schorm <mschorm@redhat.com> - 3:10.2.15-1
- Rebase to 10.2.15
- CVEs fixed: #1568962
  CVE-2018-2755 CVE-2018-2761 CVE-2018-2766 CVE-2018-2771 CVE-2018-2781
  CVE-2018-2782 CVE-2018-2784 CVE-2018-2787 CVE-2018-2813 CVE-2018-2817
  CVE-2018-2819 CVE-2018-2786 CVE-2018-2759 CVE-2018-2777 CVE-2018-2810

* Thu Mar 29 2018 Michal Schorm <mschorm@redhat.com> - 3:10.2.14-1
- Rebase to 10.2.14
- Update testsuite run for SSL self signed certificates

* Tue Mar 6 2018 Michal Schorm <mschorm@redhat.com> - 3:10.2.13-2
- Further fix of ldconfig scriptlets for F27
- Fix hardcoded paths, move unversioned libraries and symlinks to the devel subpackage

* Thu Mar 1 2018 Michal Schorm <mschorm@redhat.com> - 3:10.2.13-1
- Rebase to 10.2.13

* Mon Feb 26 2018 Michal Schorm <mschorm@redhat.com> - 3:10.2.12-8
- SPECfile refresh, RHEL6, SySV init and old fedora stuff removed

* Sun Feb 25 2018 Michal Schorm <mschorm@redhat.com> - 3:10.2.12-7
- Rebuilt for ldconfig_post and ldconfig_postun bug
  Related: #1548331

* Thu Feb 08 2018 Fedora Release Engineering <releng@fedoraproject.org> - 3:10.2.12-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Fri Jan 26 2018 Michal Schorm <mschorm@redhat.com> - 3:10.2.12-5
- Use '-ldl' compiler flag when associated library used
  Resolves: #1538990

* Thu Jan 25 2018 Michal Schorm <mschorm@redhat.com> - 3:10.2.12-4
- Fix the upgrade path. Build TokuDB subpackage again, but build a unsupported
  configuration by upstream (without Jemalloc).
  Jemmalloc has been updated to version 5, which isn't backwards compatible.
- Use downstream tmpfiles instead of the upstream one
  Related: #1538066

* Sat Jan 20 2018 Björn Esser <besser82@fedoraproject.org> - 3:10.2.12-3
- Rebuilt for switch to libxcrypt

* Thu Jan 11 2018 Honza Horak <hhorak@redhat.com> - 3:10.2.12-1
- Do not build connect plugin with mongo and jdbc connectors
- Support MYSQLD_OPTS and _WSREP_NEW_CLUSTER env vars in init script,
  same as it is done in case of systemd unit file
  Related: #1455850
- Print the same messages as before when starting the service in SysV init,
  to not scare users
  Related: #1463411

* Wed Jan 10 2018 Michal Schorm <mschorm@redhat.com> - 3:10.2.12-1
- Rebase to 10.2.12
- Temporary fix for https://jira.mariadb.org/browse/MDEV-14537 removed
- TokuDB disabled

* Mon Dec 11 2017 Michal Schorm <mschorm@redhat.com> - 3:10.2.11-2
- Temporary fix for #1523875 removed, bug in Annobin fixed
  Resolves: #1523875

* Sat Dec 09 2017 Michal Schorm <mschorm@redhat.com> - 3:10.2.11-1
- Rebase to 10.2.11
- Temporary fix for https://jira.mariadb.org/browse/MDEV-14537 introduced
- Temporary fix for #1523875 intoruced
  Related: #1523875

* Wed Dec 06 2017 Michal Schorm <mschorm@redhat.com> - 3:10.2.10-2
- Fix PID file location
  Related: #1483331, #1515779
- Remove 'Group' tags as they should not be used any more
  Related: https://fedoraproject.org/wiki/RPMGroups

* Mon Nov 20 2017 Michal Schorm <mschorm@redhat.com> - 3:10.2.10-1
- Rebase to 10.2.10 version
- Patch 2: mariadb-install-test.patch has been incorporated by upstream
- Patch 8: mariadb-install-db-sharedir.patch; upstream started to use macros
- Update PCRE check
- Start using location libdir/mariadb for plugins
- Move libraries to libdir
- Divided to more sub-packages to match upstream's RPM list
  Resolves: #1490401; #1400463
- Update of Cmake arguments to supported format
  Related: https://lists.launchpad.net/maria-discuss/msg04852.html
- Remove false Provides

* Thu Oct 05 2017 Michal Schorm <mschorm@redhat.com> - 3:10.2.9-3
- Fix client library obsolete
  Related: #1498956
- Enable testsuite again
- RPMLint error fix:
  Remove unused python scripts which remained from TokuDB upstream
- RPMLint error fix: description line too long

* Wed Oct 04 2017 Michal Schorm <mschorm@redhat.com> - 3:10.2.9-2
- Fix of "with" and "without" macros, so they works
- Use 'iproute' dependency instead of 'net-tools'
  Related: #1496131
- Set server package to own /usr/lib64/mysql directory
- Use correct obsolete, so upgrade from maridb 10.1 to 10.2 is possible
  with dnf "--allowerasing" option
  Related: #1497234
- Fix building with client library

* Thu Sep 28 2017 Michal Schorm <mschorm@redhat.com> - 3:10.2.9-1
- Rebase to 10.2.9
- Testsuite temorarly disabled in order to fast deploy critical fix
  Related: #1497234

* Wed Sep 20 2017 Michal Schorm <mschorm@redhat.com> - 3:10.2.8-5
- Fix building without client library part
- Start building mariadb without client library part,
  use mariadb-connector-c package >= 3.0 instead
- Use obosletes of "-libs" in "-common", if built without client library part

* Mon Aug 28 2017 Honza Horak <hhorak@redhat.com> - 3:10.2.8-2
- Fix paths in galera_recovery and galera_new_cluster
  Resolves: #1403416
- Support --defaults-group-suffix properly in systemd unit file
  Resolves: #1485777
- Allow 4567 port for tcp as well
- Install mysql-wait-ready on RHEL-6 for the SysV init
- Run mysql-prepare-db-dir as non-root
- Sync mysql.init with community-mysql

* Sun Aug 20 2017 Honza Horak <hhorak@redhat.com> - 3:10.2.8-1
- Rebase to 10.2.8

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3:10.2.7-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3:10.2.7-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Tue Jul 25 2017 Adam Williamson <awilliam@redhat.com> - 3:10.2.7-6
- Revert previous change, go back to libmariadb headers (RHBZ #1474764)

* Fri Jul 21 2017 Adam Williamson <awilliam@redhat.com> - 3:10.2.7-5
- Install correct headers (server, not client) - MDEV-13370

* Wed Jul 19 2017 Jonathan Wakely <jwakely@redhat.com> - 3:10.2.7-4
- Rebuilt for s390x binutils bug

* Tue Jul 18 2017 Jonathan Wakely <jwakely@redhat.com> - 3:10.2.7-3
- Rebuilt for Boost 1.64

* Thu Jul 13 2017 Michal Schorm <mschorm@redhat.com> - 3:10.2.7-2
- Remove mysql-wait-* scripts. They aren't needed when using systemd "Type=notify"

* Thu Jul 13 2017 Michal Schorm <mschorm@redhat.com> - 3:10.2.7-1
- Rebase to 10.2.7
- Get back mysql_config, its "--libmysqld-libs" is still needed

* Wed Jul 12 2017 Adam Williamson <awilliam@redhat.com> - 3:10.2.6-4
- Add manual Provides: for the libmysqlcient compat symlink

* Wed Jul 12 2017 Adam Williamson <awilliam@redhat.com> - 3:10.2.6-3
- Move libmysqlclient.so.18 compat link to -libs subpackage

* Tue Jul 11 2017 Michal Schorm <mschorm@redhat.com> - 3:10.2.6-2
- Disable Dtrace
- Disable Sphinx, circural dependency

* Tue Jul 11 2017 Michal Schorm <mschorm@redhat.com> - 3:10.2.6-1
- Rebase to 10.2.6
- SSL patch removed
- 'libmariadb.so.3' replaced 'limysqlclient.so.18.0.0', symlinks provided
- "make test" removed, it needs running server and same test are included in the testsuite

* Mon Jul 10 2017 Michal Schorm <mschorm@redhat.com> - 3:10.1.25-1
- Rebase to 10.1.25
- Disable plugins 'cracklib' and 'gssapi' by default
- Related: #1468028, #1464070
- Looks like the testsuite removes its 'var' content correctly,
  no need to do that explicitly.

* Fri Jul 07 2017 Igor Gnatenko <ignatenko@redhat.com> - 3:10.1.24-5
- Rebuild due to bug in RPM (RHBZ #1468476)

* Mon Jun 19 2017 Michal Schorm <mschorm@redhat.com> - 3:10.1.24-4
- Use "/run" location instead of "/var/run" symlink
- Related: #1455811
- Remove AppArmor files

* Fri Jun 09 2017 Honza Horak <hhorak@redhat.com> - 3:10.1.24-3
- Downstream script mariadb-prepare-db-dir fixed for CVE-2017-3265
- Resolves: #1458940
- Check properly that datadir includes only expected files
- Related: #1356897

* Wed Jun 07 2017 Michal Schorm <mschorm@redhat.com> - 3:10.1.24-2
- Fixed incorrect Jemalloc initialization; #1459671

* Fri Jun 02 2017 Michal Schorm <mschorm@redhat.com> - 3:10.1.24-1
- Rebase to 10.1.24
- Build dependecies Bison and Libarchive added, others corrected
- Disabling Mroonga engine for i686 architecture, as it is not supported by MariaDB
- Removed patches: (fixed by upstream)
    Patch5:  mariadb-file-contents.patch
    Patch14: mariadb-example-config-files.patch
    Patch31: mariadb-string-overflow.patch
    Patch32: mariadb-basedir.patch
    Patch41: mariadb-galera-new-cluster-help.patch
- Resolves: rhbz#1414387
    CVE-2017-3313
- Resolves partly: rhbz#1443408
    CVE-2017-3308 CVE-2017-3309 CVE-2017-3453 CVE-2017-3456 CVE-2017-3464

* Tue May 23 2017 Michal Schorm <mschorm@redhat.com> - 3:10.1.21-6
- Plugin oqgraph enabled
- Plugin jemalloc enabled
- 'force' option for 'rm' removed
- Enabled '--big-test' option for the testsuite
- Disabled '--skip-rpl' option for the testsuite = replication tests enabled
- Multilib manpage added

* Mon May 15 2017 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3:10.1.21-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_27_Mass_Rebuild

* Tue Mar 07 2017 Michal Schorm <mschorm@redhat.com> - 3:10.1.21-4
- Cracklib plugin enabled
- Removed strmov patch, it is no longer needed. The issue was fixed long ago in both MariaDB and MySQL

* Wed Feb 15 2017 Michal Schorm <mschorm@redhat.com> - 3:10.1.21-3
- Fix for some RPMLint issues
- Fix: Only server utilities can be move to server-utils subpackage. The rest (from client)
  were moved back to where they came from (client - the main subpackage)
- Added correct "Obsoletes" for the server-utils subpackage
- Fixed FTBFS in F26 on x86_64, because of -Werror option
- Related: #1421092, #1395127

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3:10.1.21-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Jan 24 2017 Michal Schorm <mschorm@redhat.com> - 3:10.1.21-1
- Rebase to version 10.1.21
- Most of the non-essential utilites has been moved to the new sub-package mariadb-server-utils
- Patches "admincrash" and "errno" removed, they are no longer relevant
  "mysql-embedded-check.c" removed, no longer relevant
- Buildrequires krb5-devel duplicity removed
- Manpage for mysql_secure_installation extended
- Preparation for the CrackLib plugin to be added (waiting for correct SELinux rules to be relased)
- Related: #1260821, #1205082, #1414387

* Tue Jan 03 2017 Honza Horak <hhorak@redhat.com> - 3:10.1.20-3
- Add explicit EVR requirement in main package for -libs
- Related: #1406320

* Tue Dec 20 2016 Honza Horak <hhorak@redhat.com> - 3:10.1.20-2
- Use correct macro when removing doc files
- Resolves: #1400981

* Sat Dec 17 2016 Michal Schorm <mschorm@redhat.com> - 3:10.1.20-1
- Rebase to version 10.1.20
- Related: #1405258

* Fri Dec 02 2016 Michal Schorm <mschorm@redhat.com> - 3:10.1.19-6
- Move patch from specfile to standalone patch file
- Related: #1382988

* Thu Dec 01 2016 Rex Dieter <rdieter@fedoraproject.org> - 3:10.1.19-6
- -devel: use pkgconfig(openssl) to allow any implementation (like compat-openssl10)

* Wed Nov 30 2016 Michal Schorm <mschorm@redhat.com> - 3:10.1.19-5
- Testsuite blacklists heavily updated. Current tracker: #1399847
- Log-error option added to all config files examples
- Resolves: #1382988

* Wed Nov 16 2016 Michal Schorm <mschorm@redhat.com> - 3:10.1.19-4
- JdbcMariaDB.jar test removed
- PCRE version check added
- Related: #1382988, #1396945, #1096787

* Wed Nov 16 2016 Michal Schorm <mschorm@redhat.com> - 3:10.1.19-4
- test suite ENABLED, consensus was made it still should be run every build

* Wed Nov 16 2016 Michal Schorm <mschorm@redhat.com> - 3:10.1.19-2
- fixed bug 1382988
- added comment to the test suite
- test suite DISABLED for most builds in Koji, see comments

* Wed Nov 16 2016 Michal Schorm <mschorm@redhat.com> - 3:10.1.19-1
- Update to 10.1.19
- added temporary support to build with OpenSSL 1.0 on Fedora >= 26
- added krb5-devel pkg as Buldrquires to prevent gssapi failure

* Tue Oct  4 2016 Jakub Dorňák <jdornak@redhat.com> - 3:10.1.18-1
- Update to 10.1.18

* Wed Aug 31 2016 Jakub Dorňák <jdornak@redhat.com> - 3:10.1.17-1
- Update to 10.1.17

* Mon Aug 29 2016 Jakub Dorňák <jdornak@redhat.com> - 3:10.1.16-2
- Fixed galera replication
- Resolves: #1352946

* Tue Jul 19 2016 Jakub Dorňák <jdornak@redhat.com> - 3:10.1.16-1
- Update to 10.1.16

* Fri Jul 15 2016 Honza Horak <hhorak@redhat.com> - 3:10.1.14-5
- Fail build when test-suite fails
- Use license macro for inclusion of licenses

* Thu Jul 14 2016 Honza Horak <hhorak@redhat.com> - 3:10.1.14-4
- Revert Update to 10.1.15, this release is broken
  https://lists.launchpad.net/maria-discuss/msg03691.html

* Thu Jul 14 2016 Honza Horak <hhorak@redhat.com> - 2:10.1.15-3
- Check datadir more carefully to avoid unwanted data corruption
- Related: #1335849

* Thu Jul  7 2016 Jakub Dorňák <jdornak@redhat.com> - 2:10.1.15-2
- Bump epoch
  (related to the downgrade from the pre-release version)

* Fri Jul  1 2016 Jakub Dorňák <jdornak@redhat.com> - 1:10.1.15-1
- Update to 10.1.15

* Fri Jul  1 2016 Jakub Dorňák <jdornak@redhat.com> - 1:10.1.14-3
- Revert "Update to 10.2.0"
  It is possible that MariaDB 10.2.0 won't be stable till f25 GA.

* Tue Jun 21 2016 Pavel Raiskup <praiskup@redhat.com> - 1:10.1.14-3
- BR multilib-rpm-config and use it for multilib workarounds
- install architecture dependant pc file to arch-dependant location

* Thu May 26 2016 Jakub Dorňák <jdornak@redhat.com> - 1:10.2.0-2
- Fix mysql-prepare-db-dir
- Resolves: #1335849

* Thu May 12 2016 Jakub Dorňák <jdornak@redhat.com> - 1:10.2.0-1
- Update to 10.2.0

* Thu May 12 2016 Jakub Dorňák <jdornak@redhat.com> - 1:10.1.14-1
- Add selinux policy
- Update to 10.1.14 (includes various bug fixes)
- Add -h and --help options to galera_new_cluster

* Thu Apr  7 2016 Jakub Dorňák <jdornak@redhat.com> - 1:10.1.13-3
- wsrep_on in galera.cnf

* Tue Apr  5 2016 Jakub Dorňák <jdornak@redhat.com> - 1:10.1.13-2
- Moved /etc/sysconfig/clustercheck
  and /usr/share/mariadb/systemd/use_galera_new_cluster.conf
  to mariadb-server-galera

* Tue Mar 29 2016 Jakub Dorňák <jdornak@redhat.com> - 1:10.1.13-1
- Update to 10.1.13

* Wed Mar 23 2016 Jakub Dorňák <jdornak@redhat.com> - 1:10.1.12-4
- Fixed conflict with mariadb-galera-server

* Tue Mar 22 2016 Jakub Dorňák <jdornak@redhat.com> - 1:10.1.12-3
- Add subpackage mariadb-server-galera
- Resolves: 1310622

* Tue Mar 01 2016 Honza Horak <hhorak@redhat.com> - 1:10.1.12-2
- Rebuild for BZ#1309199 (symbol versioning)

* Mon Feb 29 2016 Jakub Dorňák <jdornak@redhat.com> - 1:10.1.12-1
- Update to 10.1.12

* Tue Feb 16 2016 Honza Horak <hhorak@redhat.com> - 1:10.1.11-9
- Remove dangling symlink to /etc/init.d/mysql

* Sat Feb 13 2016 Honza Horak <hhorak@redhat.com> - 1:10.1.11-8
- Use epoch for obsoleting mariadb-galera-server

* Fri Feb 12 2016 Honza Horak <hhorak@redhat.com> - 1:10.1.11-7
- Add Provides: bundled(pcre) in case we build with bundled pcre
- Related: #1302296
- embedded-devel should require libaio-devel
- Resolves: #1290517

* Fri Feb 12 2016 Honza Horak <hhorak@redhat.com> - 1:10.1.11-6
- Fix typo s/obsolate/obsolete/

* Thu Feb 11 2016 Honza Horak <hhorak@redhat.com> - 1:10.1.11-5
- Add missing requirements for proper wsrep functionality
- Obsolate mariadb-galera & mariadb-galera-server (thanks Tomas Repik)
- Resolves: #1279753
- Re-enable using libedit, which should be now fixed
- Related: #1201988
- Remove mariadb-wait-ready call from systemd unit, we have now systemd notify support
- Make mariadb@.service similar to mariadb.service

* Mon Feb 08 2016 Honza Horak <hhorak@redhat.com> - 1:10.1.11-4
- Use systemd unit file more compatible with upstream

* Sun Feb 07 2016 Honza Horak <hhorak@redhat.com> - 1:10.1.11-3
- Temporarily disabling oqgraph for
  https://mariadb.atlassian.net/browse/MDEV-9479

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1:10.1.11-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Wed Feb  3 2016 Jakub Dorňák <jdornak@redhat.com> - 1:10.1.11-1
- Update to 10.1.11

* Tue Jan 19 2016 Jakub Dorňák <jdornak@redhat.com> - 1:10.1.10-1
- Update to 10.1.10

* Mon Dec 07 2015 Dan Horák <dan[at]danny.cz> - 1:10.1.8-3
- rebuilt for s390(x)

* Tue Nov 03 2015 Honza Horak <hhorak@redhat.com> - 1:10.1.8-2
- Expand variables in server.cnf

* Thu Oct 22 2015 Jakub Dorňák <jdornak@redhat.com> - 1:10.1.8-1
- Update to 10.1.8

* Thu Aug 27 2015 Jonathan Wakely <jwakely@redhat.com> - 1:10.0.21-2
- Rebuilt for Boost 1.59

* Mon Aug 10 2015 Jakub Dorňák <jdornak@redhat.com> - 1:10.0.21-1
- Update to 10.0.21

* Wed Jul 29 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:10.0.20-3
- Rebuilt for https://fedoraproject.org/wiki/Changes/F23Boost159

* Wed Jul 22 2015 David Tardon <dtardon@redhat.com> - 1:10.0.20-2
- rebuild for Boost 1.58

* Tue Jun 23 2015 Honza Horak <hhorak@redhat.com> - 1:10.0.20-1
- Update to 10.0.20

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:10.0.19-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Wed Jun 03 2015 Dan Horák <dan[at]danny.cz> - 1:10.0.19-2
- Update lists of failing tests (jdornak)
- Related: #1149647

* Mon May 11 2015 Honza Horak <hhorak@redhat.com> - 1:10.0.19-1
- Update to 10.0.19

* Thu May 07 2015 Honza Horak <hhorak@redhat.com> - 1:10.0.18-1
- Update to 10.0.18

* Thu May 07 2015 Honza Horak <hhorak@redhat.com> - 1:10.0.17-4
- Include client plugins into -common package since they are used by both -libs
  and base packages.
- Do not use libedit
- Related: #1201988
- Let plugin dir to be owned by -common
- Use correct comment in the init script
- Related: #1184604
- Add openssl as BuildRequires to run some openssl tests during build
- Related: #1189180
- Fail in case any command in check fails
- Related: #1124791
- Fix mysqladmin crash if run with -u root -p
- Resolves: #1207170

* Sat May 02 2015 Kalev Lember <kalevlember@gmail.com> - 1:10.0.17-3
- Rebuilt for GCC 5 C++11 ABI change

* Fri Mar 06 2015 Honza Horak <hhorak@redhat.com> - 1:10.0.17-2
- Wait for daemon ends
- Resolves: #1072958
- Do not include symlink to libmysqlclient if not shipping the library
- Do not use scl prefix more than once in paths
  Based on https://www.redhat.com/archives/sclorg/2015-February/msg00038.html

* Wed Mar 04 2015 Honza Horak <hhorak@redhat.com> - 1:10.0.17-1
- Rebase to version 10.0.17
- Added variable for turn off skipping some tests

* Tue Mar 03 2015 Honza Horak <hhorak@redhat.com> - 1:10.0.16-6
- Check permissions when starting service on RHEL-6
- Resolves: #1194699
- Do not create test database by default
- Related: #1194611

* Fri Feb 13 2015 Matej Muzila <mmuzila@redhat.com> - 1:10.0.16-4
- Enable tokudb

* Tue Feb 10 2015 Honza Horak <hhorak@redhat.com> - 1:10.0.16-3
- Fix openssl_1 test

* Wed Feb  4 2015 Jakub Dorňák <jdornak@redhat.com> - 1:10.0.16-2
- Include new certificate for tests
- Update lists of failing tests
- Related: #1186110

* Tue Feb  3 2015 Jakub Dorňák <jdornak@redhat.com> - 1:10.0.16-9
- Rebase to version 10.0.16
- Resolves: #1187895

* Tue Jan 27 2015 Petr Machata <pmachata@redhat.com> - 1:10.0.15-9
- Rebuild for boost 1.57.0

* Mon Jan 26 2015 Honza Horak <hhorak@redhat.com> - 1:10.0.15-8
- Fix typo in the config file

* Sun Jan 25 2015 Honza Horak <hhorak@redhat.com> - 1:10.0.15-7
- Do not create log file in post script

* Sat Jan 24 2015 Honza Horak <hhorak@redhat.com> - 1:10.0.15-6
- Move server settings to config file under my.cnf.d dir

* Sat Jan 24 2015 Honza Horak <hhorak@redhat.com> - 1:10.0.15-5
- Fix path for sysconfig file
  Filter provides in el6 properly
  Fix initscript file location

* Tue Jan 06 2015 Honza Horak <hhorak@redhat.com> - 1:10.0.15-4
- Disable failing tests connect.mrr, connect.updelx2 on ppc and s390

* Mon Dec 22 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.15-3
- Fix macros paths in my.cnf
- Create old location for pid file if it remained in my.cnf

* Fri Dec 05 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.15-2
- Rework usage of macros and remove some compatibility artefacts

* Thu Nov 27 2014 Jakub Dorňák <jdornak@redhat.com> - 1:10.0.15-1
- Update to 10.0.15

* Thu Nov 20 2014 Jan Stanek <jstanek@redhat.com> - 1:10.0.14-8
- Applied upstream fix for mysql_config --cflags output.
- Resolves: #1160845

* Fri Oct 24 2014 Jan Stanek <jstanek@redhat.com> - 1:10.0.14-7
- Fixed compat service file.
- Resolves: #1155700

* Mon Oct 13 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.14-6
- Remove bundled cmd-line-utils
- Related: #1079637
- Move mysqlimport man page to proper package
- Disable main.key_cache test on s390
  Releated: #1149647

* Wed Oct 08 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.14-5
- Disable tests connect.part_file, connect.part_table
  and connect.updelx
- Related: #1149647

* Wed Oct 01 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.14-4
- Add bcond_without mysql_names
  Use more correct path when deleting mysql logrotate script

* Wed Oct 01 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.14-3
- Build with system libedit
- Resolves: #1079637

* Mon Sep 29 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.14-2
- Add with_debug option

* Mon Sep 29 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.14-1
- Update to 10.0.14

* Wed Sep 24 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.13-8
- Move connect engine to a separate package
  Rename oqgraph engine to align with upstream packages
- Move some files to correspond with MariaDB upstream packages
  client.cnf into -libs, mysql_plugin and msql2mysql into base,
  tokuftdump and aria_* into -server, errmsg-utf8.txt into -errmsg
- Remove duplicate cnf files packaged using %%doc
- Check upgrade script added to warn about need for mysql_upgrade

* Wed Sep 24 2014 Matej Muzila <mmuzila@redhat.com> - 1:10.0.13-7
- Client related libraries moved from mariadb-server to mariadb-libs
- Related: #1138843

* Mon Sep 08 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.13-6
- Disable vcol_supported_sql_funcs_myisam test on all arches
- Related: #1096787
- Install systemd service file on RHEL-7+
  Server requires any mysql package, so it should be fine with older client

* Thu Sep 04 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.13-5
- Fix paths in mysql_install_db script
- Resolves: #1134328
- Use %%cmake macro

* Tue Aug 19 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.13-4
- Build config subpackage everytime
- Disable failing tests: innodb_simulate_comp_failures_small, key_cache
  rhbz#1096787

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:10.0.13-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Thu Aug 14 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.13-2
- Include mysqld_unit only if required; enable tokudb in f20-

* Wed Aug 13 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.13-1
- Rebase to version 10.0.13

* Tue Aug 12 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.12-8
- Introduce -config subpackage and ship base config files here

* Tue Aug  5 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.12-7
- Adopt changes from mysql, thanks Bjorn Munch <bjorn.munch@oracle.com>

* Mon Jul 28 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.12-6
- Use explicit sysconfdir
- Absolut path for default value for pid file and error log

* Tue Jul 22 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.12-5
- Hardcoded paths removed to work fine in chroot
- Spec rewrite to be more similar to oterh MySQL implementations
- Use variable for daemon unit name
- Include SysV init script if built on older system
- Add possibility to not ship some sub-packages

* Mon Jul 21 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.12-4
- Reformating spec and removing unnecessary snippets

* Tue Jul 15 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.12-3
- Enable OQGRAPH engine and package it as a sub-package
- Add support for TokuDB engine for x86_64 (currently still disabled)
- Re-enable tokudb_innodb_xa_crash again, seems to be fixed now
- Drop superfluous -libs and -embedded ldconfig deps (thanks Ville Skyttä)
- Separate -lib and -common sub-packages
- Require /etc/my.cnf instead of shipping it
- Include README.mysql-cnf
- Multilib support re-worked
- Introduce new option with_mysqld_unit
- Removed obsolete mysql-cluster, the package should already be removed
- Improve error message when log file is not writable
- Compile all binaries with full RELRO (RHBZ#1092548)
- Use modern symbol filtering with compatible backup
- Add more groupnames for server's my.cnf
- Error messages now provided by a separate package (thanks Alexander Barkov)
- Expand paths in helper scripts using cmake

* Wed Jun 18 2014 Mikko Tiihonen <mikko.tiihonen@iki.fi> - 1:10.0.12-2
- Use -fno-delete-null-pointer-checks to avoid segfaults with gcc 4.9

* Tue Jun 17 2014 Jakub Dorňák <jdornak@redhat.com> - 1:10.0.12-1
- Rebase to version 10.0.12

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:10.0.11-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Tue Jun  3 2014 Jakub Dorňák <jdornak@redhat.com> - 1:10.0.11-4
- rebuild with tests failing on different arches disabled (#1096787)

* Thu May 29 2014 Dan Horák <dan[at]danny.cz> - 1:10.0.11-2
- rebuild with tests failing on big endian arches disabled (#1096787)

* Wed May 14 2014 Jakub Dorňák <jdornak@redhat.com> - 1:10.0.11-1
- Rebase to version 10.0.11

* Mon May 05 2014 Honza Horak <hhorak@redhat.com> - 1:10.0.10-3
- Script for socket check enhanced

* Thu Apr 10 2014 Jakub Dorňák <jdornak@redhat.com> - 1:10.0.10-2
- use system pcre library

* Thu Apr 10 2014 Jakub Dorňák <jdornak@redhat.com> - 1:10.0.10-1
- Rebase to version 10.0.10

* Wed Mar 12 2014 Honza Horak <hhorak@redhat.com> - 1:5.5.36-2
- Server crashes on SQL select containing more group by and left join statements using innodb tables
- Resolves: #1065676
- Fix paths in helper scripts
- Move language files into mariadb directory

* Thu Mar 06 2014 Honza Horak <hhorak@redhat.com> - 1:5.5.36-1
- Rebase to 5.5.36
  https://kb.askmonty.org/en/mariadb-5536-changelog/

* Tue Feb 25 2014 Honza Horak <hhorak@redhat.com> 1:5.5.35-5
- Daemon helper scripts sanity changes and spec files clean-up

* Tue Feb 11 2014 Honza Horak <hhorak@redhat.com> 1:5.5.35-4
- Fix typo in mysqld.service
- Resolves: #1063981

* Wed Feb  5 2014 Honza Horak <hhorak@redhat.com> 1:5.5.35-3
- Do not touch the log file in post script, so it does not get wrong owner
- Resolves: #1061045

* Thu Jan 30 2014 Honza Horak <hhorak@redhat.com> 1:5.5.35-1
- Rebase to 5.5.35
  https://kb.askmonty.org/en/mariadb-5535-changelog/
  Also fixes: CVE-2014-0001, CVE-2014-0412, CVE-2014-0437, CVE-2013-5908,
  CVE-2014-0420, CVE-2014-0393, CVE-2013-5891, CVE-2014-0386, CVE-2014-0401,
  CVE-2014-0402
- Resolves: #1054043
- Resolves: #1059546

* Tue Jan 14 2014 Honza Horak <hhorak@redhat.com> - 1:5.5.34-9
- Adopt compatible system versioning
- Related: #1045013
- Use compatibility mysqld.service instead of link
- Related: #1014311

* Mon Jan 13 2014 Rex Dieter <rdieter@fedoraproject.org> 1:5.5.34-8
- move mysql_config alternatives scriptlets to -devel too

* Fri Jan 10 2014 Honza Horak <hhorak@redhat.com> 1:5.5.34-7
- Build with -O3 on ppc64
- Related: #1051069
- Move mysql_config to -devel sub-package and remove Require: mariadb
- Related: #1050920

* Fri Jan 10 2014 Marcin Juszkiewicz <mjuszkiewicz@redhat.com> 1:5.5.34-6
- Disable main.gis-precise test also for AArch64
- Disable perfschema.func_file_io and perfschema.func_mutex for AArch64
  (like it is done for 32-bit ARM)

* Fri Jan 10 2014 Honza Horak <hhorak@redhat.com> 1:5.5.34-5
- Clean all non-needed doc files properly

* Wed Jan  8 2014 Honza Horak <hhorak@redhat.com> 1:5.5.34-4
- Read socketfile location in mariadb-prepare-db-dir script

* Mon Jan  6 2014 Honza Horak <hhorak@redhat.com> 1:5.5.34-3
- Don't test EDH-RSA-DES-CBC-SHA cipher, it seems to be removed from openssl
  which now makes mariadb/mysql FTBFS because openssl_1 test fails
- Related: #1044565
- Use upstream's layout for symbols version in client library
- Related: #1045013
- Check if socket file is not being used by another process at a time
  of starting the service
- Related: #1045435
- Use %%ghost directive for the log file
- Related: 1043501

* Wed Nov 27 2013 Honza Horak <hhorak@redhat.com> 1:5.5.34-2
- Fix mariadb-wait-ready script

* Fri Nov 22 2013 Honza Horak <hhorak@redhat.com> 1:5.5.34-1
- Rebase to 5.5.34

* Mon Nov  4 2013 Honza Horak <hhorak@redhat.com> 1:5.5.33a-4
- Fix spec file to be ready for backport by Oden Eriksson
- Resolves: #1026404

* Mon Nov  4 2013 Honza Horak <hhorak@redhat.com> 1:5.5.33a-3
- Add pam-devel to build-requires in order to build
- Related: #1019945
- Check if correct process is running in mysql-wait-ready script
- Related: #1026313

* Mon Oct 14 2013 Honza Horak <hhorak@redhat.com> 1:5.5.33a-2
- Turn on test suite

* Thu Oct 10 2013 Honza Horak <hhorak@redhat.com> 1:5.5.33a-1
- Rebase to 5.5.33a
  https://kb.askmonty.org/en/mariadb-5533-changelog/
  https://kb.askmonty.org/en/mariadb-5533a-changelog/
- Enable outfile_loaddata test
- Disable tokudb_innodb_xa_crash test

* Mon Sep  2 2013 Honza Horak <hhorak@redhat.com> - 1:5.5.32-12
- Re-organize my.cnf to include only generic settings
- Resolves: #1003115
- Move pid file location to /var/run/mariadb
- Make mysqld a symlink to mariadb unit file rather than the opposite way
- Related: #999589

* Thu Aug 29 2013 Honza Horak <hhorak@redhat.com> - 1:5.5.32-11
- Move log file into /var/log/mariadb/mariadb.log
- Rename logrotate script to mariadb
- Resolves: #999589

* Wed Aug 14 2013 Rex Dieter <rdieter@fedoraproject.org> 1:5.5.32-10
- fix alternatives usage

* Tue Aug 13 2013 Honza Horak <hhorak@redhat.com> - 1:5.5.32-9
- Multilib issues solved by alternatives
- Resolves: #986959

* Sat Aug 03 2013 Petr Pisar <ppisar@redhat.com> - 1:5.5.32-8
- Perl 5.18 rebuild

* Wed Jul 31 2013 Honza Horak <hhorak@redhat.com> - 1:5.5.32-7
- Do not use login shell for mysql user

* Tue Jul 30 2013 Honza Horak <hhorak@redhat.com> - 1:5.5.32-6
- Remove unneeded systemd-sysv requires
- Provide mysql-compat-server symbol
- Create mariadb.service symlink
- Fix multilib header location for arm
- Enhance documentation in the unit file
- Use scriptstub instead of links to avoid multilib conflicts
- Add condition for doc placement in F20+

* Sun Jul 28 2013 Dennis Gilmore <dennis@ausil.us> - 1:5.5.32-5
- remove "Requires(pretrans): systemd" since its not possible
- when installing mariadb and systemd at the same time. as in a new install

* Sat Jul 27 2013 Kevin Fenzi <kevin@scrye.com> 1:5.5.32-4
- Set rpm doc macro to install docs in unversioned dir

* Fri Jul 26 2013 Dennis Gilmore <dennis@ausil.us> 1:5.5.32-3
- add Requires(pre) on systemd for the server package

* Tue Jul 23 2013 Dennis Gilmore <dennis@ausil.us> 1:5.5.32-2
- replace systemd-units requires with systemd
- remove solaris files

* Fri Jul 19 2013 Honza Horak <hhorak@redhat.com> 1:5.5.32-1
- Rebase to 5.5.32
  https://kb.askmonty.org/en/mariadb-5532-changelog/
- Clean-up un-necessary systemd snippets

* Wed Jul 17 2013 Petr Pisar <ppisar@redhat.com> - 1:5.5.31-7
- Perl 5.18 rebuild

* Mon Jul  1 2013 Honza Horak <hhorak@redhat.com> 1:5.5.31-6
- Test suite params enhanced to decrease server condition influence
- Fix misleading error message when uninstalling built-in plugins
- Related: #966873

* Thu Jun 27 2013 Honza Horak <hhorak@redhat.com> 1:5.5.31-5
- Apply fixes found by Coverity static analysis tool

* Wed Jun 19 2013 Honza Horak <hhorak@redhat.com> 1:5.5.31-4
- Do not use pretrans scriptlet, which doesn't work in anaconda
- Resolves: #975348

* Fri Jun 14 2013 Honza Horak <hhorak@redhat.com> 1:5.5.31-3
- Explicitly enable mysqld if it was enabled in the beginning
  of the transaction.

* Thu Jun 13 2013 Honza Horak <hhorak@redhat.com> 1:5.5.31-2
- Apply man page fix from Jan Stanek

* Fri May 24 2013 Honza Horak <hhorak@redhat.com> 1:5.5.31-1
- Rebase to 5.5.31
  https://kb.askmonty.org/en/mariadb-5531-changelog/
- Preserve time-stamps in case of installed files
- Use /var/tmp instead of /tmp, since the later is using tmpfs,
  which can cause problems
- Resolves: #962087
- Fix test suite requirements

* Sun May  5 2013 Honza Horak <hhorak@redhat.com> 1:5.5.30-2
- Remove mytop utility, which is packaged separately
- Resolve multilib conflicts in mysql/private/config.h

* Fri Mar 22 2013 Honza Horak <hhorak@redhat.com> 1:5.5.30-1
- Rebase to 5.5.30
  https://kb.askmonty.org/en/mariadb-5530-changelog/

* Fri Mar 22 2013 Honza Horak <hhorak@redhat.com> 1:5.5.29-11
- Obsolete MySQL since it is now renamed to community-mysql
- Remove real- virtual names

* Thu Mar 21 2013 Honza Horak <hhorak@redhat.com> 1:5.5.29-10
- Adding epoch to have higher priority than other mysql implementations
  when comes to provider comparison

* Wed Mar 13 2013 Honza Horak <hhorak@redhat.com> 5.5.29-9
- Let mariadb-embedded-devel conflict with MySQL-embedded-devel
- Adjust mariadb-sortbuffer.patch to correspond with upstream patch

* Mon Mar  4 2013 Honza Horak <hhorak@redhat.com> 5.5.29-8
- Mask expected warnings about setrlimit in test suite

* Thu Feb 28 2013 Honza Horak <hhorak@redhat.com> 5.5.29-7
- Use configured prefix value instead of guessing basedir
  in mysql_config
- Resolves: #916189
- Export dynamic columns and non-blocking API functions documented
  by upstream

* Wed Feb 27 2013 Honza Horak <hhorak@redhat.com> 5.5.29-6
- Fix sort_buffer_length option type

* Wed Feb 13 2013 Honza Horak <hhorak@redhat.com> 5.5.29-5
- Suppress warnings in tests and skip tests also on ppc64p7

* Tue Feb 12 2013 Honza Horak <hhorak@redhat.com> 5.5.29-4
- Suppress warning in tests on ppc
- Enable fixed index_merge_myisam test case

* Thu Feb 07 2013 Honza Horak <hhorak@redhat.com> 5.5.29-3
- Packages need to provide also %%_isa version of mysql package
- Provide own symbols with real- prefix to distinguish from mysql
  unambiguously
- Fix format for buffer size in error messages (MDEV-4156)
- Disable some tests that fail on ppc and s390
- Conflict only with real-mysql, otherwise mariadb conflicts with ourself

* Tue Feb 05 2013 Honza Horak <hhorak@redhat.com> 5.5.29-2
- Let mariadb-libs to own /etc/my.cnf.d

* Thu Jan 31 2013 Honza Horak <hhorak@redhat.com> 5.5.29-1
- Rebase to 5.5.29
  https://kb.askmonty.org/en/mariadb-5529-changelog/
- Fix inaccurate default for socket location in mysqld-wait-ready
- Resolves: #890535

* Thu Jan 31 2013 Honza Horak <hhorak@redhat.com> 5.5.28a-8
- Enable obsoleting mysql

* Wed Jan 30 2013 Honza Horak <hhorak@redhat.com> 5.5.28a-7
- Adding necessary hacks for perl dependency checking, rpm is still
  not wise enough
- Namespace sanity re-added for symbol default_charset_info

* Mon Jan 28 2013 Honza Horak <hhorak@redhat.com> 5.5.28a-6
- Removed %%{_isa} from provides/obsoletes, which doesn't allow
  proper obsoleting
- Do not obsolete mysql at the time of testing

* Thu Jan 10 2013 Honza Horak <hhorak@redhat.com> 5.5.28a-5
- Added licenses LGPLv2 and BSD
- Removed wrong usage of %%{epoch}
- Test-suite is run in %%check
- Removed perl dependency checking adjustment, rpm seems to be smart enough
- Other minor spec file fixes

* Tue Dec 18 2012 Honza Horak <hhorak@redhat.com> 5.5.28a-4
- Packaging of MariaDB based on MySQL package

