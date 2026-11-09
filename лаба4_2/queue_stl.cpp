// Модуль 2 (C++): очередь на основе адаптера STL std::queue<int>.
// Тот же C-интерфейс, что и у queue_dyn.cpp, поэтому библиотеки взаимозаменяемы.
#include <queue>
#include <new>

#ifdef _WIN32
#define API extern "C" __declspec(dllexport)
#else
#define API extern "C"
#endif

typedef std::queue<int> IntQueue;

API void* q_create() {
    return new (std::nothrow) IntQueue();
}

API void q_clear(void* h) {
    IntQueue* q = static_cast<IntQueue*>(h);
    IntQueue empty;
    q->swap(empty);
}

API void q_destroy(void* h) {
    delete static_cast<IntQueue*>(h);
}

API int q_enqueue(void* h, int value) {
    try {
        static_cast<IntQueue*>(h)->push(value);
        return 1;
    } catch (...) {
        return 0;  // исключения не должны пересекать границу C/Python
    }
}

API int q_dequeue(void* h, int* out) {
    IntQueue* q = static_cast<IntQueue*>(h);
    if (q->empty()) return 0;
    *out = q->front();
    q->pop();
    return 1;
}

API int q_peek(void* h, int* out) {
    IntQueue* q = static_cast<IntQueue*>(h);
    if (q->empty()) return 0;
    *out = q->front();
    return 1;
}

API int q_size(void* h) {
    return static_cast<int>(static_cast<IntQueue*>(h)->size());
}

// std::queue не умеет итерироваться, поэтому обходим копию адаптера
API int q_to_array(void* h, int* buf, int cap) {
    IntQueue copy = *static_cast<IntQueue*>(h);
    int i = 0;
    while (!copy.empty() && i < cap) {
        buf[i++] = copy.front();
        copy.pop();
    }
    return i;
}
