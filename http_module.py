#!/usr/bin/python3

import os
import logging
import asyncio
import motor.motor_asyncio
from bson.objectid import ObjectId

from aiohttp import web

from db_module import get_list_dir, do_find_one, do_search

disk_command_path = '/usr/stora/'
my_disks = ('1', '2', '3', '4', '5', '6')
db_socket = "192.168.32.64:27017"

router = web.RouteTableDef()
offline_stora_explorer_collection = None

def setup_db(db_socket):
    global offline_stora_explorer_collection
    if offline_stora_explorer_collection == None:
        db_client = motor.motor_asyncio.AsyncIOMotorClient(f'mongodb://{db_socket}',
                                                           io_loop=asyncio.get_event_loop())
        db = db_client.offline_stora_explorer
        offline_stora_explorer_collection = db.test
        logging.info('!!! Hook enable: Aiohttp and Motor in the same event loop')


@router.get("/files/")
async def go_to_dir(request: web.Request) -> web.Response:
    setup_db(db_socket)
    status = 200

    try:
        operation = request.query["operation"]
        id = request.query["id"]
    except:
        result = {'error': 'request invalid'}
        status = 400

    try:
        if operation == 'dir_list':
            result = await get_list_dir(offline_stora_explorer_collection, id)
            if len(result) == 0:
                result = {'error': 'object is file, not directory'}
                status = 400
        elif operation == 'dir_up':
            if id != 'None':
                updir = await do_find_one(offline_stora_explorer_collection, {'_id': ObjectId(id)})
                result = await get_list_dir(offline_stora_explorer_collection, updir['parent'])
            else:
                result = await get_list_dir(offline_stora_explorer_collection, 'None')
        else:
            result = {'error': 'unknown operation'}
            status = 400
    except:
        result = {'error': 'unknown data'}
        status = 204

    return web.json_response(result, status=status)


@router.get("/search/")
async def go_search(request: web.Request) -> web.Response:
    setup_db(db_socket)
    status = 200
    try:
        search_string = request.query["search"]
    except:
        result = {'error': 'request invalid'}
        status = 400
    try:
        result = await do_search(offline_stora_explorer_collection, search_string)
    except:
        result = {'error': 'unknown data'}
        status = 204
    return web.json_response(result, status=status)


@router.get("/command/")
async def go_command(request: web.Request) -> web.Response:
    valid_commands = ('disk', 'status')
    valid_parameters = my_disks

    command = request.query["command"]
    parameter = request.query["parameter"]

    if command in valid_commands and parameter in valid_parameters:
        shell_command = f'{disk_command_path}{command} {parameter}'
        #os.system(shell_command) // uncomment for production
        os.system(f'echo {shell_command}')
        result = {f'{command} {parameter}': 'done'}
        status = 200
    else:
        result = {'error': 'invalid command'}
        status = 204
    return web.json_response(result, status=status)


async def root_handler(request):
    return web.HTTPFound('/index.html')


async def init_app() -> web.Application:
    app = web.Application(client_max_size=1024 ** 3)
    app.add_routes(router)
    app.router.add_route('*', '/', root_handler)
    app.router.add_static('/', './web/static')
    logging.basicConfig(level=logging.DEBUG)
    return app


if __name__ == '__main__':
    web.run_app(init_app(), port=5000)

