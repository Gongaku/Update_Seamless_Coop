#!/usr/bin/env python3

import json
import logging
import os
import platform
import requests
import shutil
import sys
import vdf
from argparse import ArgumentParser, Namespace
from time import gmtime
from tempfile import mkdtemp
from zipfile import ZipFile
from _version import __version__


def parse_arguments() -> Namespace:
    parser = ArgumentParser(
        description='''
        This tool is meant to download the latest version of the Seamless Coop Elden Ring Mod.
        This will install the mod for you if not installed.
        If the mod is already installed, it will keep the old ini file and download the latest version of the mod.
        ''',
        add_help=True
    )

    parser.add_argument(
        '-s',
        '--steam_path',
        type=str,
        help="Direct path to steam downloads folder. This is in case you have a non-standard steam location."
    )

    parser.add_argument(
        '-u',
        '--update',
        action='store_true',
        help='Update the script to the latest version from Github'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        default=False,
        help='Print all log message to console'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s ' + __version__
    )

    return parser.parse_args()


def get_steam_path() -> str:
    """
    Returns steam path on current system

    Currently no implementation for MacOS
    """
    if platform.system() == "Windows":
        import winreg
        hkey = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Valve\Steam"
        )
        steam_path = winreg.QueryValueEx(hkey, "InstallPath")[0]
    elif platform.system() == "Linux":
        steam_path = os.path.expanduser("~/.steam/steam")
    elif platform.system() == "Darwin":
        steam_path = os.path.expanduser("~/Library/Application Support/Steam")

    logging.debug(f"Validating Steam Path: {steam_path}")
    if not os.path.exists(steam_path):
        logging.error(f"Invalid Steam Path: {steam_path}")
        logging.error("Unable to find steam path")
        sys.exit(1)
    logging.debug(f"Steam Path: {steam_path}")
    return steam_path


def get_install_path(steam_path: str) -> str:
    """
    Searchs through all of Steam library paths,
    to find where Elden Ring is installed on the system

    Returns Elden Ring installation path
    """
    steam_path = os.path.expanduser(steam_path)
    logging.debug(f"Steam Libraries: {steam_path}")

    document = vdf.parse(open(steam_path))
    logging.info('Found Steam installation')
    logging.debug('Parsing all game directories for Elden Ring')

    for i in document['libraryfolders'].values():
        library_directory = os.path.abspath(i['path'])
        logging.debug(f'Checking "{library_directory}" for Elden Ring installation')
        elden_ring_install = os.path.join(
            library_directory,
            'steamapps/common/ELDEN RING/Game'
        )

        if os.path.exists(elden_ring_install):
            logging.info(f'Found Elden Ring download path: "{elden_ring_install}"')
            break

    return elden_ring_install


def download_release(
    url: str,
    output_path: str,
    filename: str,
    file_type: str = 'exe'
) -> str:
    """
    Download requested file from github
    """
    git_releases = requests.get(url)

    if git_releases.status_code != 200:
        logging.error("Unable to get the latest version")
        sys.exit(1)
    assert git_releases.status_code == 200

    if file_type == 'py':
        download_link = json.loads(git_releases.content)['zipball_url']
        version = download_link.split('/')[-1]
    else:
        download_link = json.loads(git_releases.content)['assets'][0]['browser_download_url']
        version = download_link.split('/')[-2]

    temporary_zip = os.path.join(output_path, filename)

    with open(os.path.join(output_path, 'current_version'), 'w') as version_number:
        version_number.write(version)

    logging.debug('Beginning download of latest release from git repo')

    with open(temporary_zip, mode='wb') as release:
        release.write(requests.get(download_link).content)
        logging.info(f'Downloaded release: {version}')

    return temporary_zip


def extract_file(
    extract_path: str,
    filename: str
) -> str:
    """
    Extracts zip file.

    Returns extracted file/directory name
    """
    output_file = None
    with ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
        logging.debug(f"Extracted latest release to \"{extract_path}\"")
        output_file = zip_ref.filename
    return output_file


