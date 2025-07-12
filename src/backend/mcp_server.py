# mcp_server.py

import os
import json
import logging
import inspect
from fastmcp import FastMCP
from azure.communication.email import EmailClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mcp_server")

# Create an instance of FastMCP
mcp = FastMCP("MagenticMCP")

# === TOOL: Send Email via Azure Communication Services ===
@mcp.tool()
def mailer(to_address: str, subject: str, plain_text: str = "", html_content: str = "") -> str:
    logger.info(f"Calling mailer(to_address={to_address}, subject={subject})")
    endpoint = os.environ.get("AZURE_COMMUNICATION_EMAIL_ENDPOINT")
    sender_address = os.environ.get("AZURE_COMMUNICATION_EMAIL_SENDER")
    if not endpoint or not sender_address:
        return f"Missing config: endpoint={endpoint}, sender={sender_address}"
    
    if not to_address:
        to_address = os.getenv("AZURE_COMMUNICATION_EMAIL_RECIPIENT_DEFAULT", "")
    if not subject:
        subject = os.getenv("AZURE_COMMUNICATION_EMAIL_SUBJECT_DEFAULT", "No Subject")

    try:
        client = EmailClient(endpoint, DefaultAzureCredential())
        message = {
            "senderAddress": sender_address,
            "recipients": { "to": [ { "address": to_address } ] },
            "content": {
                "subject": subject,
                "plainText": plain_text,
                "html": html_content or f"<html><body><pre>{plain_text}</pre></body></html>"
            }
        }
        poller = client.begin_send(message)
        _ = poller.result()
        return f"Email successfully sent to {to_address}."
    except Exception as e:
        logger.error(f"Mailer error: {e}")
        return f"Mailer failed: {e}"

# === TOOL: Add Two Integers ===
@mcp.tool(name="add", description="Add two integers")
def add(a: int, b: int) -> int:
    logger.info(f"Calling add(a={a}, b={b})")
    print(f"Calling add(a={a}, b={b})")  # Ensures visibility during dev
    return a + b

# === TOOL: Multiply Two Integers ===
@mcp.tool(name="multiply", description="multiply two integers")
def multiply(a: int, b: int) -> int:
    logger.info(f"Calling multiply(a={a}, b={b})")
    return a * b

# === TOOL: File-based Table Data Provider ===
@mcp.tool(name="dataprovider", description="Load tabular data from a CSV file")
def data_provider(tablename: str) -> str:
    """
    Loads tabular data from a CSV file based on the given table name.
    Expects files in ./data subdirectory.
    Returns the file contents as a string.
    This is useful for MCP tool schema generation, as it returns the raw CSV content as a string.
    """
    logger.info(f"Calling data_provider(tablename={tablename})")
    filename = f"{tablename.strip()}.csv"
    file_path = find_file(filename)
    if not file_path:
        return f"File '{filename}' not found."
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return f"Failed to read file: {e}"

# === Helper ===
def find_file(filename: str) -> str:
    for root, _, files in os.walk("./data"):
        if filename in files:
            return os.path.join(root, filename)
    return None

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")  # stdio or sse
    logger.info(f"Starting MCP server with transport: {transport}")
    logger.info(f"Loaded {len(mcp.list_tools())} tools:")
    for tool in mcp.list_tools():
        logger.info(f"- {tool.name}")

    if transport == "stdio":
        try:
            input_json = input()
            request = json.loads(input_json)
            tool_name = request["tool"]
            args = request.get("args", {})

            tool = next((t for t in mcp.list_tools() if t.name == tool_name), None)
            if tool is None:
                print(json.dumps({"error": f"Tool '{tool_name}' not found"}))
            else:
                sig = inspect.signature(tool.fn)
                kwargs = {k: v for k, v in args.items() if k in sig.parameters}
                result = tool.fn(**kwargs)
                print(json.dumps({"result": result}))
        except Exception as e:
            print(json.dumps({"error": str(e)}))
    else:
        mcp.run(transport=transport)