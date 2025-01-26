#!/usr/bin/env python3

import logging
import shutil
from datetime import datetime
from pathlib import Path
from tempfile import mkdtemp

import update_ersc.releases as r
import update_ersc.steam_libraries

def get_elden_ring_path(steam_path: str | Path = None) -> Path:
    """
    Searchs through all of Steam library paths,
    to find where Elden Ring is installed on the system

    Returns Elden Ring installation path
    """
    steam_root = steam_libraries.get_steam_root() \
        if steam_path is None \
        else steam_path

    libaries = steam_libraries.fetch_game_libraries(steam_root)

    for libary in libaries:
        library_directory = Path(libary['path'])
        logging.info(f"Checking \"{library_directory}\" for Elden Ring")
        elden_ring_install = library_directory / "steamapps/common/ELDEN RING/Game"
        if elden_ring_install.exists():
            logging.info(f'Found Elden Ring download path => "{elden_ring_install}"')
            break

    return elden_ring_install


def fetch_ersc_releases(
    url: str
):
    all_releases = r.get_json_data(
        "https://api.github.com/repos/LukeYui/EldenRingSeamlessCoopRelease/releases"
    )
    builds = []
    for release in all_releases:
        created = release['created_at']
        version_number = release['tag_name']
        download_link = release['assets'][0]['browser_download_url']
        builds.append({'created': created, 'version': version_number, 'link': download_link})

    return builds


def update_ersc(
    installation_path: Path,
    mod_path: Path,
    temp_path: Path
) -> None:
    logging.info("ERSC is installed locally")
    logging.info("Checking for update...")

    releases = fetch_ersc_releases(
        "https://api.github.com/repos/LukeYui/EldenRingSeamlessCoopRelease/releases"
    )

    updated_needed = False
    ersc_dll = mod_path / "ersc.dll"
    c_time = datetime.fromtimestamp(ersc_dll.stat().st_mtime)

    current_version = None
    for release in releases:
        created_timestamp = datetime\
            .strptime(release['created'], '%Y-%m-%dT%H:%M:%SZ')

        if created_timestamp.date() > c_time.date():
            updated_needed = True

        if c_time > created_timestamp:
            current_version = release['version']
            break

    _, latest_version, download_link = releases[0].values()
    if updated_needed:
        if current_version:
            logging.info(f"Updating from {current_version} to {latest_version}")
        else:
            logging.warning("Unable to determine current version of ERSC")
            logging.info("Updating to latest version")

        settings_file_path = mod_path / "ersc_settings.ini"
        shutil.copy2(settings_file_path, temp_path)
        logging.debug(f"Copied Seamless Coop ini file to \"{temp_path}\"")

        temporary_zip = r.download_build(
            url=download_link,
            output_path=temp_path,
            filename='ersc.zip'
        )

        r.extract_file(installation_path, temporary_zip)
        logging.info("Update completed")
    else:
        logging.info(f"No update needed. Currently at latest version: {latest_version}")


def download_ersc(
    installation_path: Path,
    temp_path: Path
) -> None:
    latest_build = r.get_json_data(
        "https://api.github.com/repos/LukeYui/EldenRingSeamlessCoopRelease/releases/latest")
    download_link = latest_build['assets'][0]['browser_download_url']
    version = download_link.split('/')[-2]

    logging.info(f"Downloading build {version}")
    temporary_zip = r.download_build(
        url=download_link,
        output_path=temp_path,
        filename='ersc.zip'
    )
    r.extract_file(installation_path, temporary_zip)
    logging.info("Installation Completed")


def perform_installation(steam_path: str = None):
    temp_path = Path(mkdtemp())
    installation_path = get_elden_ring_path(steam_path)
    mod_path = installation_path / "SeamlessCoop"
    mod_installed = mod_path.exists()

    if mod_installed:
        update_ersc(installation_path, mod_path, temp_path)
    else:
        download_ersc(installation_path, temp_path)

    shutil.rmtree(temp_path)
    logging.debug(f"Cleaned up {temp_path}")
