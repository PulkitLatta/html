import pytest
from unittest.mock import Mock, patch, MagicMock
from app.forensics import (
    analyze_video_authenticity,
    check_video_integrity,
    calculate_fraud_score,
    determine_authenticity_verdict
)

class TestForensics:
    
    @patch('app.forensics.SessionLocal')
    @patch('cv2.VideoCapture')
    @patch('ffmpeg.probe')
    def test_video_integrity_check(self, mock_probe, mock_cv2, mock_session):
        """Test video file integrity checking"""
        
        # Mock ffmpeg probe response
        mock_probe.return_value = {
            'format': {
                'duration': '10.5',
                'bit_rate': '1000000'
            },
            'streams': [{
                'codec_type': 'video',
                'codec_name': 'h264',
                'width': 1920,
                'height': 1080,
                'r_frame_rate': '30/1'
            }]
        }
        
        result = check_video_integrity("test_video.mp4")
        
        assert result['valid'] is True
        assert result['duration'] == 10.5
        assert result['codec'] == 'h264'
        assert result['resolution'] == '1920x1080'
        assert result['fps'] == 30.0
    
    def test_calculate_fraud_score(self):
        """Test fraud score calculation"""
        
        # Low fraud indicators
        clean_forensics = {
            'fraud_indicators': {
                'reencoding_detected': {'detected': False, 'confidence': 0.1},
                'unnatural_motion': {'unnatural_detected': False, 'confidence': 0.2}
            },
            'authenticity_indicators': {
                'frame_variance': {'healthy_variance': True, 'health_score': 0.9},
                'color_consistency': {'consistent': True, 'consistency_score': 0.95},
                'file_integrity': {'valid': True}
            }
        }
        
        score = calculate_fraud_score(clean_forensics)
        assert score < 0.2  # Should be low fraud score
        
        # High fraud indicators
        suspicious_forensics = {
            'fraud_indicators': {
                'reencoding_detected': {'detected': True, 'confidence': 0.9},
                'unnatural_motion': {'unnatural_detected': True, 'confidence': 0.8}
            },
            'authenticity_indicators': {
                'frame_variance': {'healthy_variance': False, 'health_score': 0.1},
                'color_consistency': {'consistent': False, 'consistency_score': 0.3},
                'file_integrity': {'valid': False}
            }
        }
        
        score = calculate_fraud_score(suspicious_forensics)
        assert score > 0.7  # Should be high fraud score
    
    def test_authenticity_verdict(self):
        """Test authenticity verdict determination"""
        
        # Test different fraud scores
        assert determine_authenticity_verdict(0.1, {}) == 'authentic'
        assert determine_authenticity_verdict(0.3, {}) == 'likely_authentic'
        assert determine_authenticity_verdict(0.6, {}) == 'suspicious'
        assert determine_authenticity_verdict(0.9, {}) == 'likely_fraudulent'
    
    @patch('app.forensics.SessionLocal')
    @patch('cv2.VideoCapture')
    @patch('ffmpeg.probe')
    def test_motion_analysis_mock(self, mock_probe, mock_cv2_class, mock_session):
        """Test motion pattern analysis with mocked OpenCV"""
        
        # Mock video capture
        mock_cap = Mock()
        mock_cv2_class.return_value = mock_cap
        
        # Mock frame reading
        mock_cap.read.side_effect = [
            (True, Mock()),  # First frame
            (True, Mock()),  # Second frame
            (False, None)    # End of video
        ]
        
        # Mock OpenCV functions
        with patch('cv2.cvtColor') as mock_cvt, \
             patch('cv2.goodFeaturesToTrack') as mock_features, \
             patch('cv2.calcOpticalFlowPyrLK') as mock_flow:
            
            mock_cvt.return_value = Mock()
            mock_features.return_value = [[[[100, 100]]]]  # Mock feature points
            mock_flow.return_value = (
                [[[[105, 102]]]], # next points (slight movement)
                [[1]],            # status (valid)
                [[0.1]]           # error
            )
            
            from app.forensics import analyze_motion_patterns
            result = analyze_motion_patterns("test_video.mp4")
            
            assert 'unnatural_detected' in result
            assert 'confidence' in result
    
    def test_empty_forensics_data(self):
        """Test handling of empty or missing forensics data"""
        
        # Empty forensics data
        score = calculate_fraud_score({'fraud_indicators': {}, 'authenticity_indicators': {}})
        assert score == 0.0
        
        # Missing keys
        score = calculate_fraud_score({})
        assert score == 0.0