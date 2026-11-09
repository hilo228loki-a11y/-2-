"""Модуль 3 (Python): очередь на односвязном списке.

Тот же интерфейс, что и у обёртки над C++ библиотеками (см. queue_cpp.py).
"""


class QueueEmptyError(Exception):
    """Попытка взять/посмотреть элемент из пустой очереди."""


class _Node:
    __slots__ = ("data", "next")

    def __init__(self, data):
        self.data = data
        self.next = None


class PyQueue:
    name = "Python (связный список)"

    def __init__(self):
        self._head = None
        self._tail = None
        self._count = 0

    def enqueue(self, value: int) -> None:
        node = _Node(value)
        if self._tail is None:
            self._head = node
        else:
            self._tail.next = node
        self._tail = node
        self._count += 1

    def dequeue(self) -> int:
        if self._head is None:
            raise QueueEmptyError("Очередь пуста: удалять нечего.")
        node = self._head
        self._head = node.next
        if self._head is None:
            self._tail = None
        self._count -= 1
        return node.data

    def peek(self) -> int:
        if self._head is None:
            raise QueueEmptyError("Очередь пуста: нет первого элемента.")
        return self._head.data

    def size(self) -> int:
        return self._count

    def clear(self) -> None:
        self._head = None
        self._tail = None
        self._count = 0

    def items(self) -> list:
        result, cur = [], self._head
        while cur is not None:
            result.append(cur.data)
            cur = cur.next
        return result

    def close(self) -> None:
        self.clear()
