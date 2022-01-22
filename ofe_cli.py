#!/usr/bin/python3

import sys
import argparse

import asyncio
import motor.motor_asyncio

from db_module import do_list_dir, do_delete_many

db_socket = "192.168.32.64:27017"

loop = asyncio.get_event_loop()

db_client = motor.motor_asyncio.AsyncIOMotorClient(f'mongodb://{db_socket}', io_loop=asyncio.get_event_loop())
db = db_client.offline_stora_explorer
offline_stora_explorer_collection = db.test


def createParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--add', default=None)
    parser.add_argument ('-u', '--update', default=None)
    parser.add_argument('-d', '--delete', default=None)
    parser.add_argument('-c', '--clear', default=None)
    parser.add_argument('-p', '--path', default=None)
    return parser

parser = createParser()
namespace = parser.parse_args(sys.argv[1:])

if namespace.add is None and namespace.update is None and namespace.delete is None and namespace.clear is None:
    print('Please specify operation (add/update/delete/clear db) or see help (-h)')
    sys.exit()

if namespace.path is None and (namespace.add is not None or namespace.update is not None):
    print('Please specify full path or see help (-h)')
    sys.exit()

if namespace.clear is not None:
    answer = input("Really clean DB? (y/n): ")
    if answer == "y" or answer == "Y":
        loop.run_until_complete(do_delete_many(offline_stora_explorer_collection, {}))
        print(f'Database is cleared')
    else:
        sys.exit()

if namespace.delete is not None:
    loop.run_until_complete(do_delete_many(offline_stora_explorer_collection, {'resource': namespace.delete}))
    print(f'Resource [{namespace.delete}] deleted')

if namespace.add is not None:
    loop.run_until_complete(do_list_dir(offline_stora_explorer_collection, namespace.add, namespace.path, "None"))
    print(f'Resource [{namespace.add}] created')

if namespace.update is not None:
    loop.run_until_complete(do_delete_many(offline_stora_explorer_collection, {'resource': namespace.update}))
    loop.run_until_complete(do_list_dir(offline_stora_explorer_collection, namespace.update, namespace.path, "None"))
    print(f'Resource [{namespace.update}] updated')

