#!/usr/bin/env python3

import argparse
import json
import logging
import os
import platform
import requests
import shutil
import sys
import vdf
import zipfile
from time import gmtime


def parse_arguments() -> None:
    parser = argparse.ArgumentParser(
        description='''
        This tool is meant to download the latest version of the Seamless Coop Elden Ring Mod.
        This will install the mod for you if not installed.
        If the mod is already installed, it will keep the old ini file and download the latest version of the mod.
        ''',
        add_help=True
    )

    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        default=False,
        help='Print all log message to console'
    )

    parser.add_argument(
        '-u',
        '--update',
        action='store_true',
        help='Update the script to the latest version from Github'
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
        raise NotImplementedError("OS X not supported")

    return steam_path


def get_install_path() -> str:
    """
    Searchs through all of Steam library paths,
    to find where Elden Ring is installed on the system

    Returns Elden Ring installation path
    """
    steam_path = os.path.join(
        get_steam_path(),
        'steamapps/libraryfolders.vdf'
    )
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


def download_release(url: str, output_path: str, filename: str, file_type: str='exe') -> str:
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
    logging.debug('Beginning download of latest release from git repo')

    with open(temporary_zip, mode='wb') as release:
        release.write(requests.get(download_link).content)
        logging.info(f'Downloaded latest release: {version}')

    return temporary_zip


def extract_file(extract_path: str, filename: str) -> str: 
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
        logging.debug(f"Extracted latest release to \"{extract_path}\"")
        return zip_ref.filename


if __name__ == '__main__':
    args = parse_arguments()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.Formatter.converter = gmtime
    logging.basicConfig(
        level=log_level,
        datefmt='%Y-%m-%dT%H:%M:%S',
        format=' %(levelname)-6s | %(asctime)s.%(msecs)03dZ | %(message)s'
    )

    temp_path = r"C:\Temp" if platform.system() == "Windows" else "/tmp"

    if args.update:
        script_path, script_name = os.path.split(__file__)

        logging.info(f'Updating "{__file__}"')
        file_type = 'exe' if 'exe' in script_name else 'py'
        release_file = download_release(
            url="https://api.github.com/repos/Gongaku/Update_Seamless_Coop/releases/latest",
            output_path=temp_path,
            filename=script_name,
            file_type=file_type
        )
        shutil.move(
            release_file, 
            os.path.splitext(script_name)[0]+'.zip'
        )
        
        extracted_file = extract_file(
            script_path, 
            os.path.splitext(script_name)[0]+'.zip'
        )
        # print(os.listdir())
        directories = [item for item in os.listdir(script_path) if os.path.isdir(item) and 'git' not in item]
        extracted_dir = directories[0]
        
        os.remove(os.path.splitext(script_name)[0]+'.zip')
        shutil.move(
            os.path.join(script_path, extracted_dir+'/'+script_name),
            __file__
        )
        shutil.rmtree(extracted_dir)
        sys.exit(0)

    steam_path = get_steam_path()
    installation_path: str = get_install_path()
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
    logging.info(f"Completed {operation}")

    if platform.system() == "Linux":
        logging.info(
            "As you're a Linux user, you will need to add the ersc_launcher.exe as a Steam Game and force proton compatability"
        )