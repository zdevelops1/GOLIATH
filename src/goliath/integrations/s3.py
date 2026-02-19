"""
Amazon S3 Integration — upload, download, and manage objects in S3 buckets.

Uses the standard AWS Signature Version 4 authentication via the `boto3` SDK.

SETUP INSTRUCTIONS
==================

1. Log in to the AWS Management Console at https://console.aws.amazon.com/

2. Go to IAM > Users > your user > Security credentials.

3. Click "Create access key" and copy the Access Key ID and Secret Access Key.

4. (Recommended) Create an IAM policy with least-privilege S3 access:
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject",
                  "s3:ListBucket", "s3:GetBucketLocation"],
       "Resource": ["arn:aws:s3:::your-bucket", "arn:aws:s3:::your-bucket/*"]
     }]
   }

5. Add to your .env:
     AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxxxxxx
     AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
     AWS_DEFAULT_REGION=us-east-1

   (Optional) For a specific bucket:
     AWS_S3_BUCKET=your-bucket-name

IMPORTANT NOTES
===============
- boto3 also reads credentials from ~/.aws/credentials and IAM roles.
- Regions: us-east-1, us-west-2, eu-west-1, etc. (full list in AWS docs).
- Max single PUT upload: 5 GB. This client uses multipart for files > 8 MB.
- Install the SDK: pip install boto3>=1.26.0
- API docs: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html

Usage:
    from goliath.integrations.s3 import S3Client

    s3 = S3Client()

    # List buckets
    buckets = s3.list_buckets()

    # List objects in a bucket
    objects = s3.list_objects("my-bucket", prefix="reports/")

    # Upload a file
    s3.upload_file("local/report.pdf", "my-bucket", "reports/report.pdf")

    # Download a file
    s3.download_file("my-bucket", "reports/report.pdf", "local/report.pdf")

    # Generate a presigned URL (shareable link)
    url = s3.presign("my-bucket", "reports/report.pdf", expires_in=3600)

    # Delete an object
    s3.delete_object("my-bucket", "reports/report.pdf")
"""

import boto3

from goliath import config


