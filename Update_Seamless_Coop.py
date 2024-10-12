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
        action=argparse.BooleanOptionalAction,
        default=False
    )

    return parser.parse_args()


def get_install_path(steam_path: str) -> str:
    steam_path = os.path.join(steam_path, 'steamapps/libraryfolders.vdf')
    document = vdf.parse(open(steam_path))
    logging.info('Found Steam installation')
    logging.debug('Parsing all game directories for Elden Ring')
    
    for i in document['libraryfolders'].values():
        library_directory = os.path.abspath(i['path'])
        logging.debug(f'Checking "{library_directory}" for Elden Ring installation')
        elden_ring_install = os.path.join(library_directory, 'steamapps/common/ELDEN RING/Game')

        if os.path.exists(elden_ring_install):
            logging.info(f'Found Elden Ring download path: "{elden_ring_install}"')
            return elden_ring_install


def download_release() -> str:
    git_releases = requests.get("https://api.github.com/repos/LukeYui/EldenRingSeamlessCoopRelease/releases/latest")
    if git_releases.status_code != 200:
        logging.error("Unable to get the latest version Seamless Coop for Elden Ring")
        sys.exit(1)
    
    download_link = json.loads(git_releases.content)['assets'][0]['browser_download_url']    
    temporary_zip = os.path.join(temp_path, 'ersc.zip')
    version = download_link.split('/')[-2]
    logging.debug('Beginning download of latest release archive file from git repo')

    with open(temporary_zip, mode='wb') as release:
        release.write(requests.get(download_link).content)
        logging.info(f'Downloaded latest release: {version}')
    
    return temporary_zip
   

if __name__ == '__main__':
    args = parse_arguments()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.Formatter.converter = gmtime
    logging.basicConfig(
        level=log_level,
        datefmt='%Y-%m-%dT%H:%M:%S',
        format='%(levelname)s | %(asctime)s.%(msecs)03dZ | %(message)s'
    )

    if platform.system() == "Windows":
        import winreg
        hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\WOW6432Node\Valve\Steam")
        steam_path = winreg.QueryValueEx(hkey, "InstallPath")[0]
        temp_path = "C:\\Temp"
    else:
        steam_path = ""
        temp_path = "/tmp"

    installation_path: str = get_install_path(steam_path=steam_path)
    mod_path: str = os.path.join(installation_path, 'SeamlessCoop')
    settings_file_path = os.path.join(installation_path, 'SeamlessCoop/ersc_settings.ini')
    
    temporary_zip = download_release()

    if not os.path.exists(mod_path):
        mod_installed = False
        logging.error('Seamless Coop is not installed on the system.')
    else:
        mod_installed = True
        shutil.copy2(settings_file_path, temp_path)
        logging.debug(f"Copied Seamless Coop config file to \"{temp_path}\"")
        
    with zipfile.ZipFile(temporary_zip, 'r') as zip_ref:
        zip_ref.extractall(installation_path)
        logging.debug('Extracted latest release')

    if mod_installed:
        shutil.copy2(os.path.join(temp_path, 'ersc_settings.ini'), settings_file_path)
        logging.debug(f'Copied previous settings file')
        logging.info('Completed Update')
    else:
        logging.info('Completed Installation')

