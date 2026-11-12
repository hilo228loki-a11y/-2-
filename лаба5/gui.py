"""GUI для лабораторной 5.1: генерация, внешняя сортировка (Python / C++), проверка результата.

Интеграция модулей:
  * генератор  - прямой импорт generator.generate() (в отдельном потоке);
  * Python-сортировка - запуск external_sort.py подпроцессом;
  * C++-сортировка    - запуск скомпилированного external_sort(.exe) подпроцессом
                        (при отсутствии exe GUI пробует собрать его через g++).
Подпроцессы печатают строки KEY=VALUE, GUI их разбирает и показывает время фаз.
"""
import csv
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import generator

BASE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(BASE, "external_sort.exe" if os.name == "nt" else "external_sort")
PREVIEW_LINES = 15


def detect_caster(v):
    for c in (int, float):
        try:
            c(v)
            return c
        except ValueError:
            pass
    return str


class App:
    def __init__(self, root):
        self.root = root
        root.title("Лабораторная 5.1 - внешняя сортировка")
        root.geometry("900x700")
        self.src = tk.StringVar()
        self.size_mb = tk.StringVar(value="1100")
        self.key = tk.StringVar()
        self.impl = tk.StringVar(value="cpp")
        self.busy = False

        # --- генерация ---
        f1 = ttk.LabelFrame(root, text="1. Генерация данных")
        f1.pack(fill="x", padx=8, pady=4)
        ttk.Label(f1, text="Размер, МБ:").pack(side="left", padx=4)
        ttk.Entry(f1, textvariable=self.size_mb, width=8).pack(side="left")
        ttk.Button(f1, text="Сгенерировать...", command=self.on_generate).pack(side="left", padx=8)
        self.progress = ttk.Progressbar(f1, length=250, maximum=100)
        self.progress.pack(side="left", padx=8)

        # --- выбор файла и сортировка ---
        f2 = ttk.LabelFrame(root, text="2. Сортировка")
        f2.pack(fill="x", padx=8, pady=4)
        row = ttk.Frame(f2)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text="Файл:").pack(side="left", padx=4)
        ttk.Entry(row, textvariable=self.src).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Выбрать...", command=self.on_choose).pack(side="left", padx=4)
        row = ttk.Frame(f2)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text="Ключ:").pack(side="left", padx=4)
        self.key_box = ttk.Combobox(row, textvariable=self.key, state="readonly", width=14)
        self.key_box.pack(side="left")
        ttk.Radiobutton(row, text="C++", variable=self.impl, value="cpp").pack(side="left", padx=10)
        ttk.Radiobutton(row, text="Python", variable=self.impl, value="py").pack(side="left")
        ttk.Button(row, text="Сортировать", command=self.on_sort).pack(side="left", padx=10)

        # --- проверка ---
        f3 = ttk.LabelFrame(root, text="3. Проверка")
        f3.pack(fill="x", padx=8, pady=4)
        ttk.Button(f3, text="Начало/конец исходного файла", command=self.show_source).pack(side="left", padx=4, pady=2)
        ttk.Button(f3, text="Начало/конец sorted.txt + проверка порядка",
                   command=self.on_verify).pack(side="left", padx=4)

        self.text = tk.Text(root, wrap="none", font=("Courier New", 10))
        sb = ttk.Scrollbar(root, command=self.text.yview)
        self.text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.text.pack(fill="both", expand=True, padx=8, pady=4)

    # ---------- утилиты ----------
    def log(self, msg):
        self.root.after(0, lambda: (self.text.insert("end", msg + "\n"), self.text.see("end")))

    def clear(self):
        self.text.delete("1.0", "end")

    def sorted_path(self):
        return os.path.join(os.path.dirname(os.path.abspath(self.src.get())), "sorted.txt")

    def load_header(self):
        try:
            with open(self.src.get(), newline="", encoding="utf-8") as f:
                cols = next(csv.reader([f.readline()]))
            self.key_box["values"] = cols
            if cols:
                self.key.set(cols[min(4, len(cols) - 1)])
        except OSError as e:
            messagebox.showerror("Ошибка", str(e))

    # ---------- генерация ----------
    def on_generate(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="data.csv",
                                            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            size = float(self.size_mb.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректный размер")
            return
        if self.busy:
            return
        self.busy = True
        self.clear()
        self.log(f"Генерация {size} МБ -> {path} ...")

        def work():
            def prog(p):
                self.root.after(0, lambda: self.progress.configure(value=p * 100))
            n = generator.generate(path, size, progress=prog)
            self.log(f"Готово: {n / 1024 / 1024:.1f} МБ")
            self.busy = False
            self.root.after(0, lambda: (self.src.set(path), self.load_header()))
        threading.Thread(target=work, daemon=True).start()

    def on_choose(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv"), ("Все файлы", "*.*")])
        if path:
            self.src.set(path)
            self.load_header()

    # ---------- сортировка ----------
    def ensure_exe(self):
        if os.path.exists(EXE):
            return True
        self.log("external_sort не найден, пробую собрать через g++ ...")
        r = subprocess.run(["g++", "-O2", "-std=c++17", os.path.join(BASE, "external_sort.cpp"), "-o", EXE],
                           capture_output=True, text=True)
        if r.returncode != 0:
            self.log("Ошибка компиляции:\n" + r.stderr)
            return False
        return True

    def on_sort(self):
        if self.busy:
            return
        if not os.path.isfile(self.src.get()) or not self.key.get():
            messagebox.showwarning("Внимание", "Выберите файл и ключ")
            return
        self.busy = True
        self.clear()
        src, dst, key = self.src.get(), self.sorted_path(), self.key.get()

        def work():
            try:
                if self.impl.get() == "cpp":
                    if not self.ensure_exe():
                        return
                    cmd = [EXE, src, dst, key]
                else:
                    cmd = [sys.executable, os.path.join(BASE, "external_sort.py"), src, dst, "--key", key]
                self.log(f"Запуск ({self.impl.get()}): ключ = {key}")
                p = subprocess.run(cmd, capture_output=True, text=True)
                self.log(p.stdout.strip() or p.stderr.strip())
                if p.returncode == 0:
                    self.log(f"\nРезультат: {dst}")
            finally:
                self.busy = False
        threading.Thread(target=work, daemon=True).start()

    # ---------- просмотр и проверка ----------
    @staticmethod
    def head_tail(path, n=PREVIEW_LINES):
        with open(path, "r", encoding="utf-8", newline="") as f:
            head = [f.readline().rstrip("\n") for _ in range(n + 1)]
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - 4096))
            tail = f.read().decode("utf-8", "ignore").splitlines()[-n:]
        return head, tail

    def show_file(self, path, title):
        head, tail = self.head_tail(path)
        self.log(f"=== {title}: первые строки ===")
        self.log("\n".join(head))
        self.log(f"=== {title}: последние строки ===")
        self.log("\n".join(tail))

    def show_source(self):
        if os.path.isfile(self.src.get()):
            self.clear()
            self.show_file(self.src.get(), "исходный файл")

    def on_verify(self):
        out = self.sorted_path() if self.src.get() else ""
        if not os.path.isfile(out):
            messagebox.showwarning("Внимание", "Сначала выполните сортировку")
            return
        self.clear()
        self.show_file(out, "sorted.txt")
        key = self.key.get()

        def work():
            with open(out, newline="", encoding="utf-8") as f:
                r = csv.reader(f)
                header = next(r)
                idx = header.index(key)
                caster, prev, n, ok = None, None, 0, True
                for row in r:
                    if caster is None:
                        caster = detect_caster(row[idx])
                    k = caster(row[idx])
                    if prev is not None and k < prev:
                        self.log(f"НАРУШЕН ПОРЯДОК в строке {n + 2}: {prev} > {k}")
                        ok = False
                        break
                    prev = k
                    n += 1
            with open(self.src.get(), "rb") as f:
                src_n = sum(chunk.count(b"\n") for chunk in iter(lambda: f.read(1 << 20), b"")) - 1
            self.log(f"\nСтрок в sorted.txt: {n}, в исходном: {src_n} "
                     f"({'совпадает' if n == src_n else 'НЕ СОВПАДАЕТ'})")
            self.log("Порядок по ключу: " + ("ВЕРНЫЙ" if ok else "ОШИБКА"))
        threading.Thread(target=work, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
