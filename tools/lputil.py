#!/usr/bin/env python
import argparse
import time
from datetime import datetime
import os
from launchpadlib.launchpad import Launchpad

SKOOLKIT_HOME = os.environ.get('SKOOLKIT_HOME')
if not SKOOLKIT_HOME:
    sys.stderr.write('SKOOLKIT_HOME is not set; aborting\n')
    sys.exit(1)
SKOOLKIT_DIST = '{}/dist'.format(SKOOLKIT_HOME)
if not os.path.isdir(SKOOLKIT_DIST):
    sys.stderr.write('{}: directory not found\n'.format(SKOOLKIT_DIST))
    sys.exit(1)

APPLICATION = 'skrelease'
SERIES_SUMMARY = 'The current stable series, recommended for all users.'
PREV_SERIES_STATUS = 'Supported'
ZIP_FILE_TYPE = TARBALL_FILE_TYPE = 'Code Release Tarball'
RPM_FILE_TYPE = DEB_FILE_TYPE = 'Installer file'

class LaunchpadError(Exception):
    pass

def _add_files(milestone):
    version = milestone.name

    zip_archive = (
        '{}/skoolkit-{}.zip'.format(SKOOLKIT_DIST, version),
        'application/zip',
        ZIP_FILE_TYPE,
        'SkoolKit {} zip archive'.format(version)
    )
    tarball = (
        '{}/skoolkit-{}.tar.xz'.format(SKOOLKIT_DIST, version),
        'application/x-tar',
        TARBALL_FILE_TYPE,
        'SkoolKit {} tarball'.format(version)
    )
    rpm = (
        '{}/skoolkit-{}-1.noarch.rpm'.format(SKOOLKIT_DIST, version),
        'application/x-redhat-package-manager',
        RPM_FILE_TYPE,
        'SkoolKit {} RPM package'.format(version)
    )
    deb = (
        '{}/skoolkit_{}-1_all.deb'.format(SKOOLKIT_DIST, version),
        'application/x-debian-package',
        DEB_FILE_TYPE,
        'SkoolKit {} DEB package'.format(version)
    )

    if milestone.release is None:
        print("Creating new release for milestone {}".format(version))
        release_date = datetime.utcfromtimestamp(os.stat(tarball[0]).st_mtime)
        release = milestone.createProductRelease(date_released=release_date)
    else:
        print("Using existing release for milestone {}".format(version))
        release = milestone.release

    if release.files:
        print("Deleting existing files")
        for f in release.files:
            try:
                f.delete()
            except:
                # delete() returns a 404 Not Found error
                pass
    if release.files:
        raise LaunchpadError("Unable to delete existing files")

    for filename, content_type, file_type, description in (zip_archive, tarball, rpm, deb):
        with open(filename, 'rb') as f:
            file_content = f.read()
        signature_filename = filename + '.asc'
        with open(signature_filename) as f:
            signature_content = f.read()
        fname = os.path.basename(filename)
        print("Uploading {}".format(fname))
        release.add_file(filename=fname,
                         file_content=file_content,
                         signature_filename=os.path.basename(signature_filename),
                         signature_content=signature_content,
                         content_type=content_type,
                         file_type=file_type,
                         description=description)

def run(server, version):
    launchpad = Launchpad.login_with(APPLICATION, server)
    skoolkit = launchpad.projects['skoolkit']

    version_numbers = version.split('.')
    series_name = '{}.{}.x'.format(version_numbers[0], version_numbers[1])
    series = skoolkit.getSeries(name=series_name)
    if series is None:
        if len(version_numbers) != 2:
            raise LaunchpadError('Cannot find series {}'.format(series_name))
        # This is an X.Y version, so create a new series (X.Y.x)
        print("Creating new series: {}".format(series_name))
        series = skoolkit.newSeries(name=series_name, summary=SERIES_SUMMARY)
        skoolkit.development_focus = series
        skoolkit.lp_save()
        prev_series = skoolkit.series[len(skoolkit.series) - 2]
        print("Setting status of previous series ({}) to '{}'".format(prev_series.name, PREV_SERIES_STATUS))
        prev_series.status = PREV_SERIES_STATUS
        prev_series.lp_save()
    else:
        print("Using existing series: {}".format(series_name))

    milestone = skoolkit.getMilestone(name=version)
    if milestone is None:
        print("Creating new milestone: {}".format(version))
        target_date = time.strftime('%Y-%m-%d', time.localtime())
        milestone = series.newMilestone(name=version, date_targeted=target_date)
    else:
        print("Using existing milestone: {}".format(version))

    _add_files(milestone)

###############################################################################
# Begin
###############################################################################
parser = argparse.ArgumentParser(
    usage='lputil.py [options] X.Y[.Z]',
    description="Update the SkoolKit project on Launchpad for version X.Y[.Z].",
    add_help=False
)
parser.add_argument('version', help=argparse.SUPPRESS, nargs='*')
group = parser.add_argument_group('Options')
group.add_argument('--production', dest='production', action='store_true',
                   help="Use launchpad.net instead of staging.launchpad.net")
namespace, unknown_args = parser.parse_known_args()
if unknown_args or not namespace.version:
    parser.exit(2, parser.format_help())
server = 'production' if namespace.production else 'staging'
version = namespace.version[0]
run(server, version)
