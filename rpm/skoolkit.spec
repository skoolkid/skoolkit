%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:           skoolkit
Version:        4.2
Release:        1%{?dist}
Summary:        Tools for creating disassemblies of ZX Spectrum programs

License:        GPLv3+
URL:            http://skoolkit.ca/
Source0:        http://skoolkit.ca/downloads/%{name}/%{name}-%{version}.tar.xz

BuildArch:      noarch
BuildRequires:  python-devel
Requires:       python >= 2.7

%description
SkoolKit is a collection of utilities that can be used to disassemble a
Spectrum game (or indeed any piece of Spectrum software written in machine
code) into a format known as a skool file. Then, from this skool file, you can
use SkoolKit to create a browsable disassembly in HTML format, or a
re-assemblable disassembly in ASM format. So the skool file is - from start to
finish as you develop it by organising and annotating the code - the common
'source' for both the reader-friendly HTML version of the disassembly, and the
developer- and assembler-friendly ASM version of the disassembly.

%prep
%setup -q

%build
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
# --prefix=... is needed on openSUSE, but not Fedora
%{__python} setup.py install -O1 --prefix=%{_prefix} --skip-build --root $RPM_BUILD_ROOT
install -d %{buildroot}%{_mandir}/man1
cp -p man/man1/* %{buildroot}%{_mandir}/man1
install -d %{buildroot}%{_datadir}/%{name}
cp -a examples %{buildroot}%{_datadir}/%{name}

%files
%doc COPYING docs/*
%{_bindir}/*
%{_mandir}/man1/*
%{_datadir}/%{name}/*
%{python_sitelib}/*

%changelog
* Sun Dec 07 2014 Richard Dymond <rjdymond@gmail.com> 4.2-1
- Updated to 4.2

* Sat Sep 20 2014 Richard Dymond <rjdymond@gmail.com> 4.1.1-1
- Updated to 4.1.1

* Sat Aug 30 2014 Richard Dymond <rjdymond@gmail.com> 4.1-1
- Updated to 4.1

* Sun May 25 2014 Richard Dymond <rjdymond@gmail.com> 4.0-1
- Updated to 4.0

* Sat Mar 08 2014 Richard Dymond <rjdymond@gmail.com> 3.7-1
- Updated to 3.7

* Sat Nov 02 2013 Richard Dymond <rjdymond@gmail.com> 3.6-1
- Updated to 3.6

* Sun Sep 01 2013 Richard Dymond <rjdymond@gmail.com> 3.5-1
- Updated to 3.5

* Mon Jul 08 2013 Richard Dymond <rjdymond@gmail.com> 3.4-1
- Updated to 3.4

* Tue May 21 2013 Richard Dymond <rjdymond@gmail.com> 3.3.2-2
- Restored manicminer.py and jetsetwilly.py modules
- Removed resources from the skoolkit package directory

* Mon May 13 2013 Richard Dymond <rjdymond@gmail.com> 3.3.2-1
- Updated to 3.3.2

* Mon Mar 04 2013 Richard Dymond <rjdymond@gmail.com> 3.3.1-1
- Updated to 3.3.1

* Tue Jan 08 2013 Richard Dymond <rjdymond@gmail.com> 3.3-1
- Updated to 3.3

* Thu Nov 01 2012 Richard Dymond <rjdymond@gmail.com> 3.2-1
- Initial RPM release
