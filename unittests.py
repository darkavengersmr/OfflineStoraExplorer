import asyncio

import aiounittest
import motor.motor_asyncio

from db_module import get_list_dir, do_search

db_socket = "192.168.32.64:27017"
db_client = motor.motor_asyncio.AsyncIOMotorClient(f'mongodb://{db_socket}')
db = db_client.offline_stora_explorer
offline_stora_explorer_collection = db.test

class DBModuleTest(aiounittest.AsyncTestCase):

    async def test_get_list_dir(self):
        parent = 'None'
        ret = await get_list_dir(offline_stora_explorer_collection, parent)
        self.assertTrue(len(ret) > 2)

    async def test_do_search(self):
        search_string = '.mp3'
        ret = await do_search(offline_stora_explorer_collection, search_string)
        self.assertTrue(len(ret) > 200)

    def get_event_loop(self):
        self.my_loop = asyncio.get_event_loop()
        return self.my_loop