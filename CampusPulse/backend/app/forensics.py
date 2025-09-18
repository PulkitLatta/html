import os
import cv2
import numpy as np
import hashlib
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime
import tempfile
import logging
from pathlib import Path
import videohash

# Redis and RQ imports
import redis
from rq import Worker, Queue, Connection
import requests

# Database imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Submission, ForensicsLog
from app.crud import get_submission, update_submission
from app.schemas import SubmissionUpdate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/campuspulse")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_conn = redis.from_url(REDIS_URL)
forensics_queue = Queue('forensics', connection=redis_conn)

class VideoForensicsAnalyzer:
    """Video forensics analysis for detecting manipulation and ensuring authenticity."""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "campuspulse_forensics"
        self.temp_dir.mkdir(exist_ok=True)
    
    def analyze_video(self, video_url: str, submission_id: str) -> Dict[str, Any]:
        """Perform comprehensive forensics analysis on a video."""
        logger.info(f"Starting forensics analysis for submission {submission_id}")
        
        analysis_results = {
            "submission_id": submission_id,
            "video_url": video_url,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "tests_performed": [],
            "overall_verdict": "authentic",
            "confidence": 0.0,
            "flags": []
        }
        
        try:
            # Download video
            video_path = self._download_video(video_url, submission_id)
            if not video_path:
                analysis_results["overall_verdict"] = "error"
                analysis_results["error"] = "Failed to download video"
                return analysis_results
            
            # Perform forensics tests
            tests = [
                self._video_hash_analysis,
                self._re_encoding_detection,
                self._optical_flow_analysis,
                self._histogram_variance_analysis,
                self._metadata_analysis
            ]
            
            test_results = []
            for test in tests:
                try:
                    result = test(video_path)
                    test_results.append(result)
                    analysis_results["tests_performed"].append(result["test_name"])
                except Exception as e:
                    logger.error(f"Error in forensics test: {e}")
                    test_results.append({
                        "test_name": test.__name__,
                        "verdict": "error",
                        "confidence": 0.0,
                        "error": str(e)
                    })
            
            # Combine test results to determine overall verdict
            analysis_results.update(self._combine_test_results(test_results))
            
            # Clean up temporary file
            self._cleanup_temp_file(video_path)
            
        except Exception as e:
            logger.error(f"Forensics analysis failed: {e}")
            analysis_results["overall_verdict"] = "error"
            analysis_results["error"] = str(e)
        
        return analysis_results
    
    def _download_video(self, video_url: str, submission_id: str) -> Optional[Path]:
        """Download video for analysis."""
        try:
            response = requests.get(video_url, timeout=60, stream=True)
            response.raise_for_status()
            
            video_path = self.temp_dir / f"{submission_id}_video.mp4"
            
            with open(video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return video_path
        except Exception as e:
            logger.error(f"Failed to download video: {e}")
            return None
    
    def _video_hash_analysis(self, video_path: Path) -> Dict[str, Any]:
        """Analyze video using perceptual hashing to detect duplicates or modifications."""
        try:
            # Generate video hash
            video_hash = videohash.VideoHash(path=str(video_path))
            hash_value = str(video_hash)
            
            # Check for known hash patterns that indicate manipulation
            suspicious_patterns = [
                "0" * 10,  # Too many zeros might indicate artificial content
                "f" * 10,  # Too many f's might indicate corruption
            ]
            
            is_suspicious = any(pattern in hash_value.lower() for pattern in suspicious_patterns)
            
            return {
                "test_name": "video_hash_analysis",
                "verdict": "suspicious" if is_suspicious else "authentic",
                "confidence": 0.6 if is_suspicious else 0.9,
                "details": {
                    "video_hash": hash_value,
                    "suspicious_patterns_found": is_suspicious
                }
            }
        except Exception as e:
            return {
                "test_name": "video_hash_analysis",
                "verdict": "error",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _re_encoding_detection(self, video_path: Path) -> Dict[str, Any]:
        """Detect signs of video re-encoding which might indicate manipulation."""
        try:
            # Use ffmpeg to analyze video encoding parameters
            cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", str(video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"ffprobe failed: {result.stderr}")
            
            import json
            metadata = json.loads(result.stdout)
            
            # Check for signs of re-encoding
            video_stream = None
            for stream in metadata.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break
            
            if not video_stream:
                raise Exception("No video stream found")
            
            # Analyze encoding parameters
            codec_name = video_stream.get("codec_name", "")
            bit_rate = int(video_stream.get("bit_rate", 0))
            
            # Red flags for manipulation
            flags = []
            if codec_name in ["mpeg4", "h263"]:  # Old codecs might indicate re-encoding
                flags.append("old_codec_detected")
            
            if bit_rate > 0 and bit_rate < 500000:  # Very low bitrate might indicate compression
                flags.append("low_bitrate_detected")
            
            verdict = "suspicious" if flags else "authentic"
            confidence = 0.7 if not flags else 0.4
            
            return {
                "test_name": "re_encoding_detection",
                "verdict": verdict,
                "confidence": confidence,
                "details": {
                    "codec": codec_name,
                    "bit_rate": bit_rate,
                    "flags": flags
                }
            }
        except Exception as e:
            return {
                "test_name": "re_encoding_detection", 
                "verdict": "error",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _optical_flow_analysis(self, video_path: Path) -> Dict[str, Any]:
        """Analyze optical flow to detect unnatural motion patterns."""
        try:
            cap = cv2.VideoCapture(str(video_path))
            
            # Read first frame
            ret, frame1 = cap.read()
            if not ret:
                raise Exception("Could not read video frames")
            
            prvs = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            
            flow_magnitudes = []
            frame_count = 0
            
            while frame_count < 100:  # Analyze first 100 frames
                ret, frame2 = cap.read()
                if not ret:
                    break
                
                next_frame = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
                
                # Calculate optical flow
                flow = cv2.calcOpticalFlowPyrLK(
                    prvs, next_frame, None, None,
                    winSize=(15, 15),
                    maxLevel=2,
                    criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
                )
                
                if flow[0] is not None:
                    # Calculate flow magnitude
                    magnitude = np.sqrt(flow[0][:, :, 0]**2 + flow[0][:, :, 1]**2)
                    flow_magnitudes.append(np.mean(magnitude))
                
                prvs = next_frame.copy()
                frame_count += 1
            
            cap.release()
            
            if not flow_magnitudes:
                raise Exception("No optical flow data calculated")
            
            # Analyze flow patterns
            avg_flow = np.mean(flow_magnitudes)
            flow_variance = np.var(flow_magnitudes)
            
            # Check for unnatural patterns
            is_suspicious = (
                avg_flow > 50 or  # Too much motion might indicate artificial movement
                flow_variance < 1  # Too little variance might indicate artificial content
            )
            
            verdict = "suspicious" if is_suspicious else "authentic"
            confidence = 0.6 if is_suspicious else 0.8
            
            return {
                "test_name": "optical_flow_analysis",
                "verdict": verdict,
                "confidence": confidence,
                "details": {
                    "average_flow": float(avg_flow),
                    "flow_variance": float(flow_variance),
                    "frames_analyzed": frame_count
                }
            }
        except Exception as e:
            return {
                "test_name": "optical_flow_analysis",
                "verdict": "error", 
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _histogram_variance_analysis(self, video_path: Path) -> Dict[str, Any]:
        """Analyze histogram variance to detect artificial or manipulated content."""
        try:
            cap = cv2.VideoCapture(str(video_path))
            
            histograms = []
            frame_count = 0
            
            while frame_count < 50:  # Analyze first 50 frames
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Calculate histogram for each color channel
                hist_b = cv2.calcHist([frame], [0], None, [256], [0, 256])
                hist_g = cv2.calcHist([frame], [1], None, [256], [0, 256])
                hist_r = cv2.calcHist([frame], [2], None, [256], [0, 256])
                
                # Combine histograms
                combined_hist = np.concatenate([hist_b.flatten(), hist_g.flatten(), hist_r.flatten()])
                histograms.append(combined_hist)
                
                frame_count += 1
            
            cap.release()
            
            if len(histograms) < 2:
                raise Exception("Not enough frames for histogram analysis")
            
            # Calculate variance between histograms
            variances = []
            for i in range(1, len(histograms)):
                variance = np.var(histograms[i] - histograms[i-1])
                variances.append(variance)
            
            avg_variance = np.mean(variances)
            
            # Very low variance might indicate artificial content
            is_suspicious = avg_variance < 1000
            
            verdict = "suspicious" if is_suspicious else "authentic"
            confidence = 0.7 if not is_suspicious else 0.5
            
            return {
                "test_name": "histogram_variance_analysis",
                "verdict": verdict,
                "confidence": confidence,
                "details": {
                    "average_variance": float(avg_variance),
                    "frames_analyzed": frame_count
                }
            }
        except Exception as e:
            return {
                "test_name": "histogram_variance_analysis",
                "verdict": "error",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _metadata_analysis(self, video_path: Path) -> Dict[str, Any]:
        """Analyze video metadata for signs of manipulation."""
        try:
            # Get file creation/modification times
            stat = video_path.stat()
            
            # Get video metadata
            cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", 
                   "-show_format", str(video_path)]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"ffprobe metadata failed: {result.stderr}")
            
            import json
            metadata = json.loads(result.stdout)
            
            format_info = metadata.get("format", {})
            
            # Check for suspicious metadata patterns
            flags = []
            
            # Check for missing or suspicious timestamps
            creation_time = format_info.get("tags", {}).get("creation_time")
            if not creation_time:
                flags.append("missing_creation_time")
            
            # Check file size vs duration ratio
            duration = float(format_info.get("duration", 0))
            file_size = int(format_info.get("size", 0))
            
            if duration > 0 and file_size > 0:
                size_per_second = file_size / duration
                # Very high or low ratios might indicate manipulation
                if size_per_second < 100000 or size_per_second > 10000000:
                    flags.append("unusual_size_ratio")
            
            verdict = "suspicious" if flags else "authentic"
            confidence = 0.8 if not flags else 0.4
            
            return {
                "test_name": "metadata_analysis",
                "verdict": verdict,
                "confidence": confidence,
                "details": {
                    "creation_time": creation_time,
                    "duration": duration,
                    "file_size": file_size,
                    "flags": flags
                }
            }
        except Exception as e:
            return {
                "test_name": "metadata_analysis",
                "verdict": "error",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _combine_test_results(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine individual test results into overall verdict."""
        authentic_count = 0
        suspicious_count = 0
        error_count = 0
        total_confidence = 0.0
        valid_tests = 0
        
        flags = []
        
        for result in test_results:
            verdict = result.get("verdict", "error")
            confidence = result.get("confidence", 0.0)
            
            if verdict == "authentic":
                authentic_count += 1
                total_confidence += confidence
                valid_tests += 1
            elif verdict == "suspicious":
                suspicious_count += 1
                total_confidence += confidence
                valid_tests += 1
                flags.extend(result.get("details", {}).get("flags", []))
            else:
                error_count += 1
        
        # Determine overall verdict
        if error_count > len(test_results) / 2:
            overall_verdict = "error"
            overall_confidence = 0.0
        elif suspicious_count > authentic_count:
            overall_verdict = "suspicious"
            overall_confidence = (total_confidence / valid_tests) if valid_tests > 0 else 0.0
        elif suspicious_count > 0:
            overall_verdict = "flagged"  # Some suspicion but not majority
            overall_confidence = (total_confidence / valid_tests) if valid_tests > 0 else 0.0
        else:
            overall_verdict = "authentic"
            overall_confidence = (total_confidence / valid_tests) if valid_tests > 0 else 0.0
        
        return {
            "overall_verdict": overall_verdict,
            "confidence": overall_confidence,
            "flags": list(set(flags)),
            "test_summary": {
                "authentic_tests": authentic_count,
                "suspicious_tests": suspicious_count,
                "error_tests": error_count,
                "total_tests": len(test_results)
            },
            "individual_results": test_results
        }
    
    def _cleanup_temp_file(self, file_path: Path) -> None:
        """Clean up temporary files."""
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {file_path}: {e}")

# RQ worker functions
def analyze_video_forensics(submission_id: str, video_url: str) -> None:
    """RQ worker job to analyze video forensics."""
    logger.info(f"Processing forensics analysis for submission {submission_id}")
    
    db = SessionLocal()
    try:
        # Get submission
        submission = get_submission(db, submission_id)
        if not submission:
            logger.error(f"Submission {submission_id} not found")
            return
        
        # Perform forensics analysis
        analyzer = VideoForensicsAnalyzer()
        analysis_results = analyzer.analyze_video(video_url, submission_id)
        
        # Update submission with forensics results
        forensics_data = {
            "analysis_timestamp": analysis_results["analysis_timestamp"],
            "overall_verdict": analysis_results["overall_verdict"],
            "confidence": analysis_results["confidence"],
            "flags": analysis_results["flags"],
            "test_summary": analysis_results.get("test_summary", {}),
            "tests_performed": analysis_results["tests_performed"]
        }
        
        # Determine verification status based on verdict
        verification_status = {
            "authentic": "verified",
            "suspicious": "flagged",
            "flagged": "flagged", 
            "error": "pending"
        }.get(analysis_results["overall_verdict"], "pending")
        
        # Update submission
        update_data = SubmissionUpdate(
            forensics_data=forensics_data,
            verification_status=verification_status
        )
        
        update_submission(db, submission_id, update_data)
        
        # Log forensics analysis
        forensics_log = ForensicsLog(
            submission_id=submission_id,
            analysis_type="comprehensive_video_forensics",
            verdict=analysis_results["overall_verdict"],
            confidence=analysis_results["confidence"],
            analysis_results=analysis_results,
            processing_time=0.0,  # Could track actual processing time
            algorithm_version="1.0.0"
        )
        
        db.add(forensics_log)
        db.commit()
        
        logger.info(f"Forensics analysis completed for submission {submission_id}: {analysis_results['overall_verdict']}")
        
    except Exception as e:
        logger.error(f"Forensics analysis failed for submission {submission_id}: {e}")
        db.rollback()
    finally:
        db.close()

def start_forensics_worker():
    """Start the forensics worker process."""
    listen = ['forensics']
    conn = redis.from_url(REDIS_URL)
    
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()

if __name__ == "__main__":
    # Start worker if run directly
    start_forensics_worker()