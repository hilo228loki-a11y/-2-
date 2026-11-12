# Лабораторная 5.1 — внешняя сортировка

Предметная область: сотрудники (`id,name,city,age,salary,date`).

    g++ -O2 -std=c++17 external_sort.cpp -o external_sort      # (Windows: ... -o external_sort.exe)
    python generator.py 1100 data.csv                          # >1 ГБ
    python external_sort.py data.csv sorted.txt --key salary
    ./external_sort data.csv sorted.txt salary
    python gui.py                                              # GUI (нужен tkinter)

Ключ — имя столбца или номер (с 0). Лимит памяти = 10 % размера файла (`--mem-percent`).
