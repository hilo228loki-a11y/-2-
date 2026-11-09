"""Обёртка (ctypes) над C++ библиотеками очереди.

Две реализации с одинаковым C-интерфейсом:
  * queue_dyn - структуры на динамической памяти (new/delete);
  * queue_stl - адаптер STL std::queue.
"""
import ctypes
import os
import sys

from queue_py import QueueEmptyError

_DIR = os.path.dirname(os.path.abspath(__file__))
_EXT = ".dll" if sys.platform.startswith("win") else (".dylib" if sys.platform == "darwin" else ".so")

INT_MIN, INT_MAX = -2**31, 2**31 - 1


def library_path(lib_name: str) -> str:
    return os.path.join(_DIR, lib_name + _EXT)


def library_available(lib_name: str) -> bool:
    return os.path.exists(library_path(lib_name))


class CppQueue:
    def __init__(self, lib_name: str, title: str):
        path = library_path(lib_name)
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Библиотека {os.path.basename(path)} не найдена. Сначала соберите её (см. README).")
        self.name = title
        lib = ctypes.CDLL(path)
        vp, ip = ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)

        lib.q_create.restype = vp
        lib.q_create.argtypes = []
        lib.q_destroy.restype = None
        lib.q_destroy.argtypes = [vp]
        lib.q_clear.restype = None
        lib.q_clear.argtypes = [vp]
        lib.q_enqueue.restype = ctypes.c_int
        lib.q_enqueue.argtypes = [vp, ctypes.c_int]
        lib.q_dequeue.restype = ctypes.c_int
        lib.q_dequeue.argtypes = [vp, ip]
        lib.q_peek.restype = ctypes.c_int
        lib.q_peek.argtypes = [vp, ip]
        lib.q_size.restype = ctypes.c_int
        lib.q_size.argtypes = [vp]
        lib.q_to_array.restype = ctypes.c_int
        lib.q_to_array.argtypes = [vp, ip, ctypes.c_int]

        self._lib = lib
        self._h = lib.q_create()
        if not self._h:
            raise MemoryError("Не удалось создать очередь.")

    def enqueue(self, value: int) -> None:
        if not INT_MIN <= value <= INT_MAX:
            raise OverflowError("Число не помещается в 32-битный int.")
        if not self._lib.q_enqueue(self._h, value):
            raise MemoryError("Недостаточно памяти для нового элемента.")

    def dequeue(self) -> int:
        out = ctypes.c_int()
        if not self._lib.q_dequeue(self._h, ctypes.byref(out)):
            raise QueueEmptyError("Очередь пуста: удалять нечего.")
        return out.value

    def peek(self) -> int:
        out = ctypes.c_int()
        if not self._lib.q_peek(self._h, ctypes.byref(out)):
            raise QueueEmptyError("Очередь пуста: нет первого элемента.")
        return out.value

    def size(self) -> int:
        return self._lib.q_size(self._h)

    def clear(self) -> None:
        self._lib.q_clear(self._h)

    def items(self) -> list:
        n = self.size()
        if n == 0:
            return []
        buf = (ctypes.c_int * n)()
        got = self._lib.q_to_array(self._h, buf, n)
        return list(buf[:got])

    def close(self) -> None:
        if self._h:
            self._lib.q_destroy(self._h)
            self._h = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
