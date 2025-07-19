import os
from pymongo import MongoClient
from typing import Optional, List, Dict
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import MultiModalMessage, TextMessage, ToolCallExecutionEvent, ToolCallRequestEvent, SelectSpeakerEvent, ToolCallSummaryMessage
from schemas import AutoGenMessage
import uuid
from dotenv import load_dotenv
import time
import glob
import json
from bson import ObjectId  # Import ObjectId for serialization

class MongoDB:
    def __init__(self):
        load_dotenv("./.env", override=True)
        # Get MongoDB connection details
        MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        MONGO_DATABASE = os.getenv("MONGO_DATABASE", "DyoPods_DB")
        
        self.client = MongoClient(MONGO_URI)
        self.database = self.client[MONGO_DATABASE]
        self.collections = {}
        # Pre-initialize default collections
        self.collections["DyoPods_demo"] = self.database["DyoPods_demo"]
        self.collections["DyoPods_teams"] = self.database["DyoPods_teams"]
    
    def get_collection(self, collection_name: str = "DyoPods_demo"):
        if collection_name in self.collections:
            return self.collections[collection_name]
        collection = self.database[collection_name]
        self.collections[collection_name] = collection
        return collection

    def serialize_document(self, document):
        """Convert MongoDB document to a JSON-serializable format."""
        if isinstance(document, dict):
            return {key: (str(value) if isinstance(value, ObjectId) else value) for key, value in document.items()}
        elif isinstance(document, list):
            return [self.serialize_document(item) for item in document]
        return document

    def format_message(self, _log_entry_json):
        _response = AutoGenMessage(
            time="N/A",
            session_id="session_id",
            session_user="session_user",
        )
        # ...existing code...
        if isinstance(_log_entry_json, TaskResult):
            _response.type = "TaskResult"
            _response.source = "TaskResult"
            _response.content = _log_entry_json.messages[-1].content
            _response.stop_reason = _log_entry_json.stop_reason
        elif isinstance(_log_entry_json, MultiModalMessage):
            _response.type = _log_entry_json.type
            _response.source = _log_entry_json.source
            _response.content = _log_entry_json.content[0]
            _response.content_image = _log_entry_json.content[1].data_uri
        elif isinstance(_log_entry_json, TextMessage):
            _response.type = _log_entry_json.type
            _response.source = _log_entry_json.source
            _response.content = _log_entry_json.content
            # Custom logic for Executor with base64 image
            if _log_entry_json.source == "Executor":
                import ast
                import re
                content = _log_entry_json.content
                try:
                    if isinstance(content, str) and "'type': 'image'" in content and "'base64_data':" in content:
                        pattern = r"\{[^{}]*'type': 'image'[^{}]*'base64_data':[^{}]*\}"
                        match = re.search(pattern, content)
                        if match:
                            img_dict_str = match.group(0)
                            img_dict = ast.literal_eval(img_dict_str)
                            if (
                                isinstance(img_dict, dict)
                                and img_dict.get('type') == 'image'
                                and img_dict.get('format') == 'png'
                                and 'base64_data' in img_dict
                            ):
                                _response.content_image = f"data:image/png;base64,{img_dict['base64_data']}"
                                # Remove the dict substring from the content
                                cleaned_content = content.replace(img_dict_str, "").strip()
                                _response.content = cleaned_content
                except Exception:
                    pass
        elif isinstance(_log_entry_json, ToolCallExecutionEvent):
            _response.type = _log_entry_json.type
            _response.source = _log_entry_json.source
            _response.content = _log_entry_json.content[0].content
        elif isinstance(_log_entry_json, ToolCallRequestEvent):
            _response.type = _log_entry_json.type
            _response.source = _log_entry_json.source
            _response.content = _log_entry_json.content[0].arguments
        elif isinstance(_log_entry_json, SelectSpeakerEvent):
            _response.type = _log_entry_json.type
            _response.source = _log_entry_json.source
            _response.content = _log_entry_json.content[0]
        elif isinstance(_log_entry_json, ToolCallSummaryMessage):
            _response.type = _log_entry_json.type
            _response.source = _log_entry_json.source
            _response.content = _log_entry_json.content
        else:
            _response.type = "N/A"
            _response.source = "N/A"
            _response.content = "Agents mumbling."
        return _response

    def store_conversation(self, conversation: TaskResult, conversation_details: AutoGenMessage, conversation_dict: dict):
        _messages = []
        for message in conversation.messages:
            _m = self.format_message(message)
            _messages.append(_m.to_json())
        conversation_document_item = {
            "id": str(uuid.uuid4()),
            "user_id": conversation_details.session_user,
            "session_id": conversation_details.session_id,
            "messages": _messages, 
            "agents": conversation_dict["agents"],
            "run_mode_locally": False,
            "timestamp": conversation_details.time,
        }
        collection = self.get_collection("DyoPods_demo")
        response = collection.insert_one(conversation_document_item)
        return response

    def fetch_user_conversations(self, user_id: Optional[str] = None, page: int = 1, page_size: int = 20) -> Dict:
        collection = self.get_collection("DyoPods_demo")
        
        # Query for total count
        if user_id is None:
            total_count = collection.count_documents({})
        else:
            total_count = collection.count_documents({"user_id": user_id})
        
        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        
        # Ensure page is within valid range
        page = max(1, min(page, total_pages))
        
        # Calculate skip for pagination
        skip = (page - 1) * page_size
        
        # Get paginated results
        if user_id is None:
            items = list(collection.find({}, {"user_id": 1, "session_id": 1, "timestamp": 1}).sort("timestamp", -1).skip(skip).limit(page_size))
        else:
            items = list(collection.find({"user_id": user_id}, {"user_id": 1, "session_id": 1, "timestamp": 1}).sort("timestamp", -1).skip(skip).limit(page_size))
        
        return {
            "conversations": self.serialize_document(items),
            "total_count": total_count,
            "page": page,
            "total_pages": total_pages
        }

    def fetch_user_conversation(self, user_id: str, session_id: str):
        collection = self.get_collection("DyoPods_demo")
        item = collection.find_one({"user_id": user_id, "session_id": session_id})
        return self.serialize_document(item)

    def delete_user_conversation(self, user_id: str, session_id: str):
        collection = self.get_collection("DyoPods_demo")
        result = collection.delete_one({"user_id": user_id, "session_id": session_id})
        if result.deleted_count == 0:
            return {"error": f"No conversation found with user_id {user_id} and session_id {session_id}."}
        return {"success": True}

    def delete_user_all_conversations(self, user_id: str):
        collection = self.get_collection("DyoPods_demo")
        result = collection.delete_many({"user_id": user_id})
        if result.deleted_count == 0:
            return {"error": f"No conversation found with user_id {user_id}."}
        return {"success": True}

    def create_team(self, team: dict):
        collection = self.get_collection("DyoPods_teams")
        response = collection.insert_one(team)
        return {"inserted_id": str(response.inserted_id)}

    def get_teams(self):
        collection = self.get_collection("DyoPods_teams")
        items = list(collection.find({}))
        return self.serialize_document(items)

    def get_team(self, team_id: str):
        collection = self.get_collection("DyoPods_teams")
        item = collection.find_one({"team_id": team_id})
        return self.serialize_document(item)

    def update_team(self, team_id: str, team: dict):
        collection = self.get_collection("DyoPods_teams")
        result = collection.update_one({"team_id": team_id}, {"$set": team})
        if result.matched_count == 0:
            return {"error": "Team not found"}
        return {"success": True}

    def delete_team(self, team_id: str):
        collection = self.get_collection("DyoPods_teams")
        result = collection.delete_one({"team_id": team_id})
        if result.deleted_count == 0:
            return {"error": "Team not found"}
        return {"success": True}

    def initialize_teams(self):
        teams_folder = os.path.join(os.path.dirname(__file__), "./data/teams-definitions")
        json_files = glob.glob(os.path.join(teams_folder, "*.json"))
        json_files.sort()
        print(f"Found {len(json_files)} JSON files in {teams_folder}.")
        created_items = 0
        for file_path in json_files:
            with open(file_path, "r") as f:
                team = json.load(f)
            response = self.create_team(team)
            print(f"Created team from {os.path.basename(file_path)}")
            created_items += 1
        print(f"Created {created_items}/{len(json_files)} items in the database.")
        return f"Successfully created {created_items} teams."

if __name__ == "__main__":
    db = MongoDB()
    teams_folder = os.path.join(os.path.dirname(__file__), "./data/teams-definitions")
    json_files = glob.glob(os.path.join(teams_folder, "*.json"))
    json_files.sort()
    print(f"Found {len(json_files)} JSON files in {teams_folder}.")
    created_items = 0
    for file_path in json_files:
        with open(file_path, "r") as f:
            team = json.load(f)
        response = db.create_team(team)
        print(f"Created team from {os.path.basename(file_path)}")
        created_items += 1
    print(f"Created {created_items}/{len(json_files)} items in the database.")