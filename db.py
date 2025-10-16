from pymongo import MongoClient

# Connect to local MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["product_db"]
collection = db["products"]

# Insert a new product
def insert_product(data):
    return collection.insert_one(data)

# Get all products
def get_all_products():
    return list(collection.find())

# Delete a row by product_code
def delete_product(product_code):
    return collection.delete_one({"product_code": product_code})

# Update product by product_code
def update_product(product_code, update_data):
    return collection.update_one({"product_code": product_code}, {"$set": update_data})

# Delete a column (field) from all documents
def delete_column(column_name):
    return collection.update_many({}, {"$unset": {column_name: ""}})
