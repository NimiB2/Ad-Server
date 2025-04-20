from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

import os


load_dotenv()

DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING")
DB_NAME = os.getenv("DB_NAME")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

Mongo_URI = f"mongodb+srv://{DB_USERNAME}:{DB_PASSWORD}@{DB_CONNECTION_STRING}/{DB_NAME}"

class MongoConnectionManager:
    __db = None

    @staticmethod
    def init_db():
        """
        Initialize the database connection

        :return: MongoDB connection
        :rtype: Database
        """
        if MongoConnectionManager.__db is None:

            # Create a new client and connect to the server
            client = MongoClient(Mongo_URI, server_api=ServerApi('1'))
            # Send a ping to confirm a successful connection
            try:
                client.admin.command('ping')
                print("Pinged your deployment. You successfully connected to MongoDB!")
                MongoConnectionManager.__db = client[DB_NAME]
                
            except Exception as e:
                print(e)

        return MongoConnectionManager.__db    


    @staticmethod
    def get_db():
        """
        Get the database connection

        :return: MongoDB connection
        :rtype: Database
        """       
        if MongoConnectionManager.__db is None:
            MongoConnectionManager.init_db()

        return MongoConnectionManager.__db

