import os
import sys
import json
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from resources.s3_resource import BucketManager
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from models.langchain_client import GeminiClient
import asyncio
# Global bucket manager initialization
_bucket_manager = None

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat() 
        return super().default(obj)
    
    
def get_bucket_manager():
    """Initializes and returns the BucketManager instance."""
    global _bucket_manager
    if _bucket_manager is None:
        _bucket_manager = BucketManager()
    return _bucket_manager

# Define tools
@tool
def list_buckets() -> str:
    """
    Lists all S3 buckets.

    Returns:
        str: The list of buckets, or an error message if buckets can't be fetched.
    """
    manager = get_bucket_manager()
    response = manager.list_buckets(context=True)
    return json.dumps(response, cls=CustomJSONEncoder, indent=2)

@tool
def list_objects(bucket_name: str) -> str:
    """
    Lists objects within a specific bucket.

    Args:
        bucket_name (str): The name of the bucket to list objects from.

    Returns:
        str: The list of objects in the specified bucket, or an error message if the objects can't be fetched.
    """
    manager = get_bucket_manager()
    response = manager.list_objects(bucket_name, context=True)
    return json.dumps(response, cls=CustomJSONEncoder, indent=2)


@tool
def upload_file(file_name: str, bucket_name: str, object_name) -> str:
    """
    Uploads a file to a specified S3 bucket.

    Args:
        file_name (str): The local file path of the file to upload.
        bucket_name (str): The name of the S3 bucket where the file will be uploaded.
        object_name (str, optional): The object name to be used in S3. If not provided, defaults to the file name.

    Returns:
        str: A message indicating success or failure of the upload operation.
    """
    manager = get_bucket_manager()
    return manager.upload_file(file_name, bucket_name, object_name)

@tool
def download_file(file_name: str, bucket_name: str) -> str:
    """
    Downloads a file from a specified S3 bucket.

    Args:
        file_name (str): The name of the file to download from S3.
        bucket_name (str): The name of the bucket to download from.

    Returns:
        str: A message indicating success or failure of the download operation.
    """
    manager = get_bucket_manager()
    return manager.download_file(file_name, bucket_name)

@tool
def search_objects(search_term: str) -> str:
    """
    Searches for objects across all buckets that match the provided search term.

    Args:
        search_term (str): The term to search for in object keys across all buckets.

    Returns:
        str: A list of matching objects across all buckets, or a message indicating no matches.
    """
    manager = get_bucket_manager()
    return manager.search_objects(search_term)

# Async function for invoking tools with Gemini
async def invoke_llm(query: str):
    """
    Takes a query, invokes it using the Gemini model, and prints the result.
    
    Args:
        query (str): The natural language query to process
    """
    tools = [list_buckets, list_objects, upload_file, download_file, search_objects]
    modelinstance = GeminiClient()
    #binding function schema to LLM
    llm_with_tools = modelinstance.llm.bind_tools(tools)
    
    messages = [
        SystemMessage(
            """You are an intelligent assistant capable of interacting with AWS S3 storage. You can perform the following tasks related to S3:
                1. **List all S3 buckets**: Provide the names, size and creation dates of all the buckets in the account.
                2. **List objects in a bucket**: Given a bucket name, list all objects (files) in that bucket along with their sizes and creation dates.
                3. **Upload a file to a bucket**: Given a file and bucket name, upload the file to the specified bucket.
                4. **Download a file from a bucket**: Given a file and bucket name, download the file from the bucket to the local system.
                5. **Search for objects**: Given a search term, find objects across all buckets that match the search term.
                6. **Explain objects in the bucket**: Given a list of objects, explain the significance of each object (such as file types or potential usage).
                8. **Get object metadata**: Retrieve metadata (such as size, last-modified date, etc.) for a given object in a bucket.
            """
            ),
        HumanMessage(query)
        ]
    ai_msg = await llm_with_tools.ainvoke(messages)
    messages.append(ai_msg)
    for tool_call in ai_msg.tool_calls:
        selected_tool = {"list_buckets": list_buckets, "list_objects": list_objects, "upload_file": upload_file, "download_file": download_file, "search_objects": search_objects}[tool_call["name"].lower()]
        #asking LLM to generate function call with arguments
        tool_output = selected_tool.invoke(tool_call["args"])
        messages.append(ToolMessage(tool_output, tool_call_id=tool_call["id"]))

    # finally prompting LLM with custom function schema and all required arguments
    response = await llm_with_tools.ainvoke(messages)
    return response.content