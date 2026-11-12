"""Внешняя сортировка CSV (Python).

Использование:
    python external_sort.py data.csv sorted.txt --key salary [--mem-percent 10]

Ключ: имя столбца из заголовка либо номер столбца (с 0).
Тип ключа (int / float / str) определяется автоматически по первой строке данных.
Фаза 1 (split): читаем файл блоками ~chunk байт, сортируем блок в памяти, пишем «серию» во временный файл.
Фаза 2 (merge): k-путевое слияние серий через heapq.merge, запись блоками.
"""
import argparse
import csv
import heapq
import itertools
import os
import shutil
import sys
import tempfile
import time
from contextlib import ExitStack

CHUNK_FRACTION = 0.20   # доля лимита памяти под «сырой» размер блока (в Python объекты раздувают данные в 2-3 раза)
MERGE_BATCH = 20_000    # строк в одной записи в выходной файл


def detect_caster(value):
    for caster in (int, float):
        try:
            caster(value)
            return caster
        except ValueError:
            pass
    return str


def resolve_key(header_cols, key):
    if key in header_cols:
        return header_cols.index(key)
    if key.isdigit() and int(key) < len(header_cols):
        return int(key)
    raise SystemExit(f"Ключ '{key}' не найден. Столбцы: {header_cols}")


def split_phase(src, tmpdir, key_idx, caster, chunk_bytes):
    runs = []
    with open(src, "r", newline="", encoding="utf-8") as f:
        f.readline()  # заголовок
        while True:
            block = f.readlines(chunk_bytes)           # чтение блоком ~chunk_bytes байт
            block = [ln for ln in block if ln.strip()]
            if not block:
                break
            if not block[-1].endswith("\n"):
                block[-1] += "\n"
            keys = [caster(row[key_idx]) for row in csv.reader(block)]
            order = sorted(range(len(keys)), key=keys.__getitem__)
            path = os.path.join(tmpdir, f"run_{len(runs):05d}.tmp")
            with open(path, "w", newline="", encoding="utf-8", buffering=1 << 20) as out:
                out.writelines(block[i] for i in order)
            runs.append(path)
            del block, keys, order
    return runs


def merge_phase(runs, dst, header_line, key_idx, caster, buf_size):
    with ExitStack() as stack, open(dst, "w", newline="", encoding="utf-8", buffering=1 << 20) as out:
        files = [stack.enter_context(open(p, "r", newline="", encoding="utf-8", buffering=buf_size))
                 for p in runs]
        iters = [((caster(r[key_idx]), r) for r in csv.reader(fh)) for fh in files]
        out.write(header_line if header_line.endswith("\n") else header_line + "\n")
        writer = csv.writer(out, lineterminator="\n")
        merged = heapq.merge(*iters)
        while True:
            batch = list(itertools.islice(merged, MERGE_BATCH))
            if not batch:
                break
            writer.writerows(r for _, r in batch)


def peak_rss_mb():
    try:
        import resource
        v = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return v / 1024 / (1024 if sys.platform == "darwin" else 1)
    except ImportError:
        return None


def external_sort(src, dst, key, mem_percent=10.0):
    size = os.path.getsize(src)
    mem_limit = int(size * mem_percent / 100)
    chunk_bytes = max(1 << 20, int(mem_limit * CHUNK_FRACTION))

    with open(src, "r", newline="", encoding="utf-8") as f:
        header_line = f.readline()
        first = next(csv.reader([f.readline()]))
    header = next(csv.reader([header_line]))
    key_idx = resolve_key(header, key)
    caster = detect_caster(first[key_idx])

    tmpdir = tempfile.mkdtemp(prefix="extsort_", dir=os.path.dirname(os.path.abspath(dst)))
    try:
        t0 = time.perf_counter()
        runs = split_phase(src, tmpdir, key_idx, caster, chunk_bytes)
        t1 = time.perf_counter()
        buf = int(min(1 << 20, max(64 << 10, mem_limit * 0.3 / max(1, len(runs)))))
        merge_phase(runs, dst, header_line, key_idx, caster, buf)
        t2 = time.perf_counter()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)     # удаление временных файлов

    return {"RUNS": len(runs), "SPLIT_SEC": t1 - t0, "MERGE_SEC": t2 - t1, "TOTAL_SEC": t2 - t0,
            "MEM_LIMIT_MB": mem_limit / 1024 / 1024, "PEAK_RSS_MB": peak_rss_mb()}


def main():
    ap = argparse.ArgumentParser(description="Внешняя сортировка CSV")
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--key", required=True, help="имя или номер (с 0) столбца")
    ap.add_argument("--mem-percent", type=float, default=10.0)
    a = ap.parse_args()
    res = external_sort(a.src, a.dst, a.key, a.mem_percent)
    for k, v in res.items():
        print(f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}")


if __name__ == "__main__":
    main()
