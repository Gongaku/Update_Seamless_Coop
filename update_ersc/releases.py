import json
import logging
from datetime import datetime
from os import utime
from pathlib import Path
from zipfile import ZipFile

import requests

def get_json_data(
    url: str,
) -> tuple:
    build_info = None

    try:
        release = requests.get(url)
        build_info = json.loads(release.content)
    except requests.HTTPError as ex:
        logging.error(f"Encountered an {ex}")
    except requests.Timeout:
        logging.error(f"Request timed out for {url}")

    return build_info


def download_build(
    url: str,
    output_path: Path,
    filename: str,
) -> None:
    downloaded_build = output_path / filename

    with open(downloaded_build, mode='wb') as release:
        release.write(requests.get(url).content)

    return downloaded_build


def correct_modified_timestamp(filename: Path, timestamp_since_epoch: int) -> None:
    modified_timestamp = (timestamp_since_epoch, timestamp_since_epoch)
    utime(filename, modified_timestamp)
    logging.debug("Corrected last modified timestamp")


def extract_file(
    extract_path: Path,
    filename: str
) -> str:
    with ZipFile(filename, 'r') as zip_file:
        logging.debug(f"Archive: {filename}")
        for archive in zip_file.infolist():
            name = extract_path / Path(archive.filename)
            with open(name, 'wb') as extracted_file:
                extracted_file.write(zip_file.open(archive).read())
                logging.debug(f"  inflating: {archive.filename}")

            # Update last modified timestamp of files to match git
            epoch_modified_timestamp = int(datetime(*archive.date_time).timestamp())
            correct_modified_timestamp(name, epoch_modified_timestamp)

    logging.info(f"Extracted latest release to \"{extract_path}\"")
