"""
Video forensics analysis worker using RQ (Redis Queue)
Performs video authenticity verification and fraud detection
"""

import os
import cv2
import numpy as np
import ffmpeg
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from rq import Worker, Queue, Connection
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from decouple import config

from app.models import Submission
from app.utils.storage import get_file_info

# Configuration
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379')
DATABASE_URL = config('DATABASE_URL', default='postgresql://user:password@localhost/campuspulse')

# Initialize Redis connection
redis_conn = redis.from_url(REDIS_URL)
forensics_queue = Queue('forensics', connection=redis_conn)

# Initialize database
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def queue_forensics_analysis(submission_id: str, video_path: str):
    """Queue a forensics analysis job"""
    job = forensics_queue.enqueue(
        analyze_video_authenticity,
        submission_id,
        video_path,
        job_timeout='10m'  # 10 minute timeout
    )
    print(f"Queued forensics analysis for submission {submission_id}: {job.id}")
    return job.id

def analyze_video_authenticity(submission_id: str, video_path: str) -> Dict[str, Any]:
    """
    Main forensics analysis function
    Performs various authenticity checks on the submitted video
    """
    
    db = SessionLocal()
    
    try:
        # Get submission from database
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            raise Exception(f"Submission {submission_id} not found")
        
        # Update status to processing
        submission.forensics_status = 'processing'
        db.commit()
        
        print(f"Starting forensics analysis for submission {submission_id}")
        
        # Initialize results
        forensics_data = {
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'video_path': video_path,
            'checks_performed': [],
            'authenticity_indicators': {},
            'fraud_indicators': {},
            'overall_verdict': 'pending'
        }
        
        # 1. Video file integrity check
        integrity_result = check_video_integrity(video_path)
        forensics_data['checks_performed'].append('integrity_check')
        forensics_data['authenticity_indicators']['file_integrity'] = integrity_result
        
        # 2. Re-encoding detection (detects if video was edited/processed)
        reencoding_result = detect_reencoding(video_path)
        forensics_data['checks_performed'].append('reencoding_detection')
        forensics_data['fraud_indicators']['reencoding_detected'] = reencoding_result
        
        # 3. Motion analysis (detects unnatural movements)
        motion_result = analyze_motion_patterns(video_path)
        forensics_data['checks_performed'].append('motion_analysis')
        forensics_data['fraud_indicators']['unnatural_motion'] = motion_result
        
        # 4. Frame variance analysis (detects static/repeated frames)
        variance_result = analyze_frame_variance(video_path)
        forensics_data['checks_performed'].append('variance_analysis')
        forensics_data['authenticity_indicators']['frame_variance'] = variance_result
        
        # 5. Histogram analysis (detects color/lighting inconsistencies)
        histogram_result = analyze_color_histogram(video_path)
        forensics_data['checks_performed'].append('histogram_analysis')
        forensics_data['authenticity_indicators']['color_consistency'] = histogram_result
        
        # 6. Calculate overall fraud score
        fraud_score = calculate_fraud_score(forensics_data)
        
        # 7. Determine verdict
        verdict = determine_authenticity_verdict(fraud_score, forensics_data)
        forensics_data['overall_verdict'] = verdict
        
        # Update submission with results
        submission.forensics_data = forensics_data
        submission.fraud_score = fraud_score
        submission.is_verified = (verdict == 'authentic')
        submission.forensics_status = 'completed'
        submission.processed_at = datetime.utcnow()
        
        db.commit()
        
        print(f"Forensics analysis completed for submission {submission_id}. Fraud score: {fraud_score:.3f}, Verdict: {verdict}")
        
        return forensics_data
        
    except Exception as e:
        print(f"Error in forensics analysis for submission {submission_id}: {str(e)}")
        
        # Update submission with error
        if submission:
            submission.forensics_status = 'failed'
            submission.forensics_data = {
                'error': str(e),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            db.commit()
        
        raise e
        
    finally:
        db.close()

def check_video_integrity(video_path: str) -> Dict[str, Any]:
    """Check if video file is valid and not corrupted"""
    
    try:
        # Use ffmpeg to probe video information
        probe = ffmpeg.probe(video_path)
        
        video_info = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        
        if not video_info:
            return {'valid': False, 'error': 'No video stream found'}
        
        return {
            'valid': True,
            'duration': float(probe['format']['duration']),
            'codec': video_info['codec_name'],
            'resolution': f"{video_info['width']}x{video_info['height']}",
            'fps': eval(video_info['r_frame_rate']),
            'bitrate': int(probe['format'].get('bit_rate', 0))
        }
        
    except Exception as e:
        return {'valid': False, 'error': str(e)}

def detect_reencoding(video_path: str) -> Dict[str, Any]:
    """Detect if video has been re-encoded (potential tampering indicator)"""
    
    try:
        # Analyze compression artifacts and encoding signatures
        cap = cv2.VideoCapture(video_path)
        
        frames_analyzed = 0
        total_block_artifacts = 0
        total_ringing_artifacts = 0
        
        while frames_analyzed < 30:  # Analyze first 30 frames
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect block artifacts (common in re-encoded videos)
            block_artifacts = detect_block_artifacts(gray)
            total_block_artifacts += block_artifacts
            
            # Detect ringing artifacts
            ringing_artifacts = detect_ringing_artifacts(gray)
            total_ringing_artifacts += ringing_artifacts
            
            frames_analyzed += 1
        
        cap.release()
        
        if frames_analyzed == 0:
            return {'detected': False, 'confidence': 0.0, 'error': 'No frames analyzed'}
        
        avg_block_artifacts = total_block_artifacts / frames_analyzed
        avg_ringing_artifacts = total_ringing_artifacts / frames_analyzed
        
        # High artifact levels suggest re-encoding
        reencoding_confidence = min(1.0, (avg_block_artifacts + avg_ringing_artifacts) / 100.0)
        
        return {
            'detected': reencoding_confidence > 0.6,
            'confidence': reencoding_confidence,
            'avg_block_artifacts': avg_block_artifacts,
            'avg_ringing_artifacts': avg_ringing_artifacts
        }
        
    except Exception as e:
        return {'detected': False, 'confidence': 0.0, 'error': str(e)}

def analyze_motion_patterns(video_path: str) -> Dict[str, Any]:
    """Analyze motion patterns to detect unnatural movements"""
    
    try:
        cap = cv2.VideoCapture(video_path)
        
        # Initialize optical flow detector
        lk_params = dict(
            winSize=(15, 15),
            maxLevel=2,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
        )
        
        # Take first frame and detect features
        ret, prev_frame = cap.read()
        if not ret:
            return {'unnatural_detected': False, 'error': 'Could not read first frame'}
        
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        prev_pts = cv2.goodFeaturesToTrack(prev_gray, maxCorners=100, qualityLevel=0.3, minDistance=7, blockSize=7)
        
        motion_vectors = []
        frame_count = 0
        
        while frame_count < 100:  # Analyze up to 100 frames
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_pts is not None:
                # Calculate optical flow
                next_pts, status, error = cv2.calcOpticalFlowPyrLK(prev_gray, frame_gray, prev_pts, None, **lk_params)
                
                # Select good points
                good_new = next_pts[status == 1]
                good_old = prev_pts[status == 1]
                
                # Calculate motion vectors
                if len(good_new) > 0:
                    vectors = good_new - good_old
                    motion_vectors.extend(vectors)
                
                # Update previous frame and points
                prev_gray = frame_gray.copy()
                prev_pts = good_new.reshape(-1, 1, 2)
            
            frame_count += 1
        
        cap.release()
        
        if not motion_vectors:
            return {'unnatural_detected': False, 'confidence': 0.0}
        
        # Analyze motion vector characteristics
        motion_vectors = np.array(motion_vectors)
        
        # Calculate motion statistics
        mean_magnitude = np.mean(np.linalg.norm(motion_vectors, axis=1))
        std_magnitude = np.std(np.linalg.norm(motion_vectors, axis=1))
        
        # Detect unnatural patterns (e.g., too uniform, too erratic)
        uniformity_score = std_magnitude / (mean_magnitude + 1e-6)  # Avoid division by zero
        
        # Very low or very high uniformity can indicate manipulation
        unnatural_confidence = 0.0
        if uniformity_score < 0.1 or uniformity_score > 5.0:
            unnatural_confidence = min(1.0, abs(uniformity_score - 1.0) / 2.0)
        
        return {
            'unnatural_detected': unnatural_confidence > 0.7,
            'confidence': unnatural_confidence,
            'mean_motion_magnitude': float(mean_magnitude),
            'motion_uniformity': float(uniformity_score),
            'total_vectors_analyzed': len(motion_vectors)
        }
        
    except Exception as e:
        return {'unnatural_detected': False, 'confidence': 0.0, 'error': str(e)}

def analyze_frame_variance(video_path: str) -> Dict[str, Any]:
    """Analyze frame-to-frame variance to detect static or repeated content"""
    
    try:
        cap = cv2.VideoCapture(video_path)
        
        prev_frame = None
        variances = []
        frame_count = 0
        
        while frame_count < 200:  # Analyze up to 200 frames
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_frame is not None:
                # Calculate frame difference
                diff = cv2.absdiff(prev_frame, gray)
                variance = np.var(diff)
                variances.append(variance)
            
            prev_frame = gray.copy()
            frame_count += 1
        
        cap.release()
        
        if not variances:
            return {'healthy_variance': False, 'error': 'No variance data collected'}
        
        mean_variance = np.mean(variances)
        std_variance = np.std(variances)
        
        # Low variance indicates static content (potential fraud)
        # High variance indicates natural movement
        variance_health_score = min(1.0, mean_variance / 1000.0)  # Normalize
        
        return {
            'healthy_variance': variance_health_score > 0.3,
            'mean_variance': float(mean_variance),
            'variance_consistency': float(std_variance),
            'health_score': float(variance_health_score),
            'frames_analyzed': len(variances)
        }
        
    except Exception as e:
        return {'healthy_variance': False, 'error': str(e)}

def analyze_color_histogram(video_path: str) -> Dict[str, Any]:
    """Analyze color distribution consistency across frames"""
    
    try:
        cap = cv2.VideoCapture(video_path)
        
        histograms = []
        frame_count = 0
        
        while frame_count < 50:  # Sample 50 frames
            ret, frame = cap.read()
            if not ret:
                break
            
            # Calculate histogram for each channel
            hist_b = cv2.calcHist([frame], [0], None, [256], [0, 256])
            hist_g = cv2.calcHist([frame], [1], None, [256], [0, 256])
            hist_r = cv2.calcHist([frame], [2], None, [256], [0, 256])
            
            # Combine histograms
            combined_hist = np.concatenate([hist_b.flatten(), hist_g.flatten(), hist_r.flatten()])
            histograms.append(combined_hist)
            
            frame_count += 1
        
        cap.release()
        
        if len(histograms) < 2:
            return {'consistent': False, 'error': 'Insufficient frames for analysis'}
        
        # Calculate histogram consistency
        consistencies = []
        for i in range(1, len(histograms)):
            correlation = cv2.compareHist(histograms[i-1], histograms[i], cv2.HISTCMP_CORREL)
            consistencies.append(correlation)
        
        mean_consistency = np.mean(consistencies)
        
        return {
            'consistent': mean_consistency > 0.7,
            'consistency_score': float(mean_consistency),
            'frames_analyzed': len(histograms)
        }
        
    except Exception as e:
        return {'consistent': False, 'error': str(e)}

def detect_block_artifacts(gray_frame):
    """Detect JPEG/MPEG compression block artifacts"""
    # Simplified block artifact detection
    # In practice, you'd use more sophisticated methods
    edges = cv2.Canny(gray_frame, 50, 150)
    return np.sum(edges) / (gray_frame.shape[0] * gray_frame.shape[1])

def detect_ringing_artifacts(gray_frame):
    """Detect ringing artifacts from compression"""
    # Apply high-pass filter to detect ringing
    kernel = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])
    filtered = cv2.filter2D(gray_frame, -1, kernel)
    return np.std(filtered)

