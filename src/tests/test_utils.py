import tempfile
from pathlib import Path

import pytest

from src.utils import get_latest_file


@pytest.fixture
def temp_dir() -> Path:
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


class TestGetLatestFileByMask:
    def test_returns_latest_file_when_only_one_matching_file(self, temp_dir):
        file_path = temp_dir / "test.sql"
        file_path.touch()
        result = get_latest_file("test-db", temp_dir, "*.sql")
        assert result == file_path

    def test_returns_none_when_directory_does_not_exist(self):
        result = get_latest_file("test-db", Path("nonexistent_dir"), "*.sql")
        assert result is None

    def test_returns_latest_file_when_multiple_matching_files(self, temp_dir):
        file1_path = temp_dir / "test1.sql"
        file2_path = temp_dir / "test2.sql"
        file3_path = temp_dir / "test3.sql"
        file1_path.touch()
        file2_path.touch()
        file3_path.touch()

        result = get_latest_file("test-db", temp_dir, "*.sql")
        assert result == file3_path

    def test_returns_latest_file_with_special_characters_in_file_names(self, temp_dir):
        file1_path = temp_dir / "test!.sql"
        file2_path = temp_dir / "test@.sql"
        file3_path = temp_dir / "test#.sql"
        file1_path.touch()
        file2_path.touch()
        file3_path.touch()

        result = get_latest_file("test-db", temp_dir, "*.sql")
        assert result == file3_path

    def test_returns_none_when_no_matching_files(self, temp_dir):
        result = get_latest_file("test-db", temp_dir, "*.sql")
        assert result is None

    # Returns None when the directory is empty
    def test_returns_none_when_directory_is_empty(self, temp_dir):
        result = get_latest_file("test-db", temp_dir, "*.sql")
        assert result is None
