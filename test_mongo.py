from pymongo import MongoClient

# Replace with your Atlas connection string


MONGO_URI = "mongodb+srv://npranavan28_db_user:s1JVOVB6pfY5XR2B@@cluster0.mongodb.net/product_db?retryWrites=true&w=majority/product_db?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)
db = client["product_db"]
collection = db["products"]

# Test insert
collection.insert_one({"name": "Test Product", "price": 100})

# Test fetch
for doc in collection.find():
    print(doc)
