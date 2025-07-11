#!/usr/bin/env python3
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def test_mongo_connection():
    try:
        # Try connecting to MongoDB Atlas with a simpler connection string
        mongo_url = "mongodb+srv://balayoutube:LoBqkfgmNWGz9KCdKfUhL16vdF7fhDbz@cluster0.wz4ng.mongodb.net/snippet_vault?retryWrites=true&w=majority"
        print(f"Testing MongoDB connection to: {mongo_url}")
        
        client = AsyncIOMotorClient(mongo_url)
        
        # Test the connection
        await client.server_info()
        print("✅ MongoDB connection successful!")
        
        # Test database access
        db = client.snippet_vault
        collections = await db.list_collection_names()
        print(f"✅ Database accessible, collections: {collections}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        
        # Try fallback to local MongoDB
        try:
            print("Trying local MongoDB connection...")
            local_client = AsyncIOMotorClient("mongodb://localhost:27017")
            await local_client.server_info()
            print("✅ Local MongoDB connection successful!")
            local_client.close()
        except Exception as e2:
            print(f"❌ Local MongoDB connection also failed: {e2}")

if __name__ == "__main__":
    asyncio.run(test_mongo_connection())