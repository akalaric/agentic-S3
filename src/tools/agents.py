import os
import sys
import json
import logging
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from resources.s3_resource import BucketManager
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from models.langchain_client import GeminiClient
import asyncio
# Global bucket manager initialization
_bucket_manager = None
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
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
async def list_buckets() -> str:
    """
    Lists all S3 buckets available in the AWS account.
    
    This function uses the BucketManager to fetch and return the list of buckets in JSON format, including detailed information if available.

    Returns:
        str: The list of buckets, or an error message if buckets can't be fetched.
    """
    manager = get_bucket_manager()
    response = await asyncio.to_thread(manager.list_buckets, context=True)
    return json.dumps(response, cls=CustomJSONEncoder, indent=2)

@tool
async def list_objects(bucket_name: str) -> str:
    """
    Lists objects within a specific bucket in AWS S3.
    
    This function retrieves and returns the objects stored in the specified bucket in JSON format, including detailed information if available.

    Args:
        bucket_name (str): The name of the bucket to list objects from.

    Returns:
        str: The list of objects in the specified bucket, or an error message if the objects can't be fetched.
    """
    manager = get_bucket_manager()
    response = await asyncio.to_thread(manager.list_objects, bucket_name, context=True)
    return json.dumps(response, cls=CustomJSONEncoder, indent=2)


@tool
async def upload_file(file_name: str, bucket_name: str, object_name) -> str:
    """
    Uploads a file to a specified S3 bucket in AWS.
    
    This function uploads a local file to the specified bucket using the BucketManager and returns a success or failure message.

    Args:
        file_name (str): The local file path of the file to upload.
        bucket_name (str): The name of the S3 bucket where the file will be uploaded.
        object_name (str, optional): The object name to be used in S3. If not provided, defaults to the file name.

    Returns:
        str: A message indicating success or failure of the upload operation.
    """
    manager = get_bucket_manager()
    return await asyncio.to_thread(manager.upload_file, file_name, bucket_name, object_name)

@tool
async def download_file(file_name: str, bucket_name: str) -> str:
    """
    Downloads a file from a specified S3 bucket in AWS.
    
    This function downloads the specified file from the bucket to the local system using the BucketManager and returns a success or failure message.

    Args:
        file_name (str): The name of the file to download from S3.
        bucket_name (str): The name of the bucket to download from.

    Returns:
        str: A message indicating success or failure of the download operation.
    """
    manager = get_bucket_manager()
    return await asyncio.to_thread(manager.download_file, file_name, bucket_name)

@tool
async def remove_file(file_name: str, bucket_name: str) -> str:
    """
    Removes a file from a specified S3 bucket in AWS.
    
    This function deletes the specified file from the bucket using the BucketManager and returns a success or failure message.

    Args:
        file_name (str): The name of the file to remove from S3.
        bucket_name (str): The name of the bucket to remove from.

    Returns:
        str: A message indicating success or failure of the remove operation.
    """
    manager = get_bucket_manager()
    return await asyncio.to_thread(manager.remove_file, file_name, bucket_name)

@tool
async def search_objects(search_term: str) -> str:
    """
    Searches for objects across all buckets in AWS S3 that match the provided search term.
    
    This function iterates through all buckets and searches for objects whose keys contain the specified term using the BucketManager. It returns a list of matching objects or a message indicating no matches found.

    Args:
        search_term (str): The term to search for in object keys across all buckets.

    Returns:
        str: A list of matching objects across all buckets, or a message indicating no matches.
    """
    manager = get_bucket_manager()
    return await asyncio.to_thread(manager.search_objects, search_term)

# Async function for invoking tools with Gemini
async def invoke_llm(query: str):
    """
    Processes a natural language query using the Gemini model and returns the result.
    
    This function binds the available tools to the Gemini model, processes the query, and returns the AI-generated response.
    
    Args:
        query (str): The natural language query to process
    """
    tools = [list_buckets, list_objects, upload_file, download_file, remove_file, search_objects]
    modelinstance = GeminiClient()
    #binding function schema to LLM
    llm_with_tools = modelinstance.llm.bind_tools(tools)
    
    messages = [
        SystemMessage(
            """You are an intelligent assistant capable of interacting with AWS S3 storage and engaging in natural conversations. You can perform the following tasks related to S3:
            1. **List all S3 buckets**: Provide the names, sizes, and creation dates of all the buckets in the account.
            2. **List objects in a bucket**: Given a bucket name, list all objects (files) in that bucket along with their sizes and creation dates.
            3. **Upload a file to a bucket**: Given a file and bucket name, upload the file to the specified bucket.
            4. **Download a file from a bucket**: Given a file and bucket name, download the file from the bucket to the local system.
            5. **Search for objects**: Given a search term, find objects across all buckets that match the search term.
            6. **Explain objects in the bucket**: Given a list of objects, explain the significance of each object (such as file types or potential usage).
            7. **Get object metadata**: Retrieve metadata (such as size, last-modified date, etc.) for a given object in a bucket.
            8. **Remove a file from a bucket**: Given a file and bucket name, remove the file from the specified S3 bucket.
            9. **Output data should be shown with new lines for better readability.
            In addition to these tasks, feel free to engage in a normal conversation. You can answer questions, explain concepts, or provide general information. Respond in a friendly, helpful, and informative manner to any query.
            """
        ),
        HumanMessage(query)
        ]
    # First LLM response
    ai_msg = await llm_with_tools.ainvoke(messages)
    messages.append(ai_msg)

    # If tools were called, handle tool invocations
    if ai_msg.tool_calls:
        for tool_call in ai_msg.tool_calls:
            tool_name = tool_call["name"].lower()
            tool_args = tool_call["args"]
            selected_tool = {
                "list_buckets": list_buckets,
                "list_objects": list_objects,
                "upload_file": upload_file,
                "download_file": download_file,
                "remove_file": remove_file,
                "search_objects": search_objects
            }.get(tool_name)

            if selected_tool:
                tool_output = await selected_tool.ainvoke(tool_args)
                messages.append(ToolMessage(tool_output, tool_call_id=tool_call["id"]))

        # Re-ask LLM for a final answer with tool results
        final_response = await llm_with_tools.ainvoke(messages)
        # logging.info("Final Response with Tool Call: %s", final_response.content)
        return final_response.content

    # No tools used, return initial AI message
    # logging.info("Response without tool call: %s", ai_msg.content)
    return ai_msg.content

    