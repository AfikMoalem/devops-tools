"""
Pytest tests for s3_component_replacer.py
"""

import json
import os
import tempfile
from unittest.mock import MagicMock
import pytest
from botocore.exceptions import ClientError

from src.s3_component_replacer import (
    construct_file_name,
    construct_paths,
    copy_component_file,
    extract_version,
    find_component_mapping,
    load_component_mappings,
    load_component_names,
)


class TestExtractVersion:
    """Tests for extract_version function"""

    def test_extract_version_single_digit(self):
        """Test extracting single digit version"""
        assert extract_version("Component-D-4") == "4"

    def test_extract_version_two_digits(self):
        """Test extracting two digit version"""
        assert extract_version("Component-A-V1-19") == "19"
        assert extract_version("Component-C-V2-22") == "22"
        assert extract_version("Component-E-57") == "57"

    def test_extract_version_three_digits(self):
        """Test extracting three digit version"""
        assert extract_version("Component-B-227") == "227"
        assert extract_version("Component-F-202") == "202"
        assert extract_version("Component-G-179") == "179"
        assert extract_version("Component-H-259") == "259"
        assert extract_version("Component-I-146") == "146"

    def test_extract_version_with_multiple_numbers(self):
        """Test extracting version when component name has multiple numbers"""
        assert extract_version("Component-A-V1-19") == "19"
        assert extract_version("Component-J-03.12.2025") == "2025"

    def test_extract_version_no_version_raises_error(self):
        """Test that ValueError is raised when no version found"""
        with pytest.raises(ValueError, match="No version number found"):
            extract_version("Component-A-V1")


class TestConstructFileName:
    """Tests for construct_file_name function"""

    def test_construct_file_name_basic(self):
        """Test basic file name construction"""
        assert (
            construct_file_name(
                "krembo.{version}.min.js", "19") == "krembo.19.min.js"
        )

    def test_construct_file_name_different_patterns(self):
        """Test various file name patterns"""
        assert (
            construct_file_name("component-b.{version}.min.js", "227")
            == "component-b.227.min.js"
        )
        assert (
            construct_file_name("component-f.{version}.min.js", "202")
            == "component-f.202.min.js"
        )
        assert (
            construct_file_name("component-j.{version}.min.js", "2025")
            == "component-j.2025.min.js"
        )

    def test_construct_file_name_multiple_placeholders(self):
        """Test file name with multiple version placeholders"""
        result = construct_file_name("app.{version}.{version}.min.js", "19")
        assert result == "app.19.19.min.js"


class TestConstructPaths:
    """Tests for construct_paths function"""

    def test_construct_paths_basic(self):
        """Test basic path construction"""
        dev_path, stage_path = construct_paths("components/component-a/")
        assert dev_path == "dev/components/component-a/"
        assert stage_path == "stage/components/component-a/"

    def test_construct_paths_without_trailing_slash(self):
        """Test path construction adds trailing slash if missing"""
        dev_path, stage_path = construct_paths("components/component-a")
        assert dev_path == "dev/components/component-a/"
        assert stage_path == "stage/components/component-a/"

    def test_construct_paths_strips_dev_prefix(self):
        """Test that dev/ prefix is stripped"""
        dev_path, stage_path = construct_paths("dev/components/component-a/")
        assert dev_path == "dev/components/component-a/"
        assert stage_path == "stage/components/component-a/"

    def test_construct_paths_strips_stage_prefix(self):
        """Test that stage/ prefix is stripped"""
        dev_path, stage_path = construct_paths("stage/components/component-a/")
        assert dev_path == "dev/components/component-a/"
        assert stage_path == "stage/components/component-a/"

    def test_construct_paths_strips_leading_slash(self):
        """Test that leading slash is stripped"""
        dev_path, stage_path = construct_paths("/components/component-a/")
        assert dev_path == "dev/components/component-a/"
        assert stage_path == "stage/components/component-a/"

    def test_construct_paths_empty_path(self):
        """Test path construction with empty path"""
        dev_path, stage_path = construct_paths("")
        assert dev_path == "dev/"
        assert stage_path == "stage/"


