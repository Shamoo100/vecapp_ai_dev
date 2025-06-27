import boto3
import aioboto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any
import logging
from app.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class S3Storage:
    """Utility for S3 storage operations with async support"""
    
    def __init__(self):
        """Initialize S3 clients for both sync and async operations"""
        # Sync client for operations that don't have async equivalents
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        # Async session for async operations
        self.session = aioboto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME
    
    async def upload_file(self, key: str, file_data: bytes, metadata: Optional[Dict[str, str]] = None) -> bool:
        """
        Upload a file to S3 asynchronously.
        
        Args:
            key: S3 object key
            file_data: File content as bytes
            metadata: Optional metadata for the S3 object
            
        Returns:
            True if upload was successful, False otherwise
        """
        try:
            async with self.session.client('s3') as s3:
                params = {
                    'Bucket': self.bucket_name,
                    'Key': key,
                    'Body': file_data
                }
                
                if metadata:
                    params['Metadata'] = metadata
                
                await s3.put_object(**params)
                
            logger.info(f"Successfully uploaded file to s3://{self.bucket_name}/{key}")
            return True
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            return False
    
    async def get_file(self, key: str) -> Optional[bytes]:
        """
        Get a file from S3 asynchronously.
        
        Args:
            key: S3 object key
            
        Returns:
            File content as bytes or None if not found
        """
        try:
            async with self.session.client('s3') as s3:
                response = await s3.get_object(
                    Bucket=self.bucket_name,
                    Key=key
                )
                return await response['Body'].read()
        except ClientError as e:
            logger.error(f"Error retrieving file from S3: {str(e)}")
            return None
    
    async def delete_file(self, key: str) -> bool:
        """
        Delete a file from S3 asynchronously.
        
        Args:
            key: S3 object key
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            async with self.session.client('s3') as s3:
                await s3.delete_object(
                    Bucket=self.bucket_name,
                    Key=key
                )
            logger.info(f"Successfully deleted file s3://{self.bucket_name}/{key}")
            return True
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {str(e)}")
            return False
    
    def get_presigned_url(self, key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for a file.
        
        Note: This method is not async because boto3's generate_presigned_url
        doesn't have an async equivalent in aioboto3.
        
        Args:
            key: S3 object key
            expiration: URL expiration time in seconds
            
        Returns:
            Presigned URL or None if generation failed
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return None