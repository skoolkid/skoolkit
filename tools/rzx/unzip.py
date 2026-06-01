#!/usr/bin/env python3
import datetime
import os
import sys
import time
import zipfile

if len(sys.argv) != 3:
    print("""
Usage: {} file.zip DESTDIR

  Extract files from file.zip in DESTDIR (which must exist). Unlike Info-ZIP's
  'unzip', this writes files with names properly encoded in UTF-8.
""".strip().format(os.path.basename(sys.argv[0])))
    sys.exit(1)

z = zipfile.ZipFile(sys.argv[1])
for info in z.infolist():
    if info.is_dir():
        continue
    fname = info.filename
    ofile = os.path.join(sys.argv[2], fname.lstrip('/'))
    odir = os.path.dirname(ofile)
    if not os.path.isdir(odir):
        os.makedirs(odir)
    member = z.open(fname)
    with open(ofile, 'wb') as f:
        f.write(member.read())
    mtime = time.mktime(datetime.datetime(*info.date_time).timetuple())
    os.utime(ofile, (mtime, mtime))
    print(f'Wrote {ofile}')
z.close()
