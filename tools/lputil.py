#!/usr/bin/env python
import argparse
import time
from datetime import datetime
import os
from launchpadlib.launchpad import Launchpad

APPLICATION = 'skrelease'
SERIES_SUMMARY = 'The current stable series, recommended for all users.'
PREV_SERIES_STATUS = 'Supported'
ZIP_FILE_TYPE = TARBALL_FILE_TYPE = 'Code Release Tarball'
RPM_FILE_TYPE = DEB_FILE_TYPE = 'Installer file'

class LaunchpadError(Exception):
    pass

def _add_files(milestone, project_title, project_name, project_dist):
    version = milestone.name

    zip_archive = (
        '{}/{}-{}.zip'.format(project_dist, project_name, version),
        'application/zip',
        ZIP_FILE_TYPE,
        '{} {} zip archive'.format(project_title, version)
    )
    tarball = (
        '{}/{}-{}.tar.xz'.format(project_dist, project_name, version),
        'application/x-tar',
        TARBALL_FILE_TYPE,
        '{} {} tarball'.format(project_title, version)
    )
    rpm = (
        '{}/{}-{}-1.noarch.rpm'.format(project_dist, project_name, version),
        'application/x-redhat-package-manager',
        RPM_FILE_TYPE,
        '{} {} RPM package'.format(project_title, version)
    )
    deb = (
        '{}/{}_{}-1_all.deb'.format(project_dist, project_name, version),
        'application/x-debian-package',
        DEB_FILE_TYPE,
        '{} {} DEB package'.format(project_title, version)
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
        signature_content = None
        if os.path.isfile(signature_filename):
            with open(signature_filename) as f:
                signature_content = f.read()
        fname = os.path.basename(filename)
        kwargs = {}
        if signature_content:
            kwargs['signature_filename'] = os.path.basename(signature_filename)
            kwargs['signature_content'] = signature_content
        print("Uploading {}".format(fname))
        release.add_file(filename=fname,
                         file_content=file_content,
                         content_type=content_type,
                         file_type=file_type,
                         description=description,
                         **kwargs)

def run(server, project_title, project_name, version, project_dist):
    launchpad = Launchpad.login_with(APPLICATION, server)
    project = launchpad.projects[project_name]

    version_numbers = version.split('.')
    series_name = '{}.{}.x'.format(version_numbers[0], version_numbers[1])
    series = project.getSeries(name=series_name)
    if series is None:
        if len(version_numbers) != 2:
            raise LaunchpadError('Cannot find series {}'.format(series_name))
        # This is an X.Y version, so create a new series (X.Y.x)
        print("Creating new series: {}".format(series_name))
        series = project.newSeries(name=series_name, summary=SERIES_SUMMARY)
        project.development_focus = series
        project.lp_save()
        prev_series = project.series[len(project.series) - 2]
        print("Setting status of previous series ({}) to '{}'".format(prev_series.name, PREV_SERIES_STATUS))
        prev_series.status = PREV_SERIES_STATUS
        prev_series.lp_save()
    else:
        print("Using existing series: {}".format(series_name))

    milestone = project.getMilestone(name=version)
    if milestone is None:
        print("Creating new milestone: {}".format(version))
        target_date = time.strftime('%Y-%m-%d', time.localtime())
        milestone = series.newMilestone(name=version, date_targeted=target_date)
    else:
        print("Using existing milestone: {}".format(version))

    _add_files(milestone, project_title, project_name, project_dist)

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
group.add_argument('--pyskool', dest='pyskool', action='store_true',
                   help="Update the Pyskool project instead of SkoolKit")
namespace, unknown_args = parser.parse_known_args()
if unknown_args or not namespace.version:
    parser.exit(2, parser.format_help())
server = 'production' if namespace.production else 'staging'
if namespace.pyskool:
    project_title = 'Pyskool'
    varname = 'PYSKOOL_HOME'
else:
    project_title = 'SkoolKit'
    varname = 'SKOOLKIT_HOME'
project_name = project_title.lower()
version = namespace.version[0]
project_home = os.environ.get(varname)
if not project_home:
    sys.stderr.write('{} is not set; aborting\n'.format(varname))
    sys.exit(1)
project_dist = '{}/dist'.format(project_home)
if not os.path.isdir(project_dist):
    sys.stderr.write('{}: directory not found\n'.format(project_dist))
    sys.exit(1)
run(server, project_title, project_name, version, project_dist)
