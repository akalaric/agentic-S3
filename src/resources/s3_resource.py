import os
import re
import logging
import boto3
from botocore.exceptions import ClientError
from typing import List, Optional
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

class BucketManager:
    def __init__(self):
        """
        Initializes the BucketManager instance, setting up the S3 client using AWS credentials
        from environment variables.
        """
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        if not aws_access_key_id or not aws_secret_access_key:
            raise Exception("AWS Environment Variables not set")

        self.config = Config(
            retries=dict(max_attempts=3, mode="adaptive"),
            connect_timeout=5,
            read_timeout=60,
            max_pool_connections=50,
        )

        self.client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            config=self.config,
        )

    def list_buckets(self, context=False) -> str:
        """
        Lists all S3 buckets available in the AWS account.
        
        This method fetches the list of buckets using the AWS S3 client and returns their names and creation dates. If the context parameter is set to True, detailed information is returned.

        Args:
            context (bool, optional): If True, returns detailed information. Defaults to False.

        Returns:
            str: The list of buckets, or an error message if buckets can't be fetched.
        """
        try:
            response = self.client.list_buckets()
            buckets = response.get("Buckets", [])
            if buckets:
                bucket_list = "\n".join(
                    [
                        f"Bucket Name: {bucket['Name']}, Created on: {bucket['CreationDate']}"
                        for bucket in buckets
                    ]
                )
                return response if context else bucket_list
            else:
                return "No buckets found."
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logging.error(f"Failed to list buckets - Code: {error_code}, Message: {error_message}")
            return f"Failed to list buckets - Code: {error_code}, Message: {error_message}"

    def list_objects(
        self, bucket_name: str, max_keys: int = 1000, context=False
    ) -> str:
        """
        Lists objects within a specific bucket in AWS S3.
        
        This method retrieves the objects stored in the specified bucket, including their keys and sizes. The max_keys parameter limits the number of objects returned, and the context parameter provides detailed information if set to True.

        Args:
            bucket_name (str): The name of the bucket to list objects from.
            max_keys (int, optional): The maximum number of keys to return. Defaults to 1000.
            context (bool, optional): If True, returns detailed information including size. Defaults to False.

        Returns:
            str: The list of objects in the specified bucket, or an error message if the objects can't be fetched.
        """
        try:
            response = self.client.list_objects_v2(Bucket=bucket_name, MaxKeys=max_keys)
            objects = response.get("Contents", [])
            if objects:
                return (
                    objects
                    if context
                    else "\n".join(
                        [
                            f"Object Key: {obj['Key']}, Size {obj['Size']/1e+6} MB"
                            for obj in objects
                        ]
                    )
                )
            else:
                return f"No objects found in bucket {bucket_name}."
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logging.error(f"Failed to list objects in {bucket_name} - Code: {error_code}, Message: {error_message}")
            return f"Failed to list objects in {bucket_name} - Code: {error_code}, Message: {error_message}"

    def upload_file(
        self, file_name: str, bucket_name: str, object_name: Optional[str] = None
    ) -> str:
        """
        Uploads a file to a specified S3 bucket in AWS.
        
        This method uploads a local file to the specified bucket, using the provided object name or defaulting to the file name. It returns a success message or an error message if the upload fails.

        Args:
            file_name (str): The local file path of the file to upload.
            bucket_name (str): The name of the S3 bucket where the file will be uploaded.
            object_name (str, optional): The object name to be used in S3. If not provided, defaults to the file name.

        Returns:
            str: A message indicating success or failure of the upload operation.
        """
        if object_name is None:
            object_name = os.path.basename(file_name)
        try:
            self.client.upload_file(file_name, bucket_name, object_name)
            return f"File {file_name} uploaded to bucket {bucket_name} as {object_name}"
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logging.error(f"Failed to upload file {file_name} - Code: {error_code}, Message: {error_message}")
            return f"Failed to upload file {file_name} - Code: {error_code}, Message: {error_message}"

    def remove_file(self, file_name: str, bucket_name: str) -> str:
        """
        Removes a file from a specified S3 bucket in AWS.
        
        This method deletes the specified file from the bucket and returns a success message or an error message if the removal fails.

        Args:
            file_name (str): The name of the file to remove from S3.
            bucket_name (str): The name of the bucket to remove from.

        Returns:
            str: A message indicating success or failure of the remove operation.
        """
        try:
            self.client.delete_object(Bucket=bucket_name, Key=file_name)
            return f"File {file_name} removed from bucket {bucket_name}"
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logging.error(f"Failed to remove file {file_name} - Code: {error_code}, Message: {error_message}")
            return f"Failed to remove file {file_name} - Code: {error_code}, Message: {error_message}"
        
        
    def download_file(self, file_name: str, bucket_name: str) -> str:
        """
        Downloads a file from a specified S3 bucket in AWS.
        
        This method downloads the specified file from the bucket to the local system and returns a success message or an error message if the download fails.

        Args:
            file_name (str): The name of the file to download from S3.
            bucket_name (str): The name of the bucket to download from.

        Returns:
            str: A message indicating success or failure of the download operation.
        """
        try:
            self.client.download_file(bucket_name, file_name, file_name)
            return f"File {file_name} downloaded from bucket {bucket_name}"
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logging.error(f"Failed to download file {file_name} - Code: {error_code}, Message: {error_message}")
            return f"Failed to download file {file_name} - Code: {error_code}, Message: {error_message}"

    def search_objects(self, search_term: str) -> List[str]:
        """
        Searches for objects across all buckets in AWS S3 that match the provided search term.
        
        This method iterates through all buckets and searches for objects whose keys contain the specified term. It returns a list of matching objects or a message indicating no matches found.

        Args:
            search_term (str): The term to search for in object keys across all buckets.

        Returns:
            List[str]: A list of matching objects across all buckets, or a message indicating no matches.
        """
        search_results = []
        buckets = self.list_buckets()

        if not buckets:
            return "No buckets found."
        bucket_names = re.findall(r"Bucket Name:\s*(\w+)", str(buckets))

        for name in bucket_names:
            try:
                response = self.client.list_objects_v2(Bucket=name)
                for obj in response.get("Contents", []):
                    if search_term.lower() in obj["Key"].lower():
                        search_results.append(f"Bucket: {name}, Object: {obj['Key']} ")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                logging.error(f"Failed to list objects in bucket {name} - Code: {error_code}, Message: {error_message}")
                print(f"Failed to list objects in bucket {name} - Code: {error_code}, Message: {error_message}")

        if search_results:
            return "\n".join(search_results)
        else:
            return f"No objects found matching '{search_term}'"


if __name__ == "__main__":
    s3_bucket = BucketManager()

    logging.info(s3_bucket.list_buckets())
    # logging.info(s3_bucket.list_objects('my_bucket'))
    # s3_bucket.upload_file('requirements.txt', 'my_bucket')
