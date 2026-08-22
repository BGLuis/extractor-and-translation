import os
import subprocess
from src.utils.ClipboardUtils import get_clipboard_folder, get_clipboard_text


def test_get_clipboard_folder_with_valid_dir(monkeypatch, tmp_path):
    monkeypatch.setattr("src.utils.ClipboardUtils.get_clipboard_text", lambda: str(tmp_path))
    assert get_clipboard_folder() == str(tmp_path)


def test_get_clipboard_folder_with_quotes(monkeypatch, tmp_path):
    monkeypatch.setattr("src.utils.ClipboardUtils.get_clipboard_text", lambda: f'"{tmp_path}"')
    assert get_clipboard_folder() == str(tmp_path)


def test_get_clipboard_folder_with_file_uri(monkeypatch, tmp_path):
    monkeypatch.setattr("src.utils.ClipboardUtils.get_clipboard_text", lambda: f"file://{tmp_path}")
    assert get_clipboard_folder() == str(tmp_path)


def test_get_clipboard_folder_with_invalid_text(monkeypatch):
    monkeypatch.setattr("src.utils.ClipboardUtils.get_clipboard_text", lambda: "invalid_path_xyz_123")
    assert get_clipboard_folder() is None


def test_get_clipboard_folder_when_clipboard_empty(monkeypatch):
    monkeypatch.setattr("src.utils.ClipboardUtils.get_clipboard_text", lambda: None)
    assert get_clipboard_folder() is None


def test_get_clipboard_folder_with_multiline_clipboard(monkeypatch, tmp_path):
    monkeypatch.setattr("src.utils.ClipboardUtils.get_clipboard_text", lambda: f"{tmp_path}\nother text")
    assert get_clipboard_folder() == str(tmp_path)
