// Модуль 1 (C++): очередь на динамической памяти (односвязный список).
// Аналог реализации из лабораторной 4.1 (Pascal): Head / Tail / Count.
// Экспортируется через C-интерфейс, чтобы библиотеку можно было вызвать из Python (ctypes).
#include <cstddef>
#include <new>

#ifdef _WIN32
#define API extern "C" __declspec(dllexport)
#else
#define API extern "C"
#endif

struct Node {
    int data;
    Node* next;
};

struct Queue {
    Node* head;
    Node* tail;
    int count;
};

API void* q_create() {
    Queue* q = new Queue;
    q->head = nullptr;
    q->tail = nullptr;
    q->count = 0;
    return q;
}

API void q_clear(void* h) {
    Queue* q = static_cast<Queue*>(h);
    while (q->head != nullptr) {
        Node* tmp = q->head;
        q->head = q->head->next;
        delete tmp;
    }
    q->tail = nullptr;
    q->count = 0;
}

API void q_destroy(void* h) {
    if (!h) return;
    q_clear(h);
    delete static_cast<Queue*>(h);
}

// Возвращает 1 при успехе, 0 при нехватке памяти
API int q_enqueue(void* h, int value) {
    Queue* q = static_cast<Queue*>(h);
    Node* node = new (std::nothrow) Node;
    if (!node) return 0;
    node->data = value;
    node->next = nullptr;
    if (q->tail == nullptr)
        q->head = node;
    else
        q->tail->next = node;
    q->tail = node;
    q->count++;
    return 1;
}

// Возвращает 1 при успехе, 0 если очередь пуста
API int q_dequeue(void* h, int* out) {
    Queue* q = static_cast<Queue*>(h);
    if (q->head == nullptr) return 0;
    Node* tmp = q->head;
    *out = tmp->data;
    q->head = tmp->next;
    if (q->head == nullptr) q->tail = nullptr;
    delete tmp;
    q->count--;
    return 1;
}

// Возвращает 1 при успехе, 0 если очередь пуста
API int q_peek(void* h, int* out) {
    Queue* q = static_cast<Queue*>(h);
    if (q->head == nullptr) return 0;
    *out = q->head->data;
    return 1;
}

API int q_size(void* h) {
    return static_cast<Queue*>(h)->count;
}

// Копирует элементы (от головы к хвосту) в буфер; возвращает число скопированных
API int q_to_array(void* h, int* buf, int cap) {
    Queue* q = static_cast<Queue*>(h);
    int i = 0;
    for (Node* cur = q->head; cur != nullptr && i < cap; cur = cur->next)
        buf[i++] = cur->data;
    return i;
}
