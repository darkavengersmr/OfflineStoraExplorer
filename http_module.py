#!/usr/bin/python3

import asyncio
import motor.motor_asyncio
from bson.objectid import ObjectId
from db_module import get_list_dir, do_find_one, do_list_dir, do_delete_many
from aiohttp import web
import logging

router = web.RouteTableDef()
offline_stora_explorer_collection = None


def setup_db():
    global offline_stora_explorer_collection
    if offline_stora_explorer_collection == None:
        db_client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://192.168.32.64:27017',
                                                           io_loop=asyncio.get_event_loop())
        db = db_client.offline_stora_explorer
        offline_stora_explorer_collection = db.test
        logging.info('!!! Hook enable: Aiohttp and Motor in the same event loop')


@router.get("/files/")
async def go_to_dir(request: web.Request) -> web.Response:
    setup_db()
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


@router.get("/savedata/")
async def save_data(request: web.Request) -> web.Response:
    setup_db()

    resource = "My test"
    path = "D:\\My Work"

    try:
        await do_delete_many(offline_stora_explorer_collection, {'resource': resource})
        logging.info(f'resource {resource} deleted')
        await do_list_dir(offline_stora_explorer_collection, resource, path, "None")
        logging.info(f'resource {resource} created')
        status = 200
        result = {'process': 'finished'}
    except:
        status = 500
        result = {'process': 'error'}

    return web.json_response(result, status=status)

async def root_handler(request):
    return web.HTTPFound('/index.html')


async def init_app() -> web.Application:
    #app = web.Application(middlewares=[auth], client_max_size=1024**3)
    app = web.Application(client_max_size=1024 ** 3)
    app.add_routes(router)
    app.router.add_route('*', '/', root_handler)
    #app.router.add_static('/', './web/static')
    logging.basicConfig(level=logging.DEBUG)
    return app


if __name__ == '__main__':
    web.run_app(init_app(), port=5000)

