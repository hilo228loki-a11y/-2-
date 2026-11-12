"""Генератор data.csv (предметная область: сотрудники компании).

Поля: id, name, city, age, salary, date
Данные только ASCII, поэтому 1 символ = 1 байт и размер считается точно.
Запуск:  python generator.py [размер_в_МБ] [путь]   (по умолчанию 1100 МБ, data.csv)
"""
import random
import sys
import time

HEADER = "id,name,city,age,salary,date\n"

SURNAMES = ["Ivanov", "Petrov", "Sidorov", "Smirnov", "Kuznetsov", "Popov", "Sokolov",
            "Lebedev", "Kozlov", "Novikov", "Morozov", "Volkov", "Solovyov", "Vasilyev",
            "Zaytsev", "Pavlov", "Semyonov", "Golubev", "Vinogradov", "Bogdanov",
            "Vorobyov", "Fyodorov", "Mikhaylov", "Belyaev", "Tarasov", "Belov",
            "Komarov", "Orlov", "Kiselyov", "Makarov"]
NAMES = ["Alexey", "Dmitry", "Ivan", "Sergey", "Andrey", "Maxim", "Nikita", "Pavel",
         "Anna", "Maria", "Elena", "Olga", "Natalia", "Irina", "Tatiana", "Ekaterina"]
CITIES = ["Moscow", "Saint-Petersburg", "Kazan", "Novosibirsk", "Yekaterinburg", "Samara",
          "Omsk", "Chelyabinsk", "Rostov", "Ufa", "Perm", "Voronezh", "Volgograd",
          "Krasnodar", "Tyumen", "Tomsk", "Irkutsk", "Tver", "Kaliningrad", "Sochi"]
DATES = [f"{y}-{m:02d}-{d:02d}" for y in range(2015, 2025)
         for m in range(1, 13) for d in range(1, 29)]
BATCH = 100_000


def generate(path="data.csv", size_mb=1100, seed=None, progress=None):
    """Пишет CSV размером не менее size_mb МБ. progress(доля) вызывается после каждой пачки."""
    rnd = random.Random(seed)
    target = int(size_mb * 1024 * 1024)
    written = len(HEADER)
    row_id = 0
    with open(path, "w", newline="", encoding="ascii", buffering=1 << 20) as f:
        f.write(HEADER)
        while written < target:
            sur = rnd.choices(SURNAMES, k=BATCH)
            nam = rnd.choices(NAMES, k=BATCH)
            cit = rnd.choices(CITIES, k=BATCH)
            age = rnd.choices(range(18, 66), k=BATCH)
            dat = rnd.choices(DATES, k=BATCH)
            lines = []
            for i in range(BATCH):
                row_id += 1
                sal = 20000 + rnd.random() * 280000
                lines.append(f"{row_id},{sur[i]} {nam[i]},{cit[i]},{age[i]},{sal:.2f},{dat[i]}")
            # перемешиваем id, чтобы файл не был уже отсортирован по первому ключу
            rnd.shuffle(lines)
            text = "\n".join(lines) + "\n"
            f.write(text)
            written += len(text)
            if progress:
                progress(min(1.0, written / target))
    return written


if __name__ == "__main__":
    size = float(sys.argv[1]) if len(sys.argv) > 1 else 1100
    out = sys.argv[2] if len(sys.argv) > 2 else "data.csv"
    t = time.perf_counter()
    n = generate(out, size, progress=lambda p: print(f"\r{p*100:5.1f}%", end="", flush=True))
    print(f"\nГотово: {out}, {n/1024/1024:.1f} МБ, {time.perf_counter()-t:.1f} c")
