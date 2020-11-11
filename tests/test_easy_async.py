from math import isclose
from unittest import TestCase

import asks
from trio import sleep
from flaky import flaky
from many_requests.easy_async import EasyAsync, delayed, zip_kw

@flaky(max_runs=5, min_passes=1)
class TestEasyAsync(TestCase):

    def test_EasyAsync_sleep(self):
        n_workers = 3
        n_tasks = 10
        sleep_seconds = 1
        output = EasyAsync(n_workers)(delayed(sleep)(sleep_seconds) for i in range(n_tasks))

        assert len(output) == n_tasks
        assert output == [None] * len(output)

    def test_EasyAsync_isclose(self):
        async def isclose_(a, b, abs_tol):
            return isclose(a=a, b=b, abs_tol=abs_tol)

        output = EasyAsync(n_workers=4)(
            delayed(isclose_)(**kwargs) for kwargs in zip_kw(a=range(10), b=range(10)[::-1], abs_tol=4))

        assert output == [False, False, False, True, True, True, True, False, False, False]

    def test_AsyncParallel_ask_get(self):
        n_workers = 3
        n_tasks = 10
        EasyAsync(n_workers)(delayed(asks.get)(f'https://example.org/{i}') for i in range(n_tasks))
