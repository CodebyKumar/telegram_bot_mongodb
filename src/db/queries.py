"""Database query functions for MongoDB operations."""
import os
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
    """Get MongoDB collection."""
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
    """Get total teams and total members stats."""
    try:
        collection = get_mongo_collection(connection_string, database_name, collection_name)
        
        pipeline = [
            {
                "$project": {
                    "teamName": 1,
                    "memberCount": {
                        "$sum": [
                            {"$cond": [{"$ifNull": ["$member1Name", False]}, 1, 0]},
                            {"$cond": [{"$ifNull": ["$member2Name", False]}, 1, 0]},
                            {"$cond": [{"$ifNull": ["$member3Name", False]}, 1, 0]},
                            {"$cond": [{"$ifNull": ["$member4Name", False]}, 1, 0]}
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_teams": {"$sum": 1},
                    "total_members": {"$sum": "$memberCount"}
                }
            }
        ]
        
        result = list(collection.aggregate(pipeline))
        
        if result:
            return {
                "total_teams": result[0]["total_teams"],
                "total_members": result[0]["total_members"]
            }
        
        return {"total_teams": 0, "total_members": 0}

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


def get_team_transactions(connection_string, database_name, collection_name):
    """Fetch team names and their transaction IDs."""
    try:
        collection = get_mongo_collection(connection_string, database_name, collection_name)
        # Projection: only teamName and transactionId, exclude _id
        cursor = collection.find({}, {"teamName": 1, "transactionId": 1, "_id": 0})
        
        results = list(cursor)
        return results

    except Exception as e:
        print(f"Transaction fetch error: {e}")
        return None


def get_teams_with_transaction_numbers(connection_string, database_name, collection_name):
    """
    Get all team names with their transaction numbers.
    Returns a list of dicts with teamName and transactionId, sorted by teamName.
    """
    try:
        collection = get_mongo_collection(connection_string, database_name, collection_name)
        # Project only teamName and transactionId, sort by teamName
        cursor = collection.find(
            {},
            {"teamName": 1, "transactionId": 1, "_id": 0}
        ).sort("teamName", 1)
        
        results = list(cursor)
        return results

    except Exception as e:
        print(f"Error fetching teams with transaction numbers: {e}")
        return None
