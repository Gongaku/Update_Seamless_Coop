#!/usr/bin/env python3

import logging
from argparse import ArgumentParser, Namespace
from pathlib import Path

import coloredlogs
from update_ersc import ersc, update_self
from update_ersc._version import __version__

def parse_arguments() -> Namespace:
    parser = ArgumentParser(
        description='''
        This tool is meant to download the latest version of the Seamless Coop Elden Ring Mod.
        This will install the mod for you if not installed.
        If the mod is already installed, it will keep the old ini file and download the latest version of the mod.
        ''',
        add_help=True)

    parser.add_argument(
        '-s',
        '--steam_path',
        type=str,
        help="Direct path to steam downloads folder. "
        "This is in case you have a non-standard steam location.")

    parser.add_argument(
        '--gui',
        action='store_true',
        help='Launch Graphical Interface')

    parser.add_argument(
        '-u',
        '--update',
        action='store_true',
        help='Update the script to the latest version from Github')

    parser.add_argument(
        '-q',
        '--quiet',
        action='store_false',
        help='Silences console output')

    parser.add_argument(
        '--verbose',
        action='store_true',
        default=False,
        help='Print all log message to console')

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s ' + __version__)

    return parser.parse_args()


def setup_logs(log_file: Path, console: bool = False, verbose: bool = False) -> None:
    log_level = logging.INFO
    file_handler = logging.FileHandler(log_file, mode="w")
    file_handler.setLevel(log_level)

    if verbose:
        log_level = logging.DEBUG

    logging.basicConfig(
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        handlers=[file_handler],
        level=log_level)

    if console:
        fields_styles = {
            'asctime': {'color': 'green'},
            'levelname': {'bold': True},
        }

        level_styles = {
            'critical': {'bold': True, 'color': 'red'},
            'debug': {},
            'error': {'color': 'red'},
            'info': {'color': 'green'},
            'notice': {'color': 'magenta'},
            'spam': {'color': 'green', 'faint': True},
            'success': {'bold': True, 'color': 'green'},
            'verbose': {'color': 'blue'},
            'warning': {'color': 'yellow'}
        }

        coloredlogs.install(
            fmt='%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt="%Y-%m-%dT%H:%M:%S%z",
            field_styles=fields_styles,
            level_styles=level_styles,
            level=log_level)


if __name__ == "__main__":
    args = parse_arguments()

    script_path = Path(__file__)
    prefix = script_path.stem
    log_file = script_path.parent / f"{prefix}.log"
    setup_logs(log_file, console=args.quiet, verbose=args.verbose)

    if args.update:
        update_self.update()
    elif args.gui:
        pass
    else:
        steam_path = args.steam_path if args.steam_path else None
        ersc.perform_installation(steam_path)
