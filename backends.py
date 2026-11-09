"""Фабрика реализаций очереди: GUI знает только про create_queue()."""
from queue_py import PyQueue
from queue_cpp import CppQueue, library_available

BACKENDS = {
    "C++ (динамическая память)": lambda: CppQueue("queue_dyn", "C++ (динамическая память)"),
    "C++ (STL std::queue)": lambda: CppQueue("queue_stl", "C++ (STL std::queue)"),
    "Python (связный список)": lambda: PyQueue(),
}

_LIBS = {
    "C++ (динамическая память)": "queue_dyn",
    "C++ (STL std::queue)": "queue_stl",
}


def available_backends() -> list:
    return [n for n in BACKENDS if n not in _LIBS or library_available(_LIBS[n])]


def create_queue(name: str):
    return BACKENDS[name]()
