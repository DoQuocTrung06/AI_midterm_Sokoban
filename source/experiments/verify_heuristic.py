"""
Requirement 4: kiểm chứng bằng thực nghiệm tính admissible và consistent
của heuristic (calculate_heuristic: Chebyshev + phát hiện deadlock góc).

Chạy:  python experiments/verify_heuristic.py

Hai chế độ kiểm tra:

A) VÉT CẠN (map nhỏ): liệt kê toàn bộ trạng thái đạt được từ trạng thái đầu,
   tính chi phí tối ưu thật h*(s) của MỌI trạng thái bằng BFS ngược từ tập
   trạng thái đích, rồi kiểm tra:
     - Admissible : h(s) <= h*(s)   (và h(s) = inf  =>  h*(s) = inf)
     - Consistent : h(s) <= c(s,s') + h(s')  với MỌI cạnh (s -> s')

B) LẤY MẪU (map lớn, không vét cạn được):
     - Admissible : các trạng thái trên đường đi tối ưu do UCS tìm ra có
                    h*(s_i) = C* - i chính xác, kiểm tra h(s_i) <= C* - i.
     - Consistent : duyệt BFS tối đa N trạng thái từ trạng thái đầu và kiểm tra
                    mọi cạnh phát sinh.
"""
import argparse
import os
import sys
from collections import deque, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from algorithms.ucs_astar import SokobanProblem, ucs, calculate_heuristic  # noqa: E402

MAP_DIR = os.path.join(HERE, "..", "maps")
OUT_DIR = os.path.join(HERE, "..", "results")
INF = float("inf")


def load(name):
    return SokobanProblem(os.path.join(MAP_DIR, f"{name}.txt"))


# ---------------------------------------------------------------- A) vét cạn
def exhaustive_check(name, max_states):
    p = load(name)
    start = p.start_state
    edges = {}                       # state -> [(next_state, cost)]
    queue = deque([start])
    seen = {start}
    while queue:
        s = queue.popleft()
        succ = [(n, c) for n, _, c in p.get_successors(s)]
        edges[s] = succ
        for n, _ in succ:
            if n not in seen:
                if len(seen) >= max_states:
                    return {"map": name, "skipped": f"> {max_states} trạng thái"}
                seen.add(n)
                queue.append(n)

    # h* bằng BFS ngược (mọi cạnh có cost 1) từ các trạng thái đích
    reverse = defaultdict(list)
    for s, succ in edges.items():
        for n, c in succ:
            reverse[n].append((s, c))
    hstar = {}
    dq = deque()
    for s in edges:
        if p.is_goal(s):
            hstar[s] = 0
            dq.append(s)
    while dq:
        s = dq.popleft()
        for prev, c in reverse[s]:
            if prev not in hstar:
                hstar[prev] = hstar[s] + c
                dq.append(prev)

    h = {s: calculate_heuristic(s, p) for s in edges}

    adm_viol, sound_viol, cons_viol, n_edges = 0, 0, 0, 0
    worst_adm, worst_cons = None, None
    for s in edges:
        real = hstar.get(s, INF)
        if h[s] == INF:
            if real != INF:            # h báo deadlock nhưng thực ra còn giải được
                sound_viol += 1
        elif real != INF and h[s] > real:
            adm_viol += 1
            worst_adm = worst_adm or (s, h[s], real)
        for n, c in edges[s]:
            n_edges += 1
            if h[s] > c + h[n]:
                cons_viol += 1
                worst_cons = worst_cons or (s, n, h[s], c, h[n])

    solvable = sum(1 for s in edges if s in hstar)
    exact = sum(1 for s in edges if s in hstar and h[s] == hstar[s])
    return {
        "map": name, "mode": "vét cạn", "states": len(edges), "edges": n_edges,
        "solvable_states": solvable,
        "inf_states": sum(1 for s in edges if h[s] == INF),
        "admissible_violations": adm_viol,
        "deadlock_soundness_violations": sound_viol,
        "consistency_violations": cons_viol,
        "avg_h_over_hstar": round(sum(h[s] / hstar[s] for s in edges
                                      if s in hstar and hstar[s] > 0 and h[s] != INF)
                                  / max(1, sum(1 for s in edges if s in hstar and hstar[s] > 0)), 3),
        "exact_states": exact,
        "worst_adm": worst_adm, "worst_cons": worst_cons,
    }


