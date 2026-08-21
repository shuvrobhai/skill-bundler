"""System clipboard interaction helpers."""

import shutil
import subprocess
import sys


def copy_to_clipboard(text: str) -> None:
    """Copy text to system clipboard. Exit on failure."""
    if sys.platform == "darwin":
        cmd = ["pbcopy"]
    elif sys.platform.startswith("linux"):
        cmd = None
        for candidate in [
            ["wl-copy"],
            ["xclip", "-selection", "clipboard"],
            ["xsel", "--clipboard", "--input"],
        ]:
            if shutil.which(candidate[0]):
                cmd = candidate
                break
        if cmd is None:
            sys.exit("Error: no clipboard utility found. Install wl-copy, xclip, or xsel.")
    else:
        sys.exit(f"Error: clipboard not supported on {sys.platform}.")

    subprocess.run(cmd, input=text.encode("utf-8"), check=True)


def paste_from_clipboard() -> str:
    """Read and return text from system clipboard. Exit on failure."""
    if sys.platform == "darwin":
        cmd = ["pbpaste"]
    elif sys.platform.startswith("linux"):
        cmd = None
        for candidate in [
            ["wl-paste"],
            ["xclip", "-selection", "clipboard", "-o"],
            ["xsel", "--clipboard", "--output"],
        ]:
            if shutil.which(candidate[0]):
                cmd = candidate
                break
        if cmd is None:
            sys.exit("Error: no clipboard utility found. Install wl-paste, xclip, or xsel.")
    else:
        sys.exit(f"Error: clipboard not supported on {sys.platform}.")

    result = subprocess.run(cmd, capture_output=True, check=True)
    return result.stdout.decode("utf-8")
