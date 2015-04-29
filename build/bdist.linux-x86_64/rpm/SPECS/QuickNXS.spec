%define name QuickNXS
%define version 2.0.577
%define unmangled_version 2.0.577
%define release 1

Summary: Liquids reflectometer data reduction software
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{unmangled_version}.tar.gz
License: UNKNOWN
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Jean Bilheux <bilheuxjm@ornl.gov>
Packager: Artur Glavic <agf@ornl.gov>
Requires: mantidnightly numpy python-matplotlib
Url: http://

%description
UNKNOWN

%prep
%setup -n %{name}-%{unmangled_version}

%build
python setup.py build

%install
python setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
%doc doc/user_manual/QuickNXS_Users_Manual.pdf
