import pytest
from io import BytesIO
from unittest.mock import patch, MagicMock
from app.utils.storage import StorageService, validate_video_file, validate_image_file

@pytest.fixture
def storage_service():
    """Create a StorageService instance for testing."""
    with patch.dict('os.environ', {'STORAGE_TYPE': 'local', 'LOCAL_STORAGE_PATH': '/tmp/test_storage'}):
        return StorageService()

def test_local_storage_upload(storage_service):
    """Test local file upload."""
    # Mock file data
    file_data = BytesIO(b"test file content")
    filename = "test.txt"
    
    with patch('pathlib.Path.mkdir') as mock_mkdir, \
         patch('builtins.open', create=True) as mock_open:
        
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        result = storage_service.upload_file(file_data, filename, folder="test")
        
        assert result["success"] is True
        assert "url" in result
        assert result["original_filename"] == filename
        assert result["size"] == 17  # Length of test content
        assert "hash" in result

def test_storage_service_s3_upload():
    """Test S3 file upload."""
    with patch.dict('os.environ', {'STORAGE_TYPE': 's3', 'S3_BUCKET': 'test-bucket'}), \
         patch('boto3.client') as mock_boto_client:
        
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        
        storage_service = StorageService()
        file_data = BytesIO(b"test content")
        filename = "test.mp4"
        
        result = storage_service.upload_file(file_data, filename, content_type="video/mp4")
        
        assert result["success"] is True
        mock_s3.put_object.assert_called_once()

def test_delete_file_local(storage_service):
    """Test local file deletion."""
    storage_path = "test/file.txt"
    
    with patch('pathlib.Path.exists') as mock_exists, \
         patch('pathlib.Path.unlink') as mock_unlink:
        
        mock_exists.return_value = True
        
        result = storage_service.delete_file(storage_path)
        
        assert result["success"] is True
        mock_unlink.assert_called_once()

def test_delete_file_not_exists(storage_service):
    """Test deleting non-existent file."""
    storage_path = "test/nonexistent.txt"
    
    with patch('pathlib.Path.exists') as mock_exists:
        mock_exists.return_value = False
        
        result = storage_service.delete_file(storage_path)
        
        assert result["success"] is True  # Should succeed even if file doesn't exist

def test_get_file_info_local(storage_service):
    """Test getting file info for local storage."""
    storage_path = "test/file.txt"
    
    with patch('pathlib.Path.exists') as mock_exists, \
         patch('pathlib.Path.stat') as mock_stat:
        
        mock_exists.return_value = True
        mock_stat.return_value.st_size = 1024
        mock_stat.return_value.st_mtime = 1642291200
        
        result = storage_service.get_file_info(storage_path)
        
        assert result is not None
        assert result["size"] == 1024
        assert "last_modified" in result

def test_get_file_info_not_exists(storage_service):
    """Test getting info for non-existent file."""
    storage_path = "test/nonexistent.txt"
    
    with patch('pathlib.Path.exists') as mock_exists:
        mock_exists.return_value = False
        
        result = storage_service.get_file_info(storage_path)
        
        assert result is None

def test_generate_presigned_url_local(storage_service):
    """Test generating presigned URL for local storage."""
    storage_path = "test/file.txt"
    
    result = storage_service.generate_presigned_url(storage_path)
    
    assert result == f"/storage/{storage_path}"

def test_validate_video_file_valid():
    """Test video file validation with valid file."""
    result = validate_video_file("test.mp4", 50 * 1024 * 1024)  # 50MB
    
    assert result["is_valid"] is True
    assert len(result["errors"]) == 0

def test_validate_video_file_invalid_type():
    """Test video file validation with invalid file type."""
    result = validate_video_file("test.txt", 10 * 1024 * 1024)
    
    assert result["is_valid"] is False
    assert "File type not allowed" in result["errors"][0]

def test_validate_video_file_too_large():
    """Test video file validation with file too large."""
    result = validate_video_file("test.mp4", 600 * 1024 * 1024)  # 600MB
    
    assert result["is_valid"] is False
    assert "File too large" in result["errors"][0]

def test_validate_image_file_valid():
    """Test image file validation with valid file."""
    result = validate_image_file("test.jpg", 5 * 1024 * 1024)  # 5MB
    
    assert result["is_valid"] is True
    assert len(result["errors"]) == 0

def test_validate_image_file_invalid_type():
    """Test image file validation with invalid file type."""
    result = validate_image_file("test.mp4", 5 * 1024 * 1024)
    
    assert result["is_valid"] is False
    assert "File type not allowed" in result["errors"][0]

def test_validate_image_file_too_large():
    """Test image file validation with file too large."""
    result = validate_image_file("test.jpg", 15 * 1024 * 1024)  # 15MB
    
    assert result["is_valid"] is False
    assert "File too large" in result["errors"][0]

def test_list_files_local(storage_service):
    """Test listing files in local storage."""
    with patch('pathlib.Path.exists') as mock_exists, \
         patch('pathlib.Path.is_dir') as mock_is_dir, \
         patch('pathlib.Path.rglob') as mock_rglob:
        
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        
        # Mock file paths
        mock_file1 = MagicMock()
        mock_file1.is_file.return_value = True
        mock_file1.relative_to.return_value = "test/file1.txt"
        mock_file1.stat.return_value.st_size = 1024
        mock_file1.stat.return_value.st_mtime = 1642291200
        
        mock_rglob.return_value = [mock_file1]
        
        result = storage_service.list_files("test", limit=10)
        
        assert len(result) == 1
        assert result[0]["key"] == "test/file1.txt"
        assert result[0]["size"] == 1024