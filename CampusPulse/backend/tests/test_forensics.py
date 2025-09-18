import pytest
from unittest.mock import patch, MagicMock
from app.forensics import VideoForensicsAnalyzer, analyze_video_forensics

@pytest.fixture
def forensics_analyzer():
    """Create a VideoForensicsAnalyzer instance."""
    return VideoForensicsAnalyzer()

def test_video_hash_analysis(forensics_analyzer):
    """Test video hash analysis with mocked videohash."""
    with patch('app.forensics.videohash.VideoHash') as mock_videohash:
        # Mock normal hash
        mock_videohash.return_value.__str__ = MagicMock(return_value="abc123def456")
        
        result = forensics_analyzer._video_hash_analysis("/fake/path.mp4")
        
        assert result["test_name"] == "video_hash_analysis"
        assert result["verdict"] == "authentic"
        assert result["confidence"] > 0.8
        assert "video_hash" in result["details"]

def test_video_hash_analysis_suspicious(forensics_analyzer):
    """Test video hash analysis with suspicious patterns."""
    with patch('app.forensics.videohash.VideoHash') as mock_videohash:
        # Mock suspicious hash with many zeros
        mock_videohash.return_value.__str__ = MagicMock(return_value="0000000000abc")
        
        result = forensics_analyzer._video_hash_analysis("/fake/path.mp4")
        
        assert result["verdict"] == "suspicious"
        assert result["confidence"] < 0.7
        assert result["details"]["suspicious_patterns_found"] is True

def test_metadata_analysis(forensics_analyzer):
    """Test metadata analysis with mocked ffprobe."""
    mock_metadata = {
        "format": {
            "duration": "15.5",
            "size": "2048000",
            "tags": {
                "creation_time": "2024-01-15T10:00:00Z"
            }
        }
    }
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '{"format": {"duration": "15.5", "size": "2048000", "tags": {"creation_time": "2024-01-15T10:00:00Z"}}}'
        
        result = forensics_analyzer._metadata_analysis("/fake/path.mp4")
        
        assert result["test_name"] == "metadata_analysis"
        assert result["verdict"] == "authentic"
        assert result["details"]["duration"] == 15.5

def test_metadata_analysis_suspicious(forensics_analyzer):
    """Test metadata analysis with suspicious patterns."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        # Missing creation time and unusual size ratio
        mock_run.return_value.stdout = '{"format": {"duration": "10.0", "size": "50000"}}'
        
        result = forensics_analyzer._metadata_analysis("/fake/path.mp4")
        
        assert result["verdict"] == "suspicious"
        assert "missing_creation_time" in result["details"]["flags"]
        assert "unusual_size_ratio" in result["details"]["flags"]

def test_combine_test_results(forensics_analyzer):
    """Test combining individual test results."""
    test_results = [
        {
            "test_name": "test1",
            "verdict": "authentic",
            "confidence": 0.9,
            "details": {"flags": []}
        },
        {
            "test_name": "test2", 
            "verdict": "authentic",
            "confidence": 0.8,
            "details": {"flags": []}
        },
        {
            "test_name": "test3",
            "verdict": "suspicious",
            "confidence": 0.6,
            "details": {"flags": ["suspicious_pattern"]}
        }
    ]
    
    result = forensics_analyzer._combine_test_results(test_results)
    
    assert result["overall_verdict"] == "flagged"  # Some suspicion
    assert result["confidence"] > 0.7  # Average of valid tests
    assert "suspicious_pattern" in result["flags"]
    assert result["test_summary"]["authentic_tests"] == 2
    assert result["test_summary"]["suspicious_tests"] == 1

def test_combine_test_results_mostly_suspicious(forensics_analyzer):
    """Test combining results with majority suspicious."""
    test_results = [
        {
            "test_name": "test1",
            "verdict": "suspicious",
            "confidence": 0.4,
            "details": {"flags": ["flag1"]}
        },
        {
            "test_name": "test2",
            "verdict": "suspicious", 
            "confidence": 0.5,
            "details": {"flags": ["flag2"]}
        },
        {
            "test_name": "test3",
            "verdict": "authentic",
            "confidence": 0.8,
            "details": {"flags": []}
        }
    ]
    
    result = forensics_analyzer._combine_test_results(test_results)
    
    assert result["overall_verdict"] == "suspicious"
    assert result["test_summary"]["suspicious_tests"] > result["test_summary"]["authentic_tests"]

def test_combine_test_results_with_errors(forensics_analyzer):
    """Test combining results with many errors."""
    test_results = [
        {
            "test_name": "test1",
            "verdict": "error",
            "confidence": 0.0,
            "error": "Some error"
        },
        {
            "test_name": "test2",
            "verdict": "error",
            "confidence": 0.0, 
            "error": "Another error"
        },
        {
            "test_name": "test3",
            "verdict": "authentic",
            "confidence": 0.8,
            "details": {"flags": []}
        }
    ]
    
    result = forensics_analyzer._combine_test_results(test_results)
    
    assert result["overall_verdict"] == "error"
    assert result["confidence"] == 0.0

@patch('app.forensics.requests.get')
def test_download_video_success(mock_get, forensics_analyzer):
    """Test successful video download."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.iter_content = MagicMock(return_value=[b'fake', b'video', b'data'])
    mock_get.return_value = mock_response
    
    with patch('builtins.open', create=True) as mock_open:
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        result = forensics_analyzer._download_video("http://example.com/video.mp4", "test-id")
        
        assert result is not None
        mock_get.assert_called_once()
        mock_file.write.assert_called()

@patch('app.forensics.requests.get')  
def test_download_video_failure(mock_get, forensics_analyzer):
    """Test failed video download."""
    mock_get.side_effect = Exception("Download failed")
    
    result = forensics_analyzer._download_video("http://example.com/video.mp4", "test-id")
    
    assert result is None