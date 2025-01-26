import logging
import platform
from pathlib import Path
import vdf

def get_steam_root() -> Path:
    """
    Returns steam root path on current system
    """
    operating_system = platform.system()
    logging.info(f"Operating System: {operating_system}")
    if operating_system == "Windows":
        import winreg
        hkey = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Valve\Steam"
        )
        steam_register = winreg.QueryValueEx(hkey, "InstallPath")[0]
        steam_path = Path(steam_register)
    elif operating_system == "Linux":
        steam_path = Path("~/.steam/steam").expanduser()
    elif operating_system == "Darwin":
        steam_path = Path("~/Library/Application Support/Steam").expanduser()
    else:
        raise NotImplementedError("Unable to determine operating system. \
            The function get_steam_root is not implemented for this operating system.")

    return steam_path


def fetch_library_vdf(steam_root: Path) -> dict:
    """
    Returns contents of the steam "libraryfolders.vdf" file.
This file contains the path, label, total size, update_clean_bytes_tally, time_last_update_verified, and apps for each given local steam library.
    """
    steam_path = steam_root / "steamapps/libraryfolders.vdf"
    logging.info(f"Steam Library VDF location: \"{steam_path}\"")

    file_contents = None
    with open(steam_path, "r") as vdf_file:
        file_contents = vdf.parse(vdf_file)

    return file_contents


def fetch_game_libraries(steam_root: Path) -> list[str]:
    """Returns the paths of all steam libraries on the local machine"""
    vdf_file = fetch_library_vdf(steam_root)
    return vdf_file['libraryfolders'].values()
