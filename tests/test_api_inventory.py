"""Tests for the read-only inventory / supported-types API helpers."""

import os

from peekdocs.api import (
    FileInventoryItem,
    inventory_folder,
    list_supported_file_types,
)


class TestListSupportedFileTypes:
    def test_common_types_present_and_sorted(self):
        exts = list_supported_file_types()
        assert ".pdf" in exts
        assert ".docx" in exts
        assert ".txt" in exts
        assert exts == sorted(exts)
        assert len(exts) == len(set(exts))  # no duplicates

    def test_ocr_types_excluded_by_default(self):
        assert ".png" not in list_supported_file_types()

    def test_ocr_types_included_on_request(self):
        exts = list_supported_file_types(include_ocr=True)
        assert ".png" in exts
        assert ".jpg" in exts


class TestInventoryFolder:
    def _seed(self, root):
        (root / "a.txt").write_text("hello")
        (root / "b.md").write_text("# heading")
        sub = root / "sub"
        sub.mkdir()
        (sub / "c.txt").write_text("nested")

    def test_flat_listing(self, tmp_path):
        self._seed(tmp_path)
        items = inventory_folder(str(tmp_path))
        names = {os.path.basename(it.path) for it in items}
        assert names == {"a.txt", "b.md"}  # non-recursive: no nested file
        assert all(isinstance(it, FileInventoryItem) for it in items)

    def test_recursive_listing(self, tmp_path):
        self._seed(tmp_path)
        items = inventory_folder(str(tmp_path), recursive=True)
        names = {os.path.basename(it.path) for it in items}
        assert names == {"a.txt", "b.md", "c.txt"}

    def test_file_type_filter(self, tmp_path):
        self._seed(tmp_path)
        items = inventory_folder(str(tmp_path), recursive=True, file_types=[".txt"])
        assert {os.path.basename(it.path) for it in items} == {"a.txt", "c.txt"}

    def test_fields_populated(self, tmp_path):
        (tmp_path / "a.txt").write_text("hello")
        (item,) = inventory_folder(str(tmp_path))
        assert item.size_bytes == 5
        assert item.extension == ".txt"
        assert item.modified > 0

    def test_is_read_only_no_index_written(self, tmp_path):
        self._seed(tmp_path)
        inventory_folder(str(tmp_path), recursive=True)
        assert not (tmp_path / ".peekdocs.db").exists()