class TestFindComponentMapping:
    """Tests for find_component_mapping function"""

    def test_find_component_mapping_exact_match(self):
        """Test finding exact component key match"""
        mappings = {
            "Component-A-V1": {
                "path_format": "/components/component-a/component-a.{0}.min.js",
            },
            "Component-B": {
                "path_format": "/components/component-b/component-b.{0}.min.js",
            },
        }
        result = find_component_mapping("Component-A-V1-19", mappings)
        assert result == mappings["Component-A-V1"]

    def test_find_component_mapping_best_match(self):
        """Test that longest (most specific) match is returned"""
        mappings = {
            "Component-A": {
                "path_format": "/components/component-a/component-a.{0}.min.js",
            },
            "Component-A-V1": {
                "path_format": "/components/component-a-v1/component-a-v1.{0}.min.js",
            },
        }
        result = find_component_mapping("Component-A-V1-19", mappings)
        # Should return the longer, more specific match
        assert result == mappings["Component-A-V1"]

    def test_find_component_mapping_no_match(self):
        """Test that None is returned when no match found"""
        mappings = {
            "Component-A-V1": {
                "path_format": "/components/component-a/component-a.{0}.min.js",
            }
        }
        result = find_component_mapping("Component-Unknown-123", mappings)
        assert result is None

    def test_find_component_mapping_multiple_matches(self):
        """Test best match when multiple keys could match"""
        mappings = {
            "Component": {
                "path_format": "/components/component.{0}.min.js",
            },
            "Component-B": {
                "path_format": "/components/component-b/component-b.{0}.min.js",
            },
            "Component-B-Wrapper": {
                "path_format": "/components/component-b-wrapper/component-b-wrapper.{0}.min.js",
            },
        }
        result = find_component_mapping("Component-B-Wrapper-227", mappings)
        # Should return the longest match
        assert result == mappings["Component-B-Wrapper"]


class TestLoadComponentMappings:
    """Tests for load_component_mappings function"""

    def test_load_component_mappings_valid_file(self):
        """Test loading valid mappings file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                [
                    {
                        "component_key": "Component-A-V1",
                        "path_format": "/components/component-a/component-a.{0}.min.js",
                    },
                    {
                        "component_key": "Component-B",
                        "path_format": "/components/component-b/component-b.{0}.min.js",
                    },
                ],
                f,
            )
            temp_path = f.name

        try:
            result = load_component_mappings(temp_path)
            assert len(result) == 2
            assert "Component-A-V1" in result
            assert "Component-B" in result
            assert (
                result["Component-A-V1"]["path_format"]
                == "/components/component-a/component-a.{0}.min.js"
            )
        finally:
            os.unlink(temp_path)

    def test_load_component_mappings_missing_file(self):
        """Test loading non-existent file returns empty dict"""
        result = load_component_mappings("/nonexistent/file.json")
        assert result == {}

    def test_load_component_mappings_invalid_json(self):
        """Test loading invalid JSON returns empty dict"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content {")
            temp_path = f.name

        try:
            result = load_component_mappings(temp_path)
            assert result == {}
        finally:
            os.unlink(temp_path)

    def test_load_component_mappings_missing_component_key(self):
        """Test that missing component_key raises ValueError"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                [{"path_format": "/test/test.{0}.min.js"}], f
            )
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="component_key"):
                load_component_mappings(temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_component_mappings_missing_path_format(self):
        """Test that missing path_format raises ValueError"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                [{"component_key": "Component-A"}], f
            )
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="path_format"):
                load_component_mappings(temp_path)
        finally:
            os.unlink(temp_path)


class TestLoadComponentNames:
    """Tests for load_component_names function"""

    def test_load_component_names_valid_file(self):
        """Test loading valid component names file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                ["Component-A-V1-19", "Component-B-227", "Component-F-202"], f)
            temp_path = f.name

        try:
            result = load_component_names(temp_path)
            assert len(result) == 3
            assert "Component-A-V1-19" in result
            assert "Component-B-227" in result
            assert "Component-F-202" in result
        finally:
            os.unlink(temp_path)

    def test_load_component_names_missing_file(self):
        """Test loading non-existent file returns empty list"""
        result = load_component_names("/nonexistent/file.json")
        assert result == []

    def test_load_component_names_invalid_json(self):
        """Test loading invalid JSON returns empty list"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content [")
            temp_path = f.name

        try:
            result = load_component_names(temp_path)
            assert result == []
        finally:
            os.unlink(temp_path)


