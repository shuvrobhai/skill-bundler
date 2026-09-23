"""System clipboard interaction helpers."""

import shutil
import subprocess
import sys


from typing import List


def _get_clipboard_command(action: str) -> List[str]:
    """Return command list for 'copy' or 'paste', or exit with error."""
    if sys.platform == "darwin":
        return ["pbcopy"] if action == "copy" else ["pbpaste"]

    if sys.platform.startswith("linux"):
        candidates = {
            "copy": [
                ["wl-copy"],
                ["xclip", "-selection", "clipboard"],
                ["xsel", "--clipboard", "--input"],
            ],
            "paste": [
                ["wl-paste"],
                ["xclip", "-selection", "clipboard", "-o"],
                ["xsel", "--clipboard", "--output"],
            ],
        }
        for command in candidates[action]:
            if shutil.which(command[0]):
                return command
        sys.exit("Error: no clipboard utility found. Install wl-copy, xclip, or xsel.")

    sys.exit(f"Error: clipboard not supported on {sys.platform}.")


def copy_to_clipboard(text: str) -> None:
    """Copy text to system clipboard. Exit on failure."""
    command = _get_clipboard_command("copy")
    subprocess.run(command, input=text.encode("utf-8"), check=True)


def paste_from_clipboard() -> str:
    """Read and return text from system clipboard. Exit on failure."""
    command = _get_clipboard_command("paste")
    result = subprocess.run(command, capture_output=True, check=True)
    return result.stdout.decode("utf-8")
