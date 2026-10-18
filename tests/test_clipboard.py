"""Unit tests for the bundium.clipboard module."""

import unittest
from unittest.mock import patch

from bundium.clipboard import (
    ClipboardError,
    copy_to_clipboard,
    paste_from_clipboard,
)


class TestClipboard(unittest.TestCase):
    """Test suite for typed clipboard error handling in various environments."""

    @patch("sys.platform", "linux")
    @patch("shutil.which", return_value=None)
    def test_headless_linux_copy_raises_clipboard_error(self, mock_which):
        with self.assertRaises(ClipboardError) as ctx:
            copy_to_clipboard("test content")
        self.assertIn("No clipboard utility found", str(ctx.exception))

    @patch("sys.platform", "linux")
    @patch("shutil.which", return_value=None)
    def test_headless_linux_paste_raises_clipboard_error(self, mock_which):
        with self.assertRaises(ClipboardError) as ctx:
            paste_from_clipboard()
        self.assertIn("No clipboard utility found", str(ctx.exception))

    @patch("sys.platform", "win32")
    def test_unsupported_os_raises_clipboard_error(self):
        with self.assertRaises(ClipboardError) as ctx:
            copy_to_clipboard("test content")
        self.assertIn("Clipboard is not supported on win32", str(ctx.exception))

    @patch("sys.platform", "darwin")
    @patch("subprocess.run", side_effect=OSError("Process spawn failure"))
    def test_process_failure_raises_clipboard_error(self, mock_run):
        with self.assertRaises(ClipboardError) as ctx:
            copy_to_clipboard("test content")
        self.assertIn("Failed to copy to clipboard", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
