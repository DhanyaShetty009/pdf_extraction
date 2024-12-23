from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["school"]
collection = db["students"]

# insert_one

details = input("Enter student details (format: name, age, email, state): ")
name, age, email, state = details.split(',')
user = {"name": name.strip(), "age": age.strip(), "email": email.strip(), "state": state.strip()}
collection.insert_one(user)
print("Inserted one user:", user)

# insert_many

users = []
user_limit = 3

while len(users) < user_limit:
    details = input("Enter student details: ")
    if not details:
        break
    name, age, email, state = details.split(',')
    users.append({
        "name": name.strip(),
        "age": age.strip(),
        "email": email.strip(),
        "state": state.strip()
    })

if users:
    collection.insert_many(users)
    print("Inserted multiple users:", users)


# find

print("All users:")
for user in collection.find():
    print(user)

# find_one

name = input("Enter the name of the user to find: ")
user = collection.find_one({"name": name.strip()})
print("User found:", user)

# update_one

name = input("Enter the name of the user to update: ")
field = input("Enter the field to update (name, age, email, state): ")
new_value = input(f"Enter the new value for {field}: ")
collection.update_one({"name": name.strip()}, {"$set": {field: new_value}})
print(f"Updated {name}'s {field} to {new_value}")

# delete_one

name = input("Enter the name of the user to delete: ")
collection.delete_one({"name": name.strip()})
print(f"Deleted user with name {name}")

# drop

to_drop = input("Type 'drop' to delete the entire 'students' collection: ")
collection.drop()
print("Dropped the 'students' collection")
