#
# spec file for package containerd
#
# Copyright (c) 2024 SUSE LLC
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via https://bugs.opensuse.org/
#
# nodebuginfo

# We need (at least) updated debuginfo scripts for these
%global _missing_build_ids_terminate_build 0

# MANUAL: Update the git_version.
%define git_version 88bf19b2105c8b17560993bee28a01ddc2f97182
%define git_short   88bf19b2105c

%global provider_prefix github.com/containerd/containerd
%global import_path %{provider_prefix}

Name:           containerd
Version:        1.7.24
Release:        1
Summary:        Standalone OCI Container Daemon
License:        Apache-2.0
Group:          System/Management
URL:            https://containerd.tools
Source0:        %{name}-%{version}.tar.xz
Source1:        %{name}-rpmlintrc
Source2:        %{name}.service
# UPSTREAM: Revert <https://github.com/containerd/containerd/pull/7933> to fix build on SLE-12.
Patch1:         0001-BUILD-SLE12-revert-btrfs-depend-on-kernel-UAPI-inste.patch
BuildRequires:  fdupes
BuildRequires:  glibc-devel
BuildRequires:  golang(API) >= 1.23
BuildRequires:  golang-packaging
#BuildRequires:  libbtrfs >= 3.8
BuildRequires:  btrfs-progs-devel >= 3.8
BuildRequires:  libseccomp >= 2.2
BuildRequires:  pkgconfig(systemd)
# We provide a git revision so that Docker can require it properly.
Provides:       %{name}-git = %{git_version}
# Currently runc is the only supported runtime for containerd. We pin the same
# flavour as us, to avoid mixing (the version pinning is done by docker.spec).
Requires:       runc
ExcludeArch:    s390
Provides:       cri-runtime

%description
Containerd is a daemon with an API and a command line client, to manage
containers on one machine. It uses runC to run containers according to the OCI
specification. Containerd has advanced features such as seccomp and user
namespace support as well as checkpoint and restore for cloning and live
migration of containers.

%package ctr
Summary:        Client for %{name}
Group:          System/Management
Requires:       %{name} = %{version}

%description ctr
Standalone client for containerd, which allows management of containerd containers
separately from Docker.

%package devel
Summary:        Source code for containerd
Group:          Development/Libraries/Go
Requires:       %{name} = %{version}
# cannot switch to noarch on SLE as that breaks maintenance updates
BuildArch:      noarch

%description devel
This package contains the source code needed for building packages that
reference the following Go import paths: github.com/containerd/containerd

%prep
%setup -q -n %{name}-%{version}/%{name}
%patch -P 1 -p1

%build
%goprep %{import_path}
BUILDTAGS="apparmor selinux seccomp"
make \
        BUILDTAGS="$BUILDTAGS" \
        VERSION="v%{version}" \
        REVISION="%{git_version}"

cp -r "$PROJECT/bin" bin

%install
%gosrc
# Install binaries.
pushd bin/
for bin in containerd{,-shim*}
do
        install -D -m755 "$bin" "%{buildroot}/%{_sbindir}/$bin"
done
# "ctr" is a bit too generic.
install -D -m755 ctr %{buildroot}/%{_sbindir}/%{name}-ctr
popd

# Set up dummy configuration.
install -d -m755 %{buildroot}/%{_sysconfdir}/%{name}
echo "# See containerd-config.toml(5) for documentation." >%{buildroot}/%{_sysconfdir}/%{name}/config.toml

# Install system service
install -Dp -m644 %{SOURCE2} %{buildroot}%{_unitdir}/%{name}.service

%fdupes %{buildroot}

%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun %{name}.service

%files
%doc README.md
%license LICENSE
%dir %{_sysconfdir}/%{name}
%config %{_sysconfdir}/%{name}/config.toml
%{_sbindir}/containerd
%{_sbindir}/containerd-shim*
%{_unitdir}/%{name}.service

%files ctr
%{_sbindir}/%{name}-ctr

%files devel
%license LICENSE
%dir %{go_contribsrcdir}/github.com
%dir %{go_contribsrcdir}/github.com/containerd
%{go_contribsrcdir}/%{import_path}

%changelog
