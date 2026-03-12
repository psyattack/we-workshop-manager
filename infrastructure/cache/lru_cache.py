from collections import OrderedDict
from typing import Generic, Optional, TypeVar


K = TypeVar("K")
V = TypeVar("V")


class LRUCache(Generic[K, V]):
    def __init__(self, max_size: int):
        self.max_size = max_size
        self._data: OrderedDict[K, V] = OrderedDict()

    def get(self, key: K) -> Optional[V]:
        if key not in self._data:
            return None

        self._data.move_to_end(key)
        return self._data[key]

    def set(self, key: K, value: V) -> None:
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value

        while len(self._data) > self.max_size:
            self._data.popitem(last=False)

    def remove(self, key: K) -> None:
        self._data.pop(key, None)

    def clear(self) -> None:
        self._data.clear()

    def keys(self) -> list[K]:
        return list(self._data.keys())

    def values(self) -> list[V]:
        return list(self._data.values())

    def items(self) -> list[tuple[K, V]]:
        return list(self._data.items())

    def __contains__(self, key: K) -> bool:
        return key in self._data

    def __len__(self) -> int:
        return len(self._data)