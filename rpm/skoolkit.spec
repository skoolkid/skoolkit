Name:           skoolkit
Version:        9.0
Release:        1
Summary:        Tools for creating disassemblies of ZX Spectrum programs

License:        GPLv3+
URL:            https://skoolkit.ca
Source0:        https://skoolkit.ca/downloads/%{name}/%{name}-%{version}.tar.xz

BuildArch:      noarch
BuildRequires:  python3-devel
Requires:       python3 >= 3.8

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
%{__python3} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{__python3} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
install -d %{buildroot}%{_mandir}/man1
cp -p man/man1/* %{buildroot}%{_mandir}/man1
install -d %{buildroot}%{_datadir}/%{name}
cp -a examples %{buildroot}%{_datadir}/%{name}

%files
%doc COPYING docs/*
%{_bindir}/*
%{_mandir}/man1/*
%{_datadir}/%{name}/*
%{python3_sitelib}/*

%changelog
* Sat Nov 04 2023 Richard Dymond <rjdymond@gmail.com> 9.0
- Updated to 9.0

* Sat Jun 17 2023 Richard Dymond <rjdymond@gmail.com> 8.10-1
- Updated to 8.10

* Sun Feb 19 2023 Richard Dymond <rjdymond@gmail.com> 8.9-1
- Updated to 8.9

* Sat Nov 19 2022 Richard Dymond <rjdymond@gmail.com> 8.8-1
- Updated to 8.8

* Sat Oct 08 2022 Richard Dymond <rjdymond@gmail.com> 8.7-1
- Updated to 8.7

* Sat Nov 06 2021 Richard Dymond <rjdymond@gmail.com> 8.6-1
- Updated to 8.6

* Sat Jul 03 2021 Richard Dymond <rjdymond@gmail.com> 8.5-1
- Updated to 8.5

* Sat Mar 06 2021 Richard Dymond <rjdymond@gmail.com> 8.4-1
- Updated to 8.4

* Sun Nov 08 2020 Richard Dymond <rjdymond@gmail.com> 8.3-1
- Updated to 8.3

* Sun Jul 19 2020 Richard Dymond <rjdymond@gmail.com> 8.2-1
- Updated to 8.2

* Sun Mar 29 2020 Richard Dymond <rjdymond@gmail.com> 8.1-1
- Updated to 8.1

* Sat Nov 09 2019 Richard Dymond <rjdymond@gmail.com> 8.0-1
- Updated to 8.0

* Sun Jun 02 2019 Richard Dymond <rjdymond@gmail.com> 7.2-1
- Updated to 7.2

* Sat Feb 02 2019 Richard Dymond <rjdymond@gmail.com> 7.1-1
- Updated to 7.1

* Sat Oct 13 2018 Richard Dymond <rjdymond@gmail.com> 7.0-1
- Updated to 7.0

* Sat Mar 31 2018 Richard Dymond <rjdymond@gmail.com> 6.4-1
- Updated to 6.4

* Mon Feb 19 2018 Richard Dymond <rjdymond@gmail.com> 6.3-1
- Updated to 6.3

* Mon Jan 01 2018 Richard Dymond <rjdymond@gmail.com> 6.2-1
- Updated to 6.2

* Sun Sep 03 2017 Richard Dymond <rjdymond@gmail.com> 6.1-1
- Updated to 6.1

* Sat May 06 2017 Richard Dymond <rjdymond@gmail.com> 6.0-1
- Updated to 6.0

* Sun Jan 08 2017 Richard Dymond <rjdymond@gmail.com> 5.4-1
- Updated to 5.4

* Mon Sep 05 2016 Richard Dymond <rjdymond@gmail.com> 5.3-1
- Updated to 5.3

* Mon May 02 2016 Richard Dymond <rjdymond@gmail.com> 5.2-1
- Updated to 5.2

* Sat Jan 09 2016 Richard Dymond <rjdymond@gmail.com> 5.1-1
- Updated to 5.1

* Sun Oct 04 2015 Richard Dymond <rjdymond@gmail.com> 5.0-1
- Updated to 5.0

* Sat Jul 04 2015 Richard Dymond <rjdymond@gmail.com> 4.5-1
- Updated to 4.5

* Sat May 23 2015 Richard Dymond <rjdymond@gmail.com> 4.4-1
- Updated to 4.4

* Sat Feb 14 2015 Richard Dymond <rjdymond@gmail.com> 4.3-1
- Updated to 4.3

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
