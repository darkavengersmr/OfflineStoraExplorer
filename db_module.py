#!/usr/bin/python3

import os, datetime
from bson.objectid import ObjectId

import asyncio
import motor.motor_asyncio


async def do_insert_one(collection, document):
    result = await collection.insert_one(document)
    return result.inserted_id


async def do_insert_many(collection, documents):
    result = await collection.insert_many(documents)
    return result.inserted_ids


async def do_find_one(collection, document):
    return await collection.find_one(document)


async def do_find(collection, document):
    cursor = collection.find(document)
    result = []
    for document in await cursor.to_list(length=100000):
        result.append(document)
    return result


async def do_update(collection, document_to_find, fields_to_update):
    result = await collection.update_one(document_to_find, fields_to_update)
    return result

async def do_delete_many(collection, documents):
    result = await collection.delete_many(documents)
    return result


async def do_list_dir(collection, resource, path, parent):

    def file_modification_date(filename):
        t = os.path.getmtime(filename)
        dt = datetime.datetime.fromtimestamp(t)
        result = str(dt.strftime('%d.%m.%Y %H:%M'))
        return result

    if parent == 'None':
        resource_date = str(datetime.datetime.now().strftime('%d.%m.%Y %H:%M'))
        document = {'name': resource,
                'directory': 'true',
                'size': 'unknown',
                'date': resource_date,
                'parent': parent,
                'resource': resource}
        id = await do_insert_one(collection, document)
        id = str(id)
    else:
        id = parent

    all_data_size = 0
    documents = []

    for file in os.listdir(path):
        file_date = file_modification_date(os.path.join(path, file))
        if os.path.isfile(os.path.join(path, file)):
            file_size = os.path.getsize(os.path.join(path, file))
            document = {'name': file,
                        'directory': 'false',
                        'size': file_size,
                        'date': file_date,
                        'parent': id,
                        'resource': resource}
            documents.append(document)
            all_data_size += file_size
        else:
            document = {'name': file,
                        'directory': 'true',
                        'size': 'unknown',
                        'date': file_date,
                        'parent': id,
                        'resource': resource}
            parent_id = await do_insert_one(collection, document)
            parent_id = str(parent_id)
            dir_size = await do_list_dir(collection, resource, os.path.join(path, file), parent_id)
            await do_update(collection, {'_id': ObjectId(parent_id)}, {'$set': {'size': dir_size}})
            all_data_size += dir_size
    if len(documents) > 0:
        await do_insert_many(collection, documents)
    if parent == 'None':
        await do_update(collection, {'_id': ObjectId(id)}, {'$set': {'size': all_data_size }})
    return all_data_size


async def get_list_dir(collection, parent):
    document = {'parent': parent}
    result = await do_find(collection, document)
    for obj in result:
        obj['_id'] = str(obj['_id'])
    return result


async def do_search(collection, search_string):
    result = await do_find(collection, {'name': {'$regex': search_string}})
    for obj in result:
        obj['_id'] = str(obj['_id'])
    return result


async def test():
    db_client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://192.168.32.64:27017',
                                                       io_loop=asyncio.get_event_loop())
    db = db_client.offline_stora_explorer
    offline_stora_explorer_collection = db.test

    result = await do_search(offline_stora_explorer_collection, "CS50")
    print(result)


#loop = asyncio.get_event_loop()
#loop.run_until_complete(test())