# ---------------------------------------------------------------- B) lấy mẫu
def sampled_check(name, n_bfs, timeout):
    p = load(name)
    path, cost = ucs(p, time_limit=timeout)
    if path is None:
        return {"map": name, "skipped": "UCS không giải được trong thời gian cho phép"}

    # Admissible trên đường đi tối ưu: h*(s_i) = C* - i
    state = p.start_state
    total = cost
    adm_viol, checked = 0, 0
    worst = None
    for i, action in enumerate(path + [None]):
        hv = calculate_heuristic(state, p)
        real = total - i
        checked += 1
        if hv > real:
            adm_viol += 1
            worst = worst or (state, hv, real)
        if action is None:
            break
        state = next(n for n, a, _ in p.get_successors(state) if a == action)

    # Consistent trên N trạng thái đầu tiên của BFS
    start = p.start_state
    seen = {start}
    queue = deque([start])
    cons_viol, n_edges, worst_c = 0, 0, None
    while queue and len(seen) < n_bfs:
        s = queue.popleft()
        hs = calculate_heuristic(s, p)
        for n, _, c in p.get_successors(s):
            n_edges += 1
            hn = calculate_heuristic(n, p)
            if hs > c + hn:
                cons_viol += 1
                worst_c = worst_c or (s, n, hs, c, hn)
            if n not in seen:
                seen.add(n)
                queue.append(n)
    return {
        "map": name, "mode": "lấy mẫu", "optimal_cost": total,
        "path_states_checked": checked, "admissible_violations": adm_viol,
        "states": len(seen), "edges": n_edges, "consistency_violations": cons_viol,
        "worst_adm": worst, "worst_cons": worst_c,
    }


def fmt(r):
    if "skipped" in r:
        return f"[{r['map']}] bỏ qua: {r['skipped']}"
    lines = [f"[{r['map']}] chế độ: {r['mode']}"]
    for k, v in r.items():
        if k in ("map", "mode") or (k.startswith("worst") and v is None):
            continue
        lines.append(f"    {k}: {v}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exhaustive", nargs="*", default=["map_2", "map_3"])
    ap.add_argument("--sampled", nargs="*", default=["example_map"])
    ap.add_argument("--max-states", type=int, default=600_000)
    ap.add_argument("--bfs-states", type=int, default=100_000)
    ap.add_argument("--timeout", type=float, default=120)
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    results = []
    for name in args.exhaustive:
        print(f"Vét cạn {name} ...", flush=True)
        results.append(exhaustive_check(name, args.max_states))
    for name in args.sampled:
        print(f"Lấy mẫu {name} ...", flush=True)
        results.append(sampled_check(name, args.bfs_states, args.timeout))

    report = "\n\n".join(fmt(r) for r in results)
    bad = sum(r.get("admissible_violations", 0) + r.get("consistency_violations", 0)
              + r.get("deadlock_soundness_violations", 0) for r in results)
    report += "\n\n" + ("KẾT LUẬN: không có vi phạm nào -> heuristic admissible và consistent "
                        "trên tất cả dữ liệu đã kiểm tra."
                        if bad == 0 else f"KẾT LUẬN: phát hiện {bad} vi phạm, xem chi tiết ở trên.")
    print("\n" + report)
    with open(os.path.join(OUT_DIR, "heuristic_verification.txt"), "w", encoding="utf-8") as f:
        f.write(report + "\n")


if __name__ == "__main__":
    main()
