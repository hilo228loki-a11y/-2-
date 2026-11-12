// Внешняя сортировка CSV (C++17, fstream).
// Сборка:  g++ -O2 -std=c++17 external_sort.cpp -o external_sort
// Запуск:  external_sort data.csv sorted.txt salary [mem_percent=10]
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

namespace fs = std::filesystem;
using Clock = std::chrono::steady_clock;

struct Key {
    double d = 0;      // числовое значение (если столбец числовой)
    std::string s;     // строковое значение (иначе)
};
static bool g_numeric = false;

static inline bool keyLess(const Key& a, const Key& b) {
    return g_numeric ? a.d < b.d : a.s < b.s;
}

static std::string getField(const std::string& line, size_t idx) {
    size_t start = 0;
    for (size_t i = 0; i < idx; ++i) {
        start = line.find(',', start);
        if (start == std::string::npos) return "";
        ++start;
    }
    size_t end = line.find(',', start);
    return line.substr(start, end == std::string::npos ? std::string::npos : end - start);
}

static Key makeKey(const std::string& line, size_t idx) {
    Key k;
    std::string f = getField(line, idx);
    if (g_numeric) k.d = std::strtod(f.c_str(), nullptr);
    else k.s = std::move(f);
    return k;
}

struct Item { Key key; std::string line; };
struct Node { Key key; std::string line; size_t run; };

int main(int argc, char** argv) {
    if (argc < 4) {
        std::cerr << "usage: external_sort <input> <output> <key name|index> [mem_percent]\n";
        return 1;
    }
    const std::string src = argv[1], dst = argv[2], keyArg = argv[3];
    const double memPercent = argc > 4 ? std::atof(argv[4]) : 10.0;

    const uintmax_t fileSize = fs::file_size(src);
    const size_t memLimit = static_cast<size_t>(fileSize * memPercent / 100.0);
    const size_t chunkBytes = std::max<size_t>(1 << 20, static_cast<size_t>(memLimit * 0.28));

    // ---- заголовок и определение ключа ----
    std::vector<char> inBuf(1 << 20);
    std::ifstream in;
    in.rdbuf()->pubsetbuf(inBuf.data(), inBuf.size());
    in.open(src, std::ios::binary);
    if (!in) { std::cerr << "cannot open " << src << "\n"; return 1; }

    std::string header, firstLine;
    std::getline(in, header);
    if (!header.empty() && header.back() == '\r') header.pop_back();
    std::getline(in, firstLine);

    size_t keyIdx = 0;
    {
        std::vector<std::string> cols;
        size_t p = 0;
        while (true) {
            size_t q = header.find(',', p);
            cols.push_back(header.substr(p, q == std::string::npos ? q : q - p));
            if (q == std::string::npos) break;
            p = q + 1;
        }
        auto it = std::find(cols.begin(), cols.end(), keyArg);
        if (it != cols.end()) keyIdx = it - cols.begin();
        else if (!keyArg.empty() && std::all_of(keyArg.begin(), keyArg.end(), ::isdigit) &&
                 std::stoul(keyArg) < cols.size()) keyIdx = std::stoul(keyArg);
        else { std::cerr << "key not found\n"; return 1; }
    }
    {
        std::string f = getField(firstLine, keyIdx);
        char* end = nullptr;
        std::strtod(f.c_str(), &end);
        g_numeric = !f.empty() && end && *end == '\0';
    }
    in.clear();
    in.seekg(0);
    std::getline(in, header);   // пропустить заголовок снова

    // ---- Фаза 1: разбиение на отсортированные серии ----
    std::vector<std::string> runs;
    auto t0 = Clock::now();
    {
        std::vector<Item> items;
        items.reserve(static_cast<size_t>(chunkBytes / (firstLine.size() + 1) * 1.1) + 16);  // без удвоений capacity
        std::vector<char> outBuf(1 << 20);
        std::string line;
        while (true) {
            items.clear();
            size_t bytes = 0;
            while (bytes < chunkBytes && std::getline(in, line)) {
                if (!line.empty() && line.back() == '\r') line.pop_back();
                if (line.empty()) continue;
                bytes += line.size() + 1;
                Item it;
                it.key = makeKey(line, keyIdx);
                it.line = std::move(line);
                items.push_back(std::move(it));
                line.clear();
            }
            if (items.empty()) break;
            std::sort(items.begin(), items.end(),
                      [](const Item& a, const Item& b) { return keyLess(a.key, b.key); });
            std::string name = dst + ".run" + std::to_string(runs.size()) + ".tmp";
            std::ofstream out;
            out.rdbuf()->pubsetbuf(outBuf.data(), outBuf.size());
            out.open(name, std::ios::binary);
            for (const auto& it : items) { out << it.line << '\n'; }
            out.close();
            runs.push_back(name);
        }
    }
    in.close();
    auto t1 = Clock::now();

    // ---- Фаза 2: k-путевое слияние ----
    {
        size_t bufSize = std::min<size_t>(1 << 20,
                           std::max<size_t>(64 << 10, memLimit * 0.3 / std::max<size_t>(1, runs.size())));
        struct Run { std::vector<char> buf; std::ifstream f; };
        std::vector<std::unique_ptr<Run>> rs;
        auto cmp = [](const Node& a, const Node& b) { return keyLess(b.key, a.key); };  // min-куча
        std::vector<Node> heap;
        for (size_t i = 0; i < runs.size(); ++i) {
            auto r = std::make_unique<Run>();
            r->buf.resize(bufSize);
            r->f.rdbuf()->pubsetbuf(r->buf.data(), r->buf.size());
            r->f.open(runs[i], std::ios::binary);
            std::string line;
            if (std::getline(r->f, line)) {
                heap.push_back({makeKey(line, keyIdx), std::move(line), i});
            }
            rs.push_back(std::move(r));
        }
        std::make_heap(heap.begin(), heap.end(), cmp);

        std::vector<char> outBuf(4 << 20);
        std::ofstream out;
        out.rdbuf()->pubsetbuf(outBuf.data(), outBuf.size());
        out.open(dst, std::ios::binary);
        out << header << '\n';
        std::string line;
        while (!heap.empty()) {
            std::pop_heap(heap.begin(), heap.end(), cmp);
            Node n = std::move(heap.back());
            heap.pop_back();
            out << n.line << '\n';
            if (std::getline(rs[n.run]->f, line)) {
                heap.push_back({makeKey(line, keyIdx), std::move(line), n.run});
                std::push_heap(heap.begin(), heap.end(), cmp);
                line.clear();
            }
        }
        out.close();
        for (auto& r : rs) r->f.close();
    }
    auto t2 = Clock::now();

    // ---- удаление временных файлов ----
    for (const auto& r : runs) std::remove(r.c_str());

    auto sec = [](Clock::time_point a, Clock::time_point b) {
        return std::chrono::duration<double>(b - a).count();
    };
    std::cout << std::fixed << std::setprecision(3)
              << "RUNS=" << runs.size() << "\n"
              << "SPLIT_SEC=" << sec(t0, t1) << "\n"
              << "MERGE_SEC=" << sec(t1, t2) << "\n"
              << "TOTAL_SEC=" << sec(t0, t2) << "\n"
              << "MEM_LIMIT_MB=" << memLimit / 1024.0 / 1024.0 << "\n";
    return 0;
}
