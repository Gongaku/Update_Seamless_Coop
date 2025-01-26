#!/usr/bin/env python3

import logging
import platform
import shutil
import sys
from datetime import datetime
from tempfile import mkdtemp
from pathlib import Path
from zipfile import ZipFile

import update_ersc.releases as r
from update_ersc._version import __version__

def update_py_files(temp_path: Path, build: dict) -> None:
    download_link = build['zipball_url']
    build_version = build['tag_name']
    temporary_zip = r.download_build(download_link, temp_path, f"{build_version}.zip")

    with ZipFile(temporary_zip, 'r') as z:
        for archive in z.infolist():
            if "py" in archive.filename:
                extracted_file = z.extract(archive, temp_path)
                epoch_modified_timestamp = int(datetime(*archive.date_time).timestamp())
                r.correct_modified_timestamp(extracted_file, epoch_modified_timestamp)

    current_directory = Path(__file__).parent
    updated_files = list(temp_path.glob("*/*"))
    old_files = [f for f in list(current_directory.glob("*")) if '.py' == f.suffix]

    logging.info("Removing old files")
    shutil.os.mkdir(temp_path / "old")
    for old_file in old_files:
        shutil.move(old_file, temp_path / "old" / old_file.name)

    logging.info("Adding updated files")
    for updated_file in updated_files:
        if updated_file.name == "Update_Seamless_Coop.py":
            shutil.move(updated_file, current_directory.parent / updated_file.name)
        else:
            shutil.move(updated_file, current_directory / updated_file.name)


def update_executable(executable: Path, temp_path: Path, build: dict) -> None:
    build_version = build['tag_name']
    build_timestamp = datetime\
        .strptime(build['created_at'], '%Y-%m-%dT%H:%M:%SZ')
    operating_system = platform.system()
    file_extension = ".exe" if operating_system == "Windows" else ".bin"
    download_link = next((
        asset['browser_download_url']
        for asset in build['assets']
        if file_extension in asset['browser_download_url'].split("/")[-1]
    ))

    updated_file = r.download_build(download_link, temp_path, executable.name)
    backup_file = executable.parent / (executable.name + ".bak")
    old_permissions = executable.stat().st_mode

    shutil.move(executable, backup_file)
    # Moving backup file to temp folder to be deleted on Windows
    if backup_file.exists() and operating_system == "Windows":
        shutil.move(backup_file, temp_path / backup_file.name)

    shutil.move(updated_file, executable)
    r.correct_modified_timestamp(
        executable,
        build_timestamp.timestamp())
    shutil.os.chmod(executable, old_permissions)

    logging.info(f"Updated {executable.name} from {__version__} to {build_version}")


def update() -> None:
    if getattr(sys, 'frozen', False):
        application_path = sys.executable
    elif __file__:
        application_path = __file__
    application_path = Path(application_path)
    temp_path = Path(mkdtemp())

    latest_build = r.get_json_data("https://api.github.com/repos/Gongaku/Update_Seamless_Coop/releases/latest")
    latest_version = latest_build['tag_name']

    try:
        latest_build = r.get_json_data("https://api.github.com/repos/Gongaku/Update_Seamless_Coop/releases/latest")
        latest_version = latest_build['tag_name']

        if latest_version == f"v{__version__}":
            logging.info("Already at latest version")
            sys.exit(0)

        logging.info("Update was found")
        logging.info("Updating script...")
        if application_path.suffix == ".py":
            update_py_files(temp_path, latest_build)
        else:
            update_executable(application_path, temp_path, latest_build)
    except Exception as e:
        logging.exception(e)
    finally:
        shutil.rmtree(temp_path)
        logging.debug("Cleaned up temporary files")
        sys.exit(0)
