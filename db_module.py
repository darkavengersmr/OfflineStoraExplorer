#!/usr/bin/python3

import asyncio
import motor.motor_asyncio
import os

client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://192.168.32.64:27017')
db = client.offline_stora_explorer


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
    for document in await cursor.to_list(length=100):
        result.append(document)
    return result


async def do_update(collection, document_to_find, fields_to_update):
    result = await collection.update_one(document_to_find, fields_to_update)
    return result

async def do_delete_many(collection, documents):
    result = await collection.delete_many(documents)
    return result


async def do_list_dir_tmp(path):
    for root, dirs, files in os.walk(path):
        print(root, dirs, files)


async def do_list_dir(collection, resource, path, parent):

    if parent == 'None':
        document = {'name': resource,
                'directory': 'true',
                'size': 0,
                'parent': parent,
                'resource': resource}
        id = await do_insert_one(collection, document)
    else:
        id = parent

    all_data_size = 0

    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            file_size = os.path.getsize(os.path.join(path, file))
            document = {'name': file,
                        'directory': 'false',
                        'size': file_size,
                        'parent': id,
                        'resource': resource}
            await do_insert_one(collection, document)
            all_data_size += file_size
        else:
            dir_size = await do_list_dir(collection, resource, os.path.join(path, file), id)
            document = {'name': file,
                        'directory': 'true',
                        'size': dir_size,
                        'parent': id,
                        'resource': resource}
            await do_insert_one(collection, document)
            all_data_size += dir_size

    if parent == 'None':
        await do_update(collection, {'name': resource}, {'$set': {'size': all_data_size }})

    return all_data_size

async def test():
    await do_list_dir(db.test, "My test", "D:\\My Work", "None")




loop = asyncio.get_event_loop()
loop.run_until_complete(test())