def calculate_fraud_score(forensics_data: Dict[str, Any]) -> float:
    """Calculate overall fraud score from forensics analysis"""
    
    score = 0.0
    weight_sum = 0.0
    
    # Reencoding detection (weight: 0.3)
    if 'reencoding_detected' in forensics_data['fraud_indicators']:
        reencoding = forensics_data['fraud_indicators']['reencoding_detected']
        if reencoding.get('detected', False):
            score += reencoding.get('confidence', 0.0) * 0.3
        weight_sum += 0.3
    
    # Motion analysis (weight: 0.25)
    if 'unnatural_motion' in forensics_data['fraud_indicators']:
        motion = forensics_data['fraud_indicators']['unnatural_motion']
        if motion.get('unnatural_detected', False):
            score += motion.get('confidence', 0.0) * 0.25
        weight_sum += 0.25
    
    # Frame variance (weight: 0.2)
    if 'frame_variance' in forensics_data['authenticity_indicators']:
        variance = forensics_data['authenticity_indicators']['frame_variance']
        if not variance.get('healthy_variance', True):
            score += (1.0 - variance.get('health_score', 1.0)) * 0.2
        weight_sum += 0.2
    
    # Color consistency (weight: 0.15)
    if 'color_consistency' in forensics_data['authenticity_indicators']:
        color = forensics_data['authenticity_indicators']['color_consistency']
        if not color.get('consistent', True):
            score += (1.0 - color.get('consistency_score', 1.0)) * 0.15
        weight_sum += 0.15
    
    # File integrity (weight: 0.1)
    if 'file_integrity' in forensics_data['authenticity_indicators']:
        integrity = forensics_data['authenticity_indicators']['file_integrity']
        if not integrity.get('valid', True):
            score += 1.0 * 0.1
        weight_sum += 0.1
    
    # Normalize score
    if weight_sum > 0:
        score = score / weight_sum
    
    return min(1.0, max(0.0, score))

def determine_authenticity_verdict(fraud_score: float, forensics_data: Dict[str, Any]) -> str:
    """Determine overall authenticity verdict"""
    
    if fraud_score < 0.2:
        return 'authentic'
    elif fraud_score < 0.5:
        return 'likely_authentic'
    elif fraud_score < 0.8:
        return 'suspicious'
    else:
        return 'likely_fraudulent'

def start_forensics_worker():
    """Start the forensics analysis worker"""
    with Connection(redis_conn):
        worker = Worker([forensics_queue])
        print("Starting forensics analysis worker...")
        worker.work()

if __name__ == '__main__':
    start_forensics_worker()