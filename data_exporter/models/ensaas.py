import logging

from flask import current_app
from pymongo import MongoClient
from mongo_proxy import MongoProxy


class MongoDB(object):
    def __init__(self):
        mongoClient = MongoProxy(
            MongoClient(
                current_app.config["EKS_009_HOST"],
                username=current_app.config["EKS_009_USERNAME"],
                password=current_app.config["EKS_009_PASSWORD"],
                authSource=current_app.config["EKS_009_DATABASE"],
                # authMechanism="SCRAM-SHA-1",
            )
        )
        self.DATABASE = mongoClient[current_app.config["EKS_009_DATABASE"]]

    def getOne(self, database, dictRequest):
        mCollection = self.DATABASE[database]
        mDocument = mCollection.find_one(dictRequest)
        return mDocument

    def getMany(self, database, pipeline):
        mCollection = self.DATABASE[database]
        mDocument = mCollection.aggregate(pipeline)
        return list(mDocument)

    def insertOne(self, database, document):
        mCollection = self.DATABASE[database]
        mCollection.insert_one(document)

    def insertMany(self, database, document):
        mCollection = self.DATABASE[database]
        mCollection.insertMany(document)

    def updateOne(self, database, myquery, newvalues):
        mCollection = self.DATABASE[database]
        mCollection.update_one(myquery, newvalues)

    def upsertOne(self, database, myquery, newvalues):
        mCollection = self.DATABASE[database]
        mCollection.update_one(myquery, newvalues, upsert=True)

    def deleteMany(self, database, document):
        mCollection = self.DATABASE[database]
        mCollection.delete_many(document)

    def getanddeleteOne(self, database, dictRequest):
        mCollection = self.DATABASE[database]
        mDocument = mCollection.find_one_and_delete(dictRequest)
        return mDocument

    def deleteDATABASE(self, database):
        mCollection = self.DATABASE[database]
        mCollection.delete_many({})