def self_update(
    output_path: str
) -> None:
    """
    Performs call to git to update the script to the latest version.

    Performs different actions depending on if script is an executable
    or python file
    """
    if getattr(sys, 'frozen', False):
        application_path = sys.executable
    elif __file__:
        application_path = __file__
    script_path, script_name = os.path.split(application_path)

    latest_version = json.loads(requests.get(
        "https://api.github.com/repos/Gongaku/Update_Seamless_Coop/releases/latest"
    ).content)['tag_name']

    if latest_version == f'v{__version__}':
        logging.info('Already at latest version')
        sys.exit(0)

    logging.info(f'Updating "{script_name}"')
    if 'py' in script_name:
        release_file = download_release(
            url="https://api.github.com/repos/Gongaku/Update_Seamless_Coop/releases/latest",
            output_path=output_path,
            filename=script_name,
            file_type='py'
        )
        temporary_zip = os.path.splitext(script_name)[0]+'.zip'
        shutil.move(
            release_file,
            temporary_zip
        )

        extract_file(
            script_path,
            temporary_zip
        )

        directories = [item for item in os.listdir(script_path) if os.path.isdir(item) and 'git' not in item]
        directories.sort(key=lambda s: os.path.getmtime(os.path.join(script_path, s)))
        extracted_dir = directories[-1]

        os.remove(temporary_zip)
        shutil.move(
            os.path.join(script_path, extracted_dir+'/'+script_name),
            __file__
        )
        shutil.rmtree(extracted_dir)
    else:
        operating_system = platform.system()
        release_file = download_release(
            url="https://api.github.com/repos/Gongaku/Update_Seamless_Coop/releases/latest",
            output_path=output_path,
            filename=script_name,
            file_type='exe'
        )

        backup_file = os.path.join(
            script_path,
            os.path.splitext(script_name)[0]+'.bak'
        )
        if os.path.exists(backup_file) and operating_system == "Windows":
            os.remove(backup_file)

        shutil.move(
            application_path,
            backup_file
        )

        logging.debug(f"Moved old version of script to {backup_file}")
        shutil.copy2(
            release_file,
            application_path
        )

        if operating_system == "Windows":
            logging.info(f"You can delete \"{backup_file}\". It's a backup of the old version of {script_name}")

    with open(os.path.join(output_path, 'current_version'), 'r') as version_file:
        version = version_file.read()
    logging.info(f"Script has self updated from v{__version__} to {version}")
    shutil.rmtree(output_path)
    sys.exit(0)


if __name__ == '__main__':
    args = parse_arguments()

    script_directory, script_name = os.path.split(__file__)
    log_file = os.path.splitext(script_name)[0] + '.log'
    handlers = [
        logging.StreamHandler(),
        logging.FileHandler(filename=log_file, mode='w')
    ]
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.Formatter.converter = gmtime
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        datefmt='%Y-%m-%dT%H:%M:%S',
        format=' %(levelname)-6s | %(asctime)s.%(msecs)03dZ | %(message)s'
    )

    temp_path = mkdtemp()
    if args.update:
        self_update(temp_path)

    steam_path = args.steam_path if args.steam_path else get_steam_path()
    steam_path = os.path.join(
        steam_path,
        'steamapps/libraryfolders.vdf'
    )
    installation_path: str = get_install_path(steam_path)
    mod_path: str = os.path.join(
        installation_path,
        "SeamlessCoop"
    )
    settings_file_path: str = os.path.join(
        installation_path,
        "SeamlessCoop/ersc_settings.ini"
    )
    temporary_zip: str = download_release(
        url="https://api.github.com/repos/LukeYui/EldenRingSeamlessCoopRelease/releases/latest",
        output_path=temp_path,
        filename='ersc.zip'
    )

    # Keep copy of ini file in temp_path if mod is installed
    if not os.path.exists(mod_path):
        mod_installed = False
        logging.warning("Seamless Coop is not installed on the system")
        logging.info("Beginning Seamless Coop installation")
    else:
        mod_installed = True
        shutil.copy2(settings_file_path, temp_path)
        logging.debug(f"Copied Seamless Coop ini file to \"{temp_path}\"")

    # Extract downloaded file
    extract_file(installation_path, temporary_zip)
    os.remove(temporary_zip)

    # If mod is installed, move keep of original file back to correct location
    if mod_installed:
        shutil.copy2(
            os.path.join(temp_path, "ersc_settings.ini"),
            settings_file_path
        )
        logging.debug("Copied previous ini file")

    # Ending Info
    operation = "Update" if mod_installed else "Installation"
    logging.info(f"{operation} Complete")

    if platform.system() == "Linux":
        logging.info(
            "As you're a Linux user, you will need to add the ersc_launcher.exe"
            "as a Steam Game and force proton compatability"
        )
    shutil.rmtree(temp_path)
