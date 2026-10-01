from pymongo import AsyncMongoClient
import os

client = AsyncMongoClient(os.getenv("MONGODB_URI"))

if not client:
    raise RuntimeError("MONGODB_URI not found in environment variables")

db = client["HydraLakes_blog_db"]