class S3Client:
    """Amazon S3 client for object storage operations."""

    def __init__(self):
        if not config.AWS_ACCESS_KEY_ID and not config.AWS_S3_USE_INSTANCE_PROFILE:
            raise RuntimeError(
                "AWS_ACCESS_KEY_ID is not set. "
                "Add it to .env, export as an environment variable, "
                "or configure ~/.aws/credentials. "
                "See integrations/s3.py for setup instructions."
            )

        kwargs = {}
        if config.AWS_ACCESS_KEY_ID:
            kwargs["aws_access_key_id"] = config.AWS_ACCESS_KEY_ID
        if config.AWS_SECRET_ACCESS_KEY:
            kwargs["aws_secret_access_key"] = config.AWS_SECRET_ACCESS_KEY
        if config.AWS_DEFAULT_REGION:
            kwargs["region_name"] = config.AWS_DEFAULT_REGION

        self.client = boto3.client("s3", **kwargs)
        self._default_bucket = config.AWS_S3_BUCKET

    # -- Buckets -----------------------------------------------------------

    def list_buckets(self) -> list[dict]:
        """List all accessible S3 buckets.

        Returns:
            List of bucket dicts with Name and CreationDate.
        """
        resp = self.client.list_buckets()
        return resp.get("Buckets", [])

    def create_bucket(self, bucket: str, region: str | None = None) -> dict:
        """Create a new S3 bucket.

        Args:
            bucket: Bucket name (globally unique, lowercase, 3-63 chars).
            region: AWS region (defaults to configured region).

        Returns:
            Create bucket response dict.
        """
        kwargs: dict = {"Bucket": bucket}
        region = region or config.AWS_DEFAULT_REGION
        if region and region != "us-east-1":
            kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}
        return self.client.create_bucket(**kwargs)

    # -- Objects -----------------------------------------------------------

    def list_objects(
        self,
        bucket: str | None = None,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> list[dict]:
        """List objects in a bucket.

        Args:
            bucket:   Bucket name (uses default if not specified).
            prefix:   Filter objects by key prefix (e.g. "reports/").
            max_keys: Maximum number of objects to return.

        Returns:
            List of object dicts with Key, Size, LastModified, etc.
        """
        bucket = bucket or self._default_bucket
        resp = self.client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix,
            MaxKeys=max_keys,
        )
        return resp.get("Contents", [])

    def upload_file(
        self,
        local_path: str,
        bucket: str | None = None,
        key: str | None = None,
        content_type: str | None = None,
    ) -> None:
        """Upload a local file to S3.

        Args:
            local_path:    Path to the local file.
            bucket:        Bucket name (uses default if not specified).
            key:           S3 object key (defaults to filename).
            content_type:  MIME type (auto-detected if not specified).
        """
        import os

        bucket = bucket or self._default_bucket
        key = key or os.path.basename(local_path)

        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        self.client.upload_file(local_path, bucket, key, ExtraArgs=extra_args or None)

    def upload_bytes(
        self,
        data: bytes,
        bucket: str | None = None,
        key: str = "",
        content_type: str = "application/octet-stream",
    ) -> dict:
        """Upload bytes directly to S3.

        Args:
            data:         Bytes to upload.
            bucket:       Bucket name (uses default if not specified).
            key:          S3 object key.
            content_type: MIME type.

        Returns:
            PutObject response dict.
        """
        bucket = bucket or self._default_bucket
        return self.client.put_object(
            Bucket=bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    def download_file(
        self,
        bucket: str | None = None,
        key: str = "",
        local_path: str = "",
    ) -> None:
        """Download an S3 object to a local file.

        Args:
            bucket:     Bucket name (uses default if not specified).
            key:        S3 object key.
            local_path: Local file path to save to.
        """
        bucket = bucket or self._default_bucket
        self.client.download_file(bucket, key, local_path)

    def get_object(self, bucket: str | None = None, key: str = "") -> bytes:
        """Get an S3 object's content as bytes.

        Args:
            bucket: Bucket name (uses default if not specified).
            key:    S3 object key.

        Returns:
            Object content as bytes.
        """
        bucket = bucket or self._default_bucket
        resp = self.client.get_object(Bucket=bucket, Key=key)
        return resp["Body"].read()

    def delete_object(self, bucket: str | None = None, key: str = "") -> dict:
        """Delete an object from S3.

        Args:
            bucket: Bucket name (uses default if not specified).
            key:    S3 object key.

        Returns:
            Delete response dict.
        """
        bucket = bucket or self._default_bucket
        return self.client.delete_object(Bucket=bucket, Key=key)

    def copy_object(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str | None = None,
        dest_key: str = "",
    ) -> dict:
        """Copy an object within or between buckets.

        Args:
            source_bucket: Source bucket name.
            source_key:    Source object key.
            dest_bucket:   Destination bucket (defaults to source bucket).
            dest_key:      Destination object key.

        Returns:
            Copy response dict.
        """
        dest_bucket = dest_bucket or source_bucket
        return self.client.copy_object(
            Bucket=dest_bucket,
            Key=dest_key,
            CopySource={"Bucket": source_bucket, "Key": source_key},
        )

    # -- Presigned URLs ----------------------------------------------------

    def presign(
        self,
        bucket: str | None = None,
        key: str = "",
        expires_in: int = 3600,
        method: str = "get_object",
    ) -> str:
        """Generate a presigned URL for temporary access.

        Args:
            bucket:     Bucket name (uses default if not specified).
            key:        S3 object key.
            expires_in: URL expiration time in seconds (default 1 hour).
            method:     "get_object" for download, "put_object" for upload.

        Returns:
            Presigned URL string.
        """
        bucket = bucket or self._default_bucket
        return self.client.generate_presigned_url(
            method,
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
