import os
import tempfile
from pathlib import Path

from src.utils import get_latest_file_by_mask


class TestGetLatestFileByMask:
    # Returns the latest file in the directory when there is only one file matching the mask
    def test_returns_latest_file_when_only_one_matching_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.sql")
            with open(file_path, "w") as f:
                f.write("test")
            result = get_latest_file_by_mask(Path(temp_dir), "*.sql")
            assert result == Path(file_path)

    # Returns None when the directory does not exist
    def test_returns_none_when_directory_does_not_exist(self):
        result = get_latest_file_by_mask(Path("nonexistent_dir"), "*.sql")
        assert result is None

    # Returns the latest file in the directory when there are multiple files matching the mask
    def test_returns_latest_file_when_multiple_matching_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file1_path = os.path.join(temp_dir, "test1.sql")
            file2_path = os.path.join(temp_dir, "test2.sql")
            file3_path = os.path.join(temp_dir, "test3.sql")
            with open(file1_path, "w") as f:
                f.write("test")
            with open(file2_path, "w") as f:
                f.write("test")
            with open(file3_path, "w") as f:
                f.write("test")
            result = get_latest_file_by_mask(Path(temp_dir), "*.sql")
            assert result == Path(file3_path)

    def test_returns_latest_file_with_special_characters_in_file_names(self):
        """
        Returns the latest file in the directory when the file names contain special characters
        """
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with special characters in their names
            file1_path = os.path.join(temp_dir, "test!.sql")
            file2_path = os.path.join(temp_dir, "test@.sql")
            file3_path = os.path.join(temp_dir, "test#.sql")
            with open(file1_path, "w") as f:
                f.write("test")
            with open(file2_path, "w") as f:
                f.write("test")
            with open(file3_path, "w") as f:
                f.write("test")

            # Call the function under test
            result = get_latest_file_by_mask(Path(temp_dir), "*.sql")

            # Assert that the result is the expected file path
            assert result == Path(file3_path)

    # Returns None when there are no files matching the mask in the directory
    def test_returns_none_when_no_matching_files(self):
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Call the function under test
            result = get_latest_file_by_mask(Path(temp_dir), "*.sql")

            # Assert that the result is None
            assert result is None

    # Returns None when the directory is empty
    def test_returns_none_when_directory_is_empty(self):
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Call the function under test
            result = get_latest_file_by_mask(Path(temp_dir), "*.sql")

            # Assert that the result is None
            assert result is None
