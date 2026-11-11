import itertools
import threading
from typing import Callable, Iterator

from cache import get_cached, set_cache

_live_iterators: dict[str, Iterator] = {}
_locks: dict[str, threading.Lock] = {}


def _lock_for(key: str) -> threading.Lock:
    if key not in _locks:
        _locks[key] = threading.Lock()
    return _locks[key]


def get_next_batch(key: str, count: int, iter_fn: Callable[[], Iterator]) -> list:
    """
    Returns the next `count` items for `key`, continuing from wherever
    the previous call for this key left off.
    """
    served_key = f"{key}:served"

    with _lock_for(key):
        if key not in _live_iterators:
            it = iter_fn()
            already_served = get_cached(served_key) or []
            skip = len(already_served)
            if skip:
                # Cold resume after a restart: burn through items we've
                # already handed out so we don't repeat them.
                list(itertools.islice(it, skip))
            _live_iterators[key] = it
        else:
            already_served = get_cached(served_key) or []

        batch = list(itertools.islice(_live_iterators[key], count))

        if len(batch) < count:
            # Source exhausted -- drop the dead generator. A later call
            # for this key will just get whatever's left (possibly empty).
            _live_iterators.pop(key, None)

        if batch:
            set_cache(served_key, already_served + batch)

    return batch


def reset_stream(key: str) -> None:
    """Forget a stream entirely -- next call starts from position 0 again."""
    with _lock_for(key):
        _live_iterators.pop(key, None)
        set_cache(f"{key}:served", [])
