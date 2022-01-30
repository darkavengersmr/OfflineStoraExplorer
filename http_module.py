#!/usr/bin/python3

import os
import logging
import asyncio
import motor.motor_asyncio
from bson.objectid import ObjectId

from aiohttp import web
from aiohttp_swagger3 import SwaggerDocs, SwaggerUiSettings

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


async def go_to_dir(request: web.Request) -> web.Response:
    """
        Endpoint: files
        ---
        summary: Перейти в директорию по ее id или перейти в директорию выше уровнем от указанной по id
        tags:
          - files
        parameters:
          - name: operation
            in: query
            required: true
            description: Допустимые команды - dir_list, dir_up
            schema:
              type: string
              format: string
          - name: id
            in: query
            required: true
            description: Допустимые команды - id директории (или None для выхода на уровень ресурсов)
            schema:
              type: string
              format: string
        responses:
          '200':
            description: Содержимое указанной директории/ресурса
            content:
              application/json:
                schema:
                  $ref: "#/components/schemas/command"
          '204':
            description: Ошибка построения содержимого диретории
            content:
              application/json:
                schema:
                  $ref: "#/components/schemas/command"
          '400':
            description: Некорректная команда, не входит в список разрешенных
            content:
              application/json:
                schema:
                  $ref: "#/components/schemas/command"
        """
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


async def go_search(request: web.Request) -> web.Response:
    """
    Endpoint: search
    ---
    summary: Поиск по файловым ресурсам
    tags:
      - search
    parameters:
      - name: search
        in: query
        required: true
        description: Подстрока для поиска
        schema:
          type: string
          format: string
    responses:
      '200':
        description: Результаты поискового запроса
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/command"
      '204':
        description: Ошибка поиска
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/command"
      '400':
        description: Некорректный запрос
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/command"
    """
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


async def go_command(request: web.Request) -> web.Response:
    """
    Endpoint: command
    ---
    summary: Отправка команд для включения/выключения дисков или получения их статуса
    tags:
      - command
    parameters:
      - name: command
        in: query
        required: true
        description: Допустимые команды - disk, status
        schema:
          type: string
          format: string
      - name: parameter
        in: query
        required: true
        description: Допустимые команды - 0,1,2,3,4,5,6
        schema:
          type: string
          format: string
    responses:
      '200':
        description: Команда выполнена
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/command"
      '204':
        description: Некорректная команда, не входит в список разрешенных
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/command"
    """
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

    swagger = SwaggerDocs(
        app,
        swagger_ui_settings=SwaggerUiSettings(path="/docs/"),
        title="Документация OfflineStoraExplorer API",
        version="1.0.0",
        components="components.yaml"
    )
    swagger.add_routes([
        web.get("/files/", go_to_dir),
        web.get("/search/", go_search),
        web.get("/command/", go_command),
    ])

    app.add_routes(router)
    app.router.add_route('*', '/', root_handler)
    app.router.add_static('/', './web/static')
    logging.basicConfig(level=logging.DEBUG)

    return app


if __name__ == '__main__':
    web.run_app(init_app(), port=5000)

