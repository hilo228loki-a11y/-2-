"""Лабораторная 4.2: GUI (tkinter) для структуры данных «очередь».

Все операции выполняются только через модули (C++ библиотеки / Python модуль).
GUI хранит лишь ссылку на объект очереди и перерисовывает её после каждой операции.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from backends import available_backends, create_queue
from queue_py import QueueEmptyError

BOX_W, BOX_H, GAP, MARGIN = 70, 44, 34, 30
BG, BOX_FILL, BOX_HI = "#fdfdfd", "#dbeafe", "#bbf7d0"


class QueueApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Очередь — визуализация (лаб. 4.2)")
        self.geometry("860x520")
        self.minsize(640, 420)

        self.queue = None
        self.highlight = None  # индекс подсвеченного элемента (peek)

        self._build_widgets()

        names = available_backends()
        self.backend_box["values"] = names
        self.backend_box.set(names[0])
        self._switch_backend()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- интерфейс ----------
    def _build_widgets(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="Реализация:").pack(side="left")
        self.backend_box = ttk.Combobox(top, state="readonly", width=30)
        self.backend_box.pack(side="left", padx=6)
        self.backend_box.bind("<<ComboboxSelected>>", lambda e: self._switch_backend())

        ctrl = ttk.Frame(self, padding=(8, 0))
        ctrl.pack(fill="x")
        ttk.Label(ctrl, text="Значение:").pack(side="left")
        self.entry = ttk.Entry(ctrl, width=14)
        self.entry.pack(side="left", padx=6)
        self.entry.bind("<Return>", lambda e: self.on_enqueue())
        self.entry.focus_set()

        for text, cmd in (("Enqueue", self.on_enqueue), ("Dequeue", self.on_dequeue),
                          ("Peek", self.on_peek), ("Clear", self.on_clear)):
            ttk.Button(ctrl, text=text, command=cmd).pack(side="left", padx=3)

        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=1, highlightbackground="#bbb")
        hbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=hbar.set)
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)
        hbar.pack(fill="x", padx=8)
        self.canvas.bind("<Configure>", lambda e: self.redraw())

        self.info = ttk.Label(self, anchor="w", padding=(8, 4))
        self.info.pack(fill="x")

        log_frame = ttk.Frame(self, padding=(8, 0, 8, 8))
        log_frame.pack(fill="x")
        self.log = tk.Listbox(log_frame, height=5)
        self.log.pack(side="left", fill="x", expand=True)
        sb = ttk.Scrollbar(log_frame, command=self.log.yview)
        sb.pack(side="right", fill="y")
        self.log.configure(yscrollcommand=sb.set)

        self.status = ttk.Label(self, anchor="w", padding=(8, 4), relief="sunken")
        self.status.pack(fill="x", side="bottom")

    # ---------- служебное ----------
    def _say(self, msg, ok=True):
        self.status.configure(text=msg, foreground="#166534" if ok else "#b91c1c")
        self.log.insert("end", msg)
        self.log.see("end")

    def _error(self, msg):
        self._say("Ошибка: " + msg, ok=False)
        messagebox.showwarning("Некорректная операция", msg, parent=self)

    def _switch_backend(self):
        name = self.backend_box.get()
        old_items = self.queue.items() if self.queue else []
        try:
            new_q = create_queue(name)
        except Exception as exc:  # нет библиотеки, нехватка памяти и т.п.
            messagebox.showerror("Не удалось загрузить реализацию", str(exc), parent=self)
            if self.queue:
                self.backend_box.set(self.queue.name)
            return
        try:
            for v in old_items:  # переносим данные в новую реализацию
                new_q.enqueue(v)
        except Exception:
            pass
        if self.queue:
            self.queue.close()
        self.queue = new_q
        self.highlight = None
        self._say(f"Используется реализация: {name}")
        self.redraw()

    def _on_close(self):
        if self.queue:
            self.queue.close()
        self.destroy()

    # ---------- операции ----------
    def on_enqueue(self):
        text = self.entry.get().strip()
        if not text:
            return self._error("Введите целое число.")
        try:
            value = int(text)
        except ValueError:
            return self._error(f"«{text}» не является целым числом.")
        try:
            self.queue.enqueue(value)
        except (OverflowError, MemoryError) as exc:
            return self._error(str(exc))
        self.highlight = None
        self.entry.delete(0, "end")
        self._say(f"Enqueue: {value} добавлен в конец очереди.")
        self.redraw()

    def on_dequeue(self):
        try:
            value = self.queue.dequeue()
        except QueueEmptyError as exc:
            return self._error(str(exc))
        self.highlight = None
        self._say(f"Dequeue: из начала удалён элемент {value}.")
        self.redraw()

    def on_peek(self):
        try:
            value = self.queue.peek()
        except QueueEmptyError as exc:
            return self._error(str(exc))
        self.highlight = 0
        self._say(f"Peek: первый элемент = {value} (очередь не изменилась).")
        self.redraw()

    def on_clear(self):
        if self.queue.size() == 0:
            return self._error("Очередь уже пуста.")
        if not messagebox.askyesno("Очистка", f"Удалить все элементы ({self.queue.size()})?", parent=self):
            return
        self.queue.clear()
        self.highlight = None
        self._say("Clear: очередь очищена.")
        self.redraw()

    # ---------- визуализация ----------
    def redraw(self):
        c = self.canvas
        c.delete("all")
        items = self.queue.items() if self.queue else []
        size = self.queue.size() if self.queue else 0
        self.info.configure(text=f"Элементов: {size}    |    Front → {items[0] if items else '—'}"
                                 f"    |    Rear → {items[-1] if items else '—'}")
        h = max(c.winfo_height(), 200)
        y = h // 2 - BOX_H // 2

        if not items:
            c.create_text(c.winfo_width() // 2, h // 2, text="[ очередь пуста ]",
                          font=("Segoe UI", 16), fill="#888")
            c.configure(scrollregion=(0, 0, c.winfo_width(), h))
            return

        for i, v in enumerate(items):
            x = MARGIN + i * (BOX_W + GAP)
            fill = BOX_HI if i == self.highlight else BOX_FILL
            c.create_rectangle(x, y, x + BOX_W, y + BOX_H, fill=fill, outline="#1e3a8a", width=2)
            c.create_text(x + BOX_W / 2, y + BOX_H / 2, text=str(v), font=("Consolas", 13, "bold"))
            c.create_text(x + BOX_W / 2, y + BOX_H + 14, text=f"#{i}", fill="#666", font=("Segoe UI", 8))
            if i < len(items) - 1:
                c.create_line(x + BOX_W, y + BOX_H / 2, x + BOX_W + GAP, y + BOX_H / 2,
                              arrow="last", width=2, fill="#1e3a8a")

        last_x = MARGIN + (len(items) - 1) * (BOX_W + GAP)
        self._pointer(MARGIN + BOX_W / 2, y, "Front (Head)", "#15803d")
        self._pointer(last_x + BOX_W / 2, y, "Rear (Tail)", "#b45309", offset=(0 if len(items) > 1 else 0))
        c.configure(scrollregion=(0, 0, last_x + BOX_W + MARGIN, h))

    def _pointer(self, cx, box_top, label, color, offset=0):
        c = self.canvas
        ty = box_top - 55 - (22 if offset else 0)
        c.create_text(cx, ty, text=label, fill=color, font=("Segoe UI", 10, "bold"))
        c.create_line(cx, ty + 12, cx, box_top - 2, arrow="last", width=2, fill=color)


if __name__ == "__main__":
    QueueApp().mainloop()
