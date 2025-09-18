import os
import shutil
import hashlib
import aiofiles
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile, HTTPException
from decouple import config
import uuid

# Storage configuration
STORAGE_TYPE = config('STORAGE_TYPE', default='local')  # local, s3, gcs
UPLOAD_DIR = config('UPLOAD_DIR', default='uploads')
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Ensure upload directory exists
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

async def save_video_file(video: UploadFile) -> Tuple[str, str]:
    """
    Save uploaded video file and return URL and hash
    
    Returns:
        Tuple[str, str]: (video_url, file_hash)
    """
    
    # Validate file
    if not video.content_type or not video.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    if video.size and video.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max size: {MAX_FILE_SIZE / (1024*1024):.0f}MB")
    
    # Generate unique filename
    file_extension = Path(video.filename or 'video.mp4').suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    if STORAGE_TYPE == 'local':
        return await _save_local(video, unique_filename)
    elif STORAGE_TYPE == 's3':
        return await _save_s3(video, unique_filename)
    elif STORAGE_TYPE == 'gcs':
        return await _save_gcs(video, unique_filename)
    else:
        raise HTTPException(status_code=500, detail="Invalid storage configuration")

async def _save_local(video: UploadFile, filename: str) -> Tuple[str, str]:
    """Save file to local storage"""
    
    file_path = Path(UPLOAD_DIR) / filename
    
    # Calculate hash while saving
    hasher = hashlib.sha256()
    
    async with aiofiles.open(file_path, 'wb') as f:
        while True:
            chunk = await video.read(8192)  # 8KB chunks
            if not chunk:
                break
            hasher.update(chunk)
            await f.write(chunk)
    
    file_hash = hasher.hexdigest()
    
    # Return relative URL for local storage
    video_url = f"/uploads/{filename}"
    
    return video_url, file_hash

async def _save_s3(video: UploadFile, filename: str) -> Tuple[str, str]:
    """Save file to AWS S3"""
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        raise HTTPException(status_code=500, detail="AWS S3 dependencies not installed")
    
    s3_bucket = config('AWS_S3_BUCKET')
    s3_region = config('AWS_REGION', default='us-east-1')
    
    if not s3_bucket:
        raise HTTPException(status_code=500, detail="S3 bucket not configured")
    
    # Initialize S3 client
    s3_client = boto3.client('s3', region_name=s3_region)
    
    # Calculate hash while reading
    hasher = hashlib.sha256()
    video_content = await video.read()
    hasher.update(video_content)
    file_hash = hasher.hexdigest()
    
    try:
        # Upload to S3
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=f"videos/{filename}",
            Body=video_content,
            ContentType=video.content_type or 'video/mp4',
            ServerSideEncryption='AES256',
        )
        
        # Generate URL
        video_url = f"https://{s3_bucket}.s3.{s3_region}.amazonaws.com/videos/{filename}"
        
        return video_url, file_hash
        
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to S3: {str(e)}")

async def _save_gcs(video: UploadFile, filename: str) -> Tuple[str, str]:
    """Save file to Google Cloud Storage"""
    try:
        from google.cloud import storage
        from google.cloud.exceptions import GoogleCloudError
    except ImportError:
        raise HTTPException(status_code=500, detail="Google Cloud Storage dependencies not installed")
    
    gcs_bucket = config('GCS_BUCKET')
    
    if not gcs_bucket:
        raise HTTPException(status_code=500, detail="GCS bucket not configured")
    
    # Initialize GCS client
    client = storage.Client()
    bucket = client.bucket(gcs_bucket)
    blob = bucket.blob(f"videos/{filename}")
    
    # Calculate hash while reading
    hasher = hashlib.sha256()
    video_content = await video.read()
    hasher.update(video_content)
    file_hash = hasher.hexdigest()
    
    try:
        # Upload to GCS
        blob.upload_from_string(
            video_content,
            content_type=video.content_type or 'video/mp4'
        )
        
        # Generate URL
        video_url = f"https://storage.googleapis.com/{gcs_bucket}/videos/{filename}"
        
        return video_url, file_hash
        
    except GoogleCloudError as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to GCS: {str(e)}")

def delete_file(file_url: str) -> bool:
    """Delete a file from storage"""
    
    if STORAGE_TYPE == 'local':
        return _delete_local(file_url)
    elif STORAGE_TYPE == 's3':
        return _delete_s3(file_url)
    elif STORAGE_TYPE == 'gcs':
        return _delete_gcs(file_url)
    
    return False

def _delete_local(file_url: str) -> bool:
    """Delete file from local storage"""
    try:
        # Extract filename from URL
        filename = Path(file_url).name
        file_path = Path(UPLOAD_DIR) / filename
        
        if file_path.exists():
            file_path.unlink()
            return True
        
        return False
        
    except Exception as e:
        print(f"Error deleting local file: {e}")
        return False

def _delete_s3(file_url: str) -> bool:
    """Delete file from S3"""
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        s3_bucket = config('AWS_S3_BUCKET')
        s3_region = config('AWS_REGION', default='us-east-1')
        
        # Extract key from URL
        key = file_url.split(f"{s3_bucket}.s3.{s3_region}.amazonaws.com/")[1]
        
        s3_client = boto3.client('s3', region_name=s3_region)
        s3_client.delete_object(Bucket=s3_bucket, Key=key)
        
        return True
        
    except (ClientError, ImportError) as e:
        print(f"Error deleting S3 file: {e}")
        return False

def _delete_gcs(file_url: str) -> bool:
    """Delete file from GCS"""
    try:
        from google.cloud import storage
        from google.cloud.exceptions import GoogleCloudError
        
        gcs_bucket = config('GCS_BUCKET')
        
        # Extract blob name from URL
        blob_name = file_url.split(f"storage.googleapis.com/{gcs_bucket}/")[1]
        
        client = storage.Client()
        bucket = client.bucket(gcs_bucket)
        blob = bucket.blob(blob_name)
        blob.delete()
        
        return True
        
    except (GoogleCloudError, ImportError) as e:
        print(f"Error deleting GCS file: {e}")
        return False

def get_file_info(file_url: str) -> dict:
    """Get information about a stored file"""
    
    if STORAGE_TYPE == 'local':
        filename = Path(file_url).name
        file_path = Path(UPLOAD_DIR) / filename
        
        if file_path.exists():
            stat = file_path.stat()
            return {
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'exists': True
            }
        else:
            return {'exists': False}
    
    # For cloud storage, you'd implement similar info retrieval
    return {'exists': True}  # Simplified for demo

def cleanup_old_files(days_old: int = 30):
    """Clean up files older than specified days (local storage only)"""
    
    if STORAGE_TYPE != 'local':
        return
    
    import time
    from datetime import datetime, timedelta
    
    cutoff_time = time.time() - (days_old * 24 * 60 * 60)
    upload_path = Path(UPLOAD_DIR)
    
    if not upload_path.exists():
        return
    
    cleaned_count = 0
    for file_path in upload_path.iterdir():
        if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
            try:
                file_path.unlink()
                cleaned_count += 1
            except Exception as e:
                print(f"Error cleaning up file {file_path}: {e}")
    
    print(f"Cleaned up {cleaned_count} old files")