import asyncio
from collections import deque
from typing import Deque, TypeVar, Generic

T = TypeVar('T')

class AsyncDeque(Generic[T]):
    def __init__(self) -> None:
        # Annotate that our internal deque holds items of type T
        self._deque: Deque[T] = deque()
        self._condition = asyncio.Condition()

    async def appendright(self, item: T) -> None:
        """Add an item to the right end of the deque."""
        async with self._condition:
            self._deque.append(item)
            self._condition.notify()

    async def appendleft(self, item: T) -> None:
        """Add an item to the left end of the deque."""
        async with self._condition:
            self._deque.appendleft(item)
            self._condition.notify()

    async def popright(self) -> T:
        """
        Remove and return an item from the right end.
        Wait if the deque is empty.
        """
        async with self._condition:
            while not self._deque:
                await self._condition.wait()
            return self._deque.pop()

    async def popleft(self) -> T:
        """
        Remove and return an item from the left end.
        Wait if the deque is empty.
        """
        async with self._condition:
            while not self._deque:
                await self._condition.wait()
            return self._deque.popleft()
