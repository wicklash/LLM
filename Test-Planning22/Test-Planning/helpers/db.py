from pymongo import MongoClient
import gridfs

client = MongoClient("mongodb://localhost:27017/")
db = client["test_planner"]
fs = gridfs.GridFS(db)