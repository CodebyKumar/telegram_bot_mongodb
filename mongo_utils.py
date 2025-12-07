import pandas as pd
from pymongo import MongoClient
import certifi
import re

_client = None


def get_mongo_client(connection_string):
    """Create or reuse global MongoDB client (connection pooling)."""
    global _client
    if _client is None:
        _client = MongoClient(connection_string, tlsCAFile=certifi.where())
    return _client


def get_mongo_collection(connection_string, database_name, collection_name):
    client = get_mongo_client(connection_string)
    db = client.get_database(database_name)
    return db.get_collection(collection_name)


def export_mongo_collection_to_csv(connection_string, database_name, collection_name, output_file="registrations.csv"):
    """Export entire collection into a CSV file."""
    try:
        collection = get_mongo_collection(connection_string, database_name, collection_name)
        data = list(collection.find({}))

        if not data:
            print("No documents found.")
            return None

        df = pd.DataFrame(data)

        # Remove MongoDB ObjectId for CSV
        if "_id" in df.columns:
            df.drop(columns=["_id"], inplace=True)

        df.to_csv(output_file, index=False)
        return output_file

    except Exception as e:
        print(f"CSV export error: {e}")
        return None


def get_stats(connection_string, database_name, collection_name):
    """Count total documents in the collection."""
    try:
        collection = get_mongo_collection(connection_string, database_name, collection_name)
        total = collection.count_documents({})
        return {"total_teams": total}
    except Exception as e:
        print(f"Stats error: {e}")
        return None


def find_team_by_name(connection_string, database_name, collection_name, team_name):
    """Case-insensitive safe match using regex."""
    try:
        if not team_name:
            return None

        collection = get_mongo_collection(connection_string, database_name, collection_name)
        safe_name = re.escape(team_name.strip())

        query = {"teamName": {"$regex": f"^{safe_name}$", "$options": "i"}}
        result = collection.find_one(query)

        return result

    except Exception as e:
        print(f"Find error: {e}")
        return None
