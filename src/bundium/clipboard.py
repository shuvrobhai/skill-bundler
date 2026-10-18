"""System clipboard interaction helpers."""

import shutil
import subprocess
import sys


class ClipboardError(Exception):
    """Raised when clipboard interaction fails or is unsupported."""
    pass


def _get_clipboard_command(action: str) -> list[str]:
    """Return command list for 'copy' or 'paste', or raise ClipboardError."""
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
        raise ClipboardError("No clipboard utility found. Install wl-copy, xclip, or xsel.")

    raise ClipboardError(f"Clipboard is not supported on {sys.platform}.")


def copy_to_clipboard(text: str) -> None:
    """Copy text to system clipboard. Raise ClipboardError on failure."""
    command = _get_clipboard_command("copy")
    try:
        subprocess.run(command, input=text.encode("utf-8"), check=True)
    except (subprocess.CalledProcessError, OSError) as err:
        raise ClipboardError(f"Failed to copy to clipboard: {err}") from err


def paste_from_clipboard() -> str:
    """Read and return text from system clipboard. Raise ClipboardError on failure."""
    command = _get_clipboard_command("paste")
    try:
        result = subprocess.run(command, capture_output=True, check=True)
        return result.stdout.decode("utf-8")
    except (subprocess.CalledProcessError, OSError) as err:
        raise ClipboardError(f"Failed to paste from clipboard: {err}") from err
