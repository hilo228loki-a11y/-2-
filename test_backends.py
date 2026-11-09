"""Проверка всех реализаций очереди одним и тем же набором тестов (без GUI)."""
import unittest

from backends import available_backends, create_queue
from queue_py import QueueEmptyError


class QueueContract(unittest.TestCase):
    def test_all_backends(self):
        names = available_backends()
        self.assertTrue(names)
        for name in names:
            with self.subTest(backend=name):
                q = create_queue(name)
                # пустая очередь
                self.assertEqual(q.size(), 0)
                self.assertEqual(q.items(), [])
                with self.assertRaises(QueueEmptyError):
                    q.dequeue()
                with self.assertRaises(QueueEmptyError):
                    q.peek()
                # FIFO
                for v in (10, -5, 0, 42):
                    q.enqueue(v)
                self.assertEqual(q.items(), [10, -5, 0, 42])
                self.assertEqual(q.size(), 4)
                self.assertEqual(q.peek(), 10)
                self.assertEqual(q.size(), 4)  # peek не удаляет
                self.assertEqual(q.dequeue(), 10)
                self.assertEqual(q.dequeue(), -5)
                self.assertEqual(q.items(), [0, 42])
                # опустошение и повторное использование (Tail сбрасывается)
                q.dequeue(); q.dequeue()
                with self.assertRaises(QueueEmptyError):
                    q.dequeue()
                q.enqueue(7)
                self.assertEqual(q.items(), [7])
                # clear
                q.enqueue(8)
                q.clear()
                self.assertEqual((q.size(), q.items()), (0, []))
                # много элементов
                for i in range(1000):
                    q.enqueue(i)
                self.assertEqual(q.size(), 1000)
                self.assertEqual(q.dequeue(), 0)
                q.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