class TestCopyComponentFile:
    """Tests for copy_component_file function"""

    @pytest.fixture
    def mock_s3_client(self):
        """Create a mock S3 client"""
        return MagicMock()

    @pytest.fixture
    def component_config(self):
        """Sample component configuration"""
        return {
            "path_format": "/components/component-a/component-a.{0}.min.js",
        }

    def test_copy_component_file_success(self, mock_s3_client, component_config):
        """Test successful file copy"""
        # Mock S3 head_object calls (file exists in both source and destination)
        mock_s3_client.head_object.return_value = {}

        result = copy_component_file(
            "Component-A-V1-19",
            component_config,
            "test-bucket",
            mock_s3_client,
            dry_run=False,
        )

        assert result is True
        # Verify copy_object was called
        mock_s3_client.copy_object.assert_called_once()

    def test_copy_component_file_dry_run(self, mock_s3_client, component_config):
        """Test dry run mode doesn't actually copy"""
        # Mock S3 head_object calls
        mock_s3_client.head_object.return_value = {}

        result = copy_component_file(
            "Component-A-V1-19",
            component_config,
            "test-bucket",
            mock_s3_client,
            dry_run=True,
        )

        assert result is True
        # Verify copy_object was NOT called in dry run
        mock_s3_client.copy_object.assert_not_called()

    def test_copy_component_file_source_not_found(
        self, mock_s3_client, component_config
    ):
        """Test handling when source file doesn't exist"""
        # Mock 404 error for source file
        error_response = {"Error": {"Code": "404", "Message": "Not Found"}}
        mock_s3_client.head_object.side_effect = ClientError(
            error_response, "HeadObject"
        )

        result = copy_component_file(
            "Component-A-V1-19",
            component_config,
            "test-bucket",
            mock_s3_client,
            dry_run=False,
        )

        assert result is False
        mock_s3_client.copy_object.assert_not_called()

    def test_copy_component_file_permission_denied(
        self, mock_s3_client, component_config
    ):
        """Test handling permission denied error"""
        # Mock 403 error
        error_response = {"Error": {"Code": "403", "Message": "Forbidden"}}
        mock_s3_client.head_object.side_effect = ClientError(
            error_response, "HeadObject"
        )

        result = copy_component_file(
            "Component-A-V1-19",
            component_config,
            "test-bucket",
            mock_s3_client,
            dry_run=False,
        )

        assert result is False

    def test_copy_component_file_destination_not_found(
        self, mock_s3_client, component_config
    ):
        """Test handling when destination file doesn't exist (should still copy)"""

        # First call (source) succeeds, second call (destination) returns 404
        def side_effect(*args, **kwargs):
            if mock_s3_client.head_object.call_count == 1:
                return {}  # Source exists
            else:
                error_response = {
                    "Error": {"Code": "404", "Message": "Not Found"}}
                raise ClientError(error_response, "HeadObject")

        mock_s3_client.head_object.side_effect = side_effect

        result = copy_component_file(
            "Component-A-V1-19",
            component_config,
            "test-bucket",
            mock_s3_client,
            dry_run=False,
        )

        assert result is True
        mock_s3_client.copy_object.assert_called_once()

    def test_copy_component_file_missing_config_field(self, mock_s3_client):
        """Test handling missing required config field"""
        incomplete_config = {}  # Missing 'path_format' field

        result = copy_component_file(
            "Component-A-V1-19",
            incomplete_config,
            "test-bucket",
            mock_s3_client,
            dry_run=False,
        )

        assert result is False

    def test_copy_component_file_invalid_version(
        self, mock_s3_client, component_config
    ):
        """Test handling component name with no version"""
        result = copy_component_file(
            "Component-A-V1",  # No version number
            component_config,
            "test-bucket",
            mock_s3_client,
            dry_run=False,
        )

        assert result is False
