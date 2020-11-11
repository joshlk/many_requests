
from itertools import repeat, count
from typing import Iterable, Optional, Coroutine, Any

import trio
from tqdm.auto import tqdm

from many_requests.common import N_WORKERS_DEFAULT, is_collection


def delayed(coroutine):
    """Decorator used to capture a coroutine and delay its execution"""

    def delayed_coroutine(*args, **kwargs):
        return coroutine, args, kwargs

    return delayed_coroutine


def zip_kw(**kwargs):
    """
    Return an iterator of dictionaries, where the Nth item of each iterator specified in `kwargs` is paired together.
    Like `zip` but returns a dict instead.
    Also keyword arguments which are strings or not iterators are repeated automatically repeated.
    The iterator stops when the shortest iterator has been exhausted.
    """

    has_collection = False
    for k, v in kwargs.items():
        if not is_collection(v):
            kwargs[k] = repeat(v)
        else:
            has_collection = True
            kwargs[k] = iter(v)

    counter = count() if has_collection else range(1)
    try:
        for i in counter:
            dict_item = {k: next(v) for k, v in kwargs.items()}
            yield dict_item
    except StopIteration:
        pass


class EasyAsync:
    def __init__(self, n_workers=N_WORKERS_DEFAULT):
        """
        Dead simple parallel execution of async coroutines.
        `n_workers` are dispatched which asynchronously process each task given.

        Args:
            n_workers: Number of workers to use

        Examples:
            Each task sleeps for `i` seconds asyncronosly:

            >>> EasyAsync(n_workers = 4)(delayed(trio.sleep)(i) for i in range(10))

            Each task calculates `isclose` with a different `a` and `b` paramter. `abs_tol` is set the same for all.

            >>> from math import isclose
            >>> async def isclose_(a, b, abs_tol): return isclose(a=a, b=b, abs_tol=abs_tol)
            >>> EasyAsync(n_workers = 4)(
            >>>     delayed(isclose_)(**kwargs)
            >>>     for kwargs in zip_kw(a=range(10), b=range(10)[::-1], abs_tol=4))
        """

        self.n_workers = n_workers
        self.progress_bar = None

    def __call__(self, tasks: Iterable[delayed], length: Optional[int] = None):
        """
        Execute given coroutine `tasks` using workers. The order of output will match the order of input.

        Args:
            tasks: A sequence of coroutines to execute
            length: The number of tasks. If not specified it will try obtain the length automatically.
                Used for progress bar

        Returns:
            A list of outputs from each task. The order of items is determined by the input.
        """

        if length is None:
            try:
                length = len(tasks)
            except TypeError:
                pass

        self.progress_bar = tqdm(total=length, smoothing=0)

        self.tasks = enumerate(iter(tasks))  # Force the sequence to be a iterator
        self.outputs = []

        trio.run(self._worker_nursery)

        # Order output and remove idx
        self.outputs = sorted(self.outputs, key=lambda e: e[0])
        self.outputs = [e[1] for e in self.outputs]

        return self.outputs

    async def _worker_nursery(self):
        """Start a trio nursery with n workers"""
        async with trio.open_nursery() as nursery:
            for i in range(self.n_workers):
                nursery.start_soon(self._worker)

    async def _worker(self):
        """Execute tasks until exhausted"""
        for idx, task in self.tasks:
            function, args, kwargs = task
            output = await function(*args, **kwargs)
            self.outputs.append((idx, output))
            self._progress_update(1)

    def _progress_update(self, n):
        """Increment progress bar"""
        if self.progress_bar is not None:
            self.progress_bar.update(n)
