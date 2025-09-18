import os
import boto3
import hashlib
import mimetypes
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Storage configuration
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")  # local, s3, gcs
LOCAL_STORAGE_PATH = os.getenv("LOCAL_STORAGE_PATH", "./storage")
S3_BUCKET = os.getenv("S3_BUCKET")
S3_REGION = os.getenv("S3_REGION", "us-west-2")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

class StorageService:
    """Unified storage service supporting local and cloud storage."""
    
    def __init__(self):
        self.storage_type = STORAGE_TYPE
        
        if self.storage_type == "s3":
            self.s3_client = boto3.client(
                's3',
                region_name=S3_REGION,
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY
            )
        elif self.storage_type == "local":
            # Ensure local storage directory exists
            Path(LOCAL_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
    
    def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        content_type: Optional[str] = None,
        folder: str = "uploads"
    ) -> Dict[str, Any]:
        """Upload file to configured storage backend."""
        
        # Generate unique filename
        file_extension = Path(filename).suffix
        unique_filename = f"{uuid4()}{file_extension}"
        storage_path = f"{folder}/{unique_filename}"
        
        # Determine content type
        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
            if not content_type:
                content_type = "application/octet-stream"
        
        # Read file data
        file_data.seek(0)
        file_content = file_data.read()
        file_size = len(file_content)
        
        # Calculate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        try:
            if self.storage_type == "s3":
                url = self._upload_to_s3(storage_path, file_content, content_type)
            else:
                url = self._upload_to_local(storage_path, file_content)
            
            return {
                "success": True,
                "url": url,
                "filename": unique_filename,
                "original_filename": filename,
                "storage_path": storage_path,
                "size": file_size,
                "content_type": content_type,
                "hash": file_hash,
                "uploaded_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }
    
    def _upload_to_s3(self, storage_path: str, file_content: bytes, content_type: str) -> str:
        """Upload file to S3."""
        self.s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=storage_path,
            Body=file_content,
            ContentType=content_type,
            ServerSideEncryption='AES256'
        )
        
        # Return public URL or signed URL based on bucket configuration
        return f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{storage_path}"
    
    def _upload_to_local(self, storage_path: str, file_content: bytes) -> str:
        """Upload file to local storage."""
        full_path = Path(LOCAL_STORAGE_PATH) / storage_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "wb") as f:
            f.write(file_content)
        
        # Return local URL path
        return f"/storage/{storage_path}"
    
    def delete_file(self, storage_path: str) -> Dict[str, Any]:
        """Delete file from storage."""
        try:
            if self.storage_type == "s3":
                self.s3_client.delete_object(Bucket=S3_BUCKET, Key=storage_path)
            else:
                full_path = Path(LOCAL_STORAGE_PATH) / storage_path
                if full_path.exists():
                    full_path.unlink()
            
            return {"success": True, "deleted_path": storage_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_presigned_url(
        self,
        storage_path: str,
        expiration: int = 3600,
        method: str = "GET"
    ) -> Optional[str]:
        """Generate presigned URL for file access."""
        if self.storage_type == "s3":
            try:
                url = self.s3_client.generate_presigned_url(
                    method.upper() == "GET" and 'get_object' or 'put_object',
                    Params={'Bucket': S3_BUCKET, 'Key': storage_path},
                    ExpiresIn=expiration
                )
                return url
            except Exception as e:
                return None
        else:
            # For local storage, just return the file path
            # In production, you might want to implement signed URLs for local files too
            return f"/storage/{storage_path}"
    
    def get_file_info(self, storage_path: str) -> Optional[Dict[str, Any]]:
        """Get file metadata."""
        try:
            if self.storage_type == "s3":
                response = self.s3_client.head_object(Bucket=S3_BUCKET, Key=storage_path)
                return {
                    "size": response['ContentLength'],
                    "content_type": response['ContentType'],
                    "last_modified": response['LastModified'].isoformat(),
                    "etag": response['ETag']
                }
            else:
                full_path = Path(LOCAL_STORAGE_PATH) / storage_path
                if full_path.exists():
                    stat = full_path.stat()
                    content_type, _ = mimetypes.guess_type(str(full_path))
                    return {
                        "size": stat.st_size,
                        "content_type": content_type or "application/octet-stream",
                        "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "path": str(full_path)
                    }
                return None
        except Exception:
            return None
    
    def list_files(self, folder: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """List files in a folder."""
        files = []
        
        try:
            if self.storage_type == "s3":
                response = self.s3_client.list_objects_v2(
                    Bucket=S3_BUCKET,
                    Prefix=folder,
                    MaxKeys=limit
                )
                
                for obj in response.get('Contents', []):
                    files.append({
                        "key": obj['Key'],
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        "etag": obj['ETag']
                    })
            else:
                folder_path = Path(LOCAL_STORAGE_PATH) / folder
                if folder_path.exists() and folder_path.is_dir():
                    for file_path in folder_path.rglob("*"):
                        if file_path.is_file():
                            relative_path = file_path.relative_to(Path(LOCAL_STORAGE_PATH))
                            stat = file_path.stat()
                            files.append({
                                "key": str(relative_path),
                                "size": stat.st_size,
                                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                "path": str(file_path)
                            })
                            
                            if len(files) >= limit:
                                break
        except Exception as e:
            pass  # Return empty list on error
        
        return files[:limit]

# File validation utilities
def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
    """Validate file type against allowed types."""
    file_extension = Path(filename).suffix.lower()
    return file_extension in [ext.lower() for ext in allowed_types]

def validate_file_size(file_size: int, max_size_mb: int = 100) -> bool:
    """Validate file size."""
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes

def validate_video_file(filename: str, file_size: int) -> Dict[str, Any]:
    """Validate video file for uploads."""
    allowed_video_types = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
    max_size_mb = 500  # 500MB max for videos
    
    validation = {
        "is_valid": True,
        "errors": []
    }
    
    if not validate_file_type(filename, allowed_video_types):
        validation["is_valid"] = False
        validation["errors"].append(f"File type not allowed. Allowed types: {', '.join(allowed_video_types)}")
    
    if not validate_file_size(file_size, max_size_mb):
        validation["is_valid"] = False
        validation["errors"].append(f"File too large. Maximum size: {max_size_mb}MB")
    
    return validation

def validate_image_file(filename: str, file_size: int) -> Dict[str, Any]:
    """Validate image file for uploads."""
    allowed_image_types = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    max_size_mb = 10  # 10MB max for images
    
    validation = {
        "is_valid": True,
        "errors": []
    }
    
    if not validate_file_type(filename, allowed_image_types):
        validation["is_valid"] = False
        validation["errors"].append(f"File type not allowed. Allowed types: {', '.join(allowed_image_types)}")
    
    if not validate_file_size(file_size, max_size_mb):
        validation["is_valid"] = False
        validation["errors"].append(f"File too large. Maximum size: {max_size_mb}MB")
    
    return validation

# Cleanup utilities
def cleanup_old_files(days_old: int = 30) -> Dict[str, Any]:
    """Clean up files older than specified days."""
    if STORAGE_TYPE != "local":
        return {"message": "Cleanup only supported for local storage"}
    
    cutoff_time = datetime.now() - timedelta(days=days_old)
    deleted_count = 0
    deleted_size = 0
    
    try:
        for file_path in Path(LOCAL_STORAGE_PATH).rglob("*"):
            if file_path.is_file():
                stat = file_path.stat()
                if datetime.fromtimestamp(stat.st_mtime) < cutoff_time:
                    deleted_size += stat.st_size
                    file_path.unlink()
                    deleted_count += 1
    except Exception as e:
        return {"error": str(e)}
    
    return {
        "deleted_files": deleted_count,
        "deleted_size_mb": round(deleted_size / (1024 * 1024), 2),
        "cutoff_date": cutoff_time.isoformat()
    }

# Create global storage service instance
storage_service = StorageService()