import asyncio
import multiprocessing
import random
from time import sleep
from unittest import TestCase
from aiohttp import web
import pytest
from asks.response_objects import Response
import logging
from flaky import flaky

from many_requests.many_requests_ import ManyRequests
from many_requests.common import BadResponse

@flaky(max_runs=5, min_passes=1)
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
        web.run_app(app)

    logging.info('Start mock server')
    p = multiprocessing.Process(target=mock_web_server)
    p.start()
    sleep(10)  # Wait for server to start-up
    yield web
    logging.info('Teardown mock server')
    p.terminate()


@pytest.mark.usefixtures("web_server")
class TestManyRequest(TestCase):

    def test_request(self):
        urls = [f'http://0.0.0.0:8080/' for i in range(10)]
        responses = ManyRequests(10, 2, retries=2, retry_sleep=0)(method='GET', url=urls)
        assert len(responses) == 10
        for response, url in zip(responses, urls):
            assert response.url == url
            assert isinstance(response, Response)

    def test_request_json(self):
        json = True
        urls = [f'http://0.0.0.0:8080/json' for i in range(10)]
        responses = ManyRequests(10, 2, retries=2, retry_sleep=0, json=json)(method='GET', url=urls)
        assert len(responses) == 10
        for response, url in zip(responses, urls):
            assert isinstance(response, dict)
            assert response == {"foo": "bar"}

    def test_json_failure(self):
        json = True
        urls = [f'http://0.0.0.0:8080/' for i in range(10)]
        responses = ManyRequests(10, 2, retries=2, retry_sleep=0, json=json)(method='GET', url=urls)
        assert len(responses) == 10
        for error, url in zip(responses, urls):
            assert isinstance(error, BadResponse)
            assert error.response.url == url
            assert error.reason == 'JSONDecodeError'

    def test_status_code_failure(self):
        urls = [f'https://example.org/bad_request' for i in range(10)]
        responses = ManyRequests(10, 2, retries=2, retry_sleep=0)(method='GET', url=urls)
        assert len(responses) == 10
        for error, url in zip(responses, urls):
            assert isinstance(error, BadResponse)
            assert error.response.url == url
            assert error.reason == 'bad_status_code'

    def test_single_request(self):
        json = False
        ok_code = (200,)
        responses = ManyRequests(10, 2, retries=2, retry_sleep=0, ok_codes=ok_code, json=json)(
            method='GET', url='https://example.org/')
        assert len(responses) == 1
        response = responses[0]
        assert response.url == 'https://example.org/'
        assert isinstance(response, Response)

