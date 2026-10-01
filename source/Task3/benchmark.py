"""
Requirement 3: so sánh thời gian và không gian của UCS và A*.

Chạy:  python Task3/benchmark.py
       python Task3/benchmark.py --repeats 3 --timeout 120

Kết quả lưu trong results/: benchmark.csv, benchmark_table.txt, benchmark_*.png
"""
import argparse
import csv
import os
import sys
import tracemalloc

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from algorithms.ucs_astar import (  # noqa: E402
    SokobanProblem, SearchStats, ucs, a_star, calculate_heuristic)

MAP_DIR = os.path.join(HERE, "..", "maps")
OUT_DIR = os.path.join(HERE, "results")

# Xếp từ dễ đến khó
DEFAULT_MAPS = ["map_2", "map_3", "example_map"]  # dễ, trung bình, khó


def run_once(problem, algorithm, timeout, measure_memory=False):
    """Chạy 1 lần, trả về (path, cost, stats, peak_mem_kb)."""
    stats = SearchStats()
    if measure_memory:
        tracemalloc.start()
    if algorithm == "UCS":
        path, cost = ucs(problem, stats=stats, time_limit=timeout)
    else:
        path, cost = a_star(problem, calculate_heuristic, stats=stats, time_limit=timeout)
    peak = 0.0
    if measure_memory:
        peak = tracemalloc.get_traced_memory()[1] / 1024
        tracemalloc.stop()
    return path, cost, stats, peak


def run_map(name, repeats, timeout):
    path_file = os.path.join(MAP_DIR, f"{name}.txt")
    problem = SokobanProblem(path_file)
    rows = []
    for algorithm in ("UCS", "A*"):
        # Đo thời gian: chạy nhiều lần lấy trung bình (không bật tracemalloc vì làm chậm)
        times = []
        for _ in range(repeats):
            path, cost, stats, _ = run_once(problem, algorithm, timeout)
            times.append(stats.time_s)
            if stats.timed_out:
                break
        # Đo bộ nhớ: một lượt riêng
        peak = 0.0
        if not stats.timed_out:
            peak = run_once(problem, algorithm, timeout, measure_memory=True)[3]
        rows.append({
            "map": name,
            "algorithm": algorithm,
            "status": "timeout" if stats.timed_out else ("ok" if path is not None else "no solution"),
            "cost": cost if path is not None else "",
            "time_s": round(sum(times) / len(times), 4),
            "expanded": stats.expanded,
            "generated": stats.generated,
            "max_frontier": stats.max_frontier,
            "max_explored": stats.max_explored,
            "peak_mem_kb": round(peak, 1),
        })
    return rows


def print_table(rows):
    cols = ["map", "algorithm", "status", "cost", "time_s", "expanded",
            "generated", "max_frontier", "max_explored", "peak_mem_kb"]
    widths = {c: max(len(c), *(len(str(r[c])) for r in rows)) for c in cols}
    line = " | ".join(c.ljust(widths[c]) for c in cols)
    out = [line, "-+-".join("-" * widths[c] for c in cols)]
    for r in rows:
        out.append(" | ".join(str(r[c]).ljust(widths[c]) for c in cols))
    return "\n".join(out)


def make_charts(rows):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("Chưa cài matplotlib -> bỏ qua biểu đồ (pip install matplotlib)")
        return

    maps = list(dict.fromkeys(r["map"] for r in rows))
    metrics = [
        ("time_s", "Thời gian chạy (giây)", "benchmark_time.png"),
        ("expanded", "Số node đã mở rộng", "benchmark_expanded.png"),
        ("max_frontier", "Kích thước frontier tối đa", "benchmark_frontier.png"),
        ("peak_mem_kb", "Bộ nhớ đỉnh (KB)", "benchmark_memory.png"),
    ]
    # Dùng xám + hatch để in đen trắng vẫn phân biệt được
    colors = {"UCS": "0.35", "A*": "0.8"}
    hatches = {"UCS": "//", "A*": ".."}
    width = 0.38
    for key, title, fname in metrics:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        for i, alg in enumerate(("UCS", "A*")):
            vals = []
            for m in maps:
                r = next(x for x in rows if x["map"] == m and x["algorithm"] == alg)
                vals.append(max(float(r[key]), 1e-6))
            xs = [k + (i - 0.5) * width for k in range(len(maps))]
            ax.bar(xs, vals, width, label=alg, edgecolor="black",
                   color=colors[alg], hatch=hatches[alg])
        ax.set_xticks(range(len(maps)))
        ax.set_xticklabels(maps)
        ax.set_yscale("log")
        ax.set_title(title + " (thang log)")
        ax.set_xlabel("Bản đồ")
        ax.legend()
        ax.grid(axis="y", linestyle=":", alpha=0.6)
        fig.tight_layout()
        fig.savefig(os.path.join(OUT_DIR, fname), dpi=150)
        plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--maps", nargs="*", default=DEFAULT_MAPS, help="tên file map (không kèm .txt)")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--timeout", type=float, default=120)
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    all_rows = []
    for name in args.maps:
        print(f"Đang chạy {name} ...", flush=True)
        all_rows.extend(run_map(name, args.repeats, args.timeout))

    table = print_table(all_rows)
    print("\n" + table)

    with open(os.path.join(OUT_DIR, "benchmark_table.txt"), "w", encoding="utf-8") as f:
        f.write(table + "\n")
    with open(os.path.join(OUT_DIR, "benchmark.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        w.writeheader()
        w.writerows(all_rows)

    make_charts(all_rows)
    print(f"\nĐã lưu kết quả vào {os.path.abspath(OUT_DIR)}")


if __name__ == "__main__":
    main()
