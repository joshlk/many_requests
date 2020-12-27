import asyncio
import logging
import multiprocessing
import random
from time import sleep
import requests

import pytest
from aiohttp import web
from aiohttp_basicauth_middleware import basic_auth_middleware


@pytest.fixture(scope="module")
def web_server():
    def mock_web_server():
        SLEEP_MEAN = 1
        async def sleep_rand():
            secs = random.expovariate(1/SLEEP_MEAN)
            if secs > 2*SLEEP_MEAN:
                logging.info(f"Sleeping request for {secs} seconds")
            await asyncio.sleep(secs)

        async def ok_handle(request):
            await sleep_rand()
            return web.Response(text='Ok response')

        async def var_handle(request):
            await sleep_rand()
            name = request.match_info.get('text', "Anonymous")
            text = "Hello, " + name
            return web.Response(text=text)

        async def json_handle(request):
            json = '{"foo": "bar"}'
            await sleep_rand()
            return web.Response(text=json)

        async def bad_request_handle(request):
            await sleep_rand()
            return web.HTTPBadRequest()

        async def mixed_response_handle(request):
            await sleep_rand()
            return random.choices(
                [web.Response(text='Ok response'), web.HTTPTooManyRequests()],
                weights=[0.6,0.4]
            )[0]

        asyncio.set_event_loop(asyncio.new_event_loop())  # Only use if in seperate thread or process
        app = web.Application()
        app.router.add_get('/', ok_handle)
        app.router.add_get('/ok', ok_handle)
        app.router.add_get('/var/{text}', var_handle)
        app.router.add_get('/json', json_handle)
        app.router.add_get('/bad_request', bad_request_handle)
        app.router.add_get('/mixed_response', mixed_response_handle)

        # Route with basic auth
        app.router.add_route('GET', '/basic_auth', ok_handle)
        app.middlewares.append(
            basic_auth_middleware(('/basic_auth',), {'username': 'password'})
        )

        web.run_app(app)

    logging.info('Start mock server')
    p = multiprocessing.Process(target=mock_web_server)
    p.start()
    while True: # Wait for server to start-up
        try:
            r = requests.get('http://0.0.0.0:8080/')
        except:
            sleep(0.1)
            continue
        if r.ok:
            break
    yield web
    logging.info('Teardown mock server')
    p.terminate()
