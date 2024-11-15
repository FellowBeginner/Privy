# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


import json
import os

class Document:
    def __init__(self, doc_type, path):
        self.doc_type = doc_type
        self.path = path

class Person:
    def __init__(self, name, aadhaar, pancard, voter_id, license):
        self.name = name
        self.aadhaar = aadhaar
        self.pancard = pancard
        self.voter_id = voter_id
        self.license = license
        self.documents = []

    def add_document(self, doc_type, path):
        self.documents.append(Document(doc_type, path))

    def to_dict(self):
        return {
            'name': self.name,
            'aadhaar': self.aadhaar,
            'pancard': self.pancard,
            'voter_id': self.voter_id,
            'license': self.license,
            'documents': [{'doc_type': doc.doc_type, 'path': doc.path} for doc in self.documents]
        }

    @classmethod
    def from_dict(cls, data):
        person = cls(
            data['name'],
            data['aadhaar'],
            data['pancard'],
            data['voter_id'],
            data['license']
        )
        for doc in data['documents']:
            person.add_document(doc['doc_type'], doc['path'])
        return person


# Function to add a family member
def add_family_member():
    name = input("Enter name: ")
    aadhaar = input("Enter Aadhaar number: ")
    pancard = input("Enter PAN card number: ")
    voter_id = input("Enter Voter ID: ")
    license = input("Enter Driving License number: ")

    person = Person(name, aadhaar, pancard, voter_id, license)

    while True:
        doc_type = input("Enter document type (or 'done' to finish): ")
        if doc_type.lower() == 'done':
            break
        path = input(f"Enter path to {doc_type} document: ")
        person.add_document(doc_type, path)

    family_data.append(person)


# Function to save data to a JSON file
def save_data():
    with open('family_data.json', 'w') as file:
        json.dump([person.to_dict() for person in family_data], file, indent=4)


# Function to load data from a JSON file
def load_data():
    global family_data
    if os.path.exists('family_data.json'):
        with open('family_data.json', 'r') as file:
            data = json.load(file)
            family_data = [Person.from_dict(person_data) for person_data in data]


# Function to display family members and their documents
def display_family_data():
    for person in family_data:
        print(f"Name: {person.name}")
        print(f"Aadhaar: {person.aadhaar}")
        print(f"PAN Card: {person.pancard}")
        print(f"Voter ID: {person.voter_id}")
        print(f"Driving License: {person.license}")
        print("Documents:")
        for doc in person.documents:
            print(f"  {doc.doc_type}: {doc.path}")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    family_data = []

    # Load existing data
    load_data()

    # Main loop
    while True:
        print("\nOptions:")
        print("1. Add family member")
        print("2. Save data")
        print("3. Display family data")
        print("4. Exit")
        choice = input("Enter choice: ")

        if choice == '1':
            add_family_member()
        elif choice == '2':
            save_data()
        elif choice == '3':
            display_family_data()
        elif choice == '4':
            break
        else:
            print("Invalid choice, please try again.")

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
