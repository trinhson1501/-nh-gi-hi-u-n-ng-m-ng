# -*- coding: utf-8 -*-
"""
plot_results.py — Vẽ biểu đồ từ CSV kết quả ns-3 (ecn-lan.csv / ecn-wan.csv)
Đầu ra: lan_throughput.png, lan_delay.png, wan_throughput.png, wan_delay.png ...
Usage: python plot_results.py <results_dir> <out_dir>
"""
import sys
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

results_dir = sys.argv[1] if len(sys.argv) > 1 else "."
out_dir = sys.argv[2] if len(sys.argv) > 2 else "."
os.makedirs(out_dir, exist_ok=True)

LABELS = {"dt": "DropTail", "red": "RED (không ECN)", "ecn": "RED + ECN"}
COLORS = {"dt": "#d62728", "red": "#ff7f0e", "ecn": "#2ca02c"}
MARKERS = {"dt": "s", "red": "o", "ecn": "^"}


def load(name):
    path = os.path.join(results_dir, name)
    df = pd.read_csv(path)
    # Gộp các run (seed) -> trung bình ± std
    agg = df.groupby(["config", "bufferKb", "winKb"]).agg(
        bulkMean=("bulkTotalMbps", "mean"),
        bulkStd=("bulkTotalMbps", "std"),
        bulkMinMean=("bulkMinMbps", "mean"),
        telnetAvgDelay=("telnetAvgDelayMs", "mean"),
        telnetWorstDelay=("telnetWorstDelayMs", "mean"),
        drops=("qdrops", "mean"),
        marks=("ceMarks", "mean"),
    ).reset_index()
    return df, agg


def plot_lan():
    df, agg = load("lan_results.csv")
    for win in sorted(agg["winKb"].unique()):
        sub = agg[agg["winKb"] == win]
        fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
        for cfg in ["dt", "red", "ecn"]:
            s = sub[sub["config"] == cfg].sort_values("bufferKb")
            if s.empty:
                continue
            axes[0].errorbar(s["bufferKb"], s["bulkMean"], yerr=s["bulkStd"].fillna(0),
                             color=COLORS[cfg], marker=MARKERS[cfg], label=LABELS[cfg], capsize=3)
            axes[1].plot(s["bufferKb"], s["telnetAvgDelay"], color=COLORS[cfg],
                         marker=MARKERS[cfg], label=LABELS[cfg])
            axes[1].plot(s["bufferKb"], s["telnetWorstDelay"], color=COLORS[cfg],
                         marker=MARKERS[cfg], linestyle="--", alpha=0.5)
            axes[2].bar(s["bufferKb"] + (["dt", "red", "ecn"].index(cfg) - 1) * 12,
                        s["drops"], width=10, color=COLORS[cfg], label=LABELS[cfg])
        axes[0].set_title("Thông lượng bulk tổng (LAN)")
        axes[0].set_ylabel("Mbps"); axes[0].set_xlabel("Buffer (kB)")
        axes[0].legend(); axes[0].grid(alpha=0.3)
        axes[1].set_title("Độ trễ telnet (đậm: TB, nhạt: cao nhất)")
        axes[1].set_ylabel("ms (log)"); axes[1].set_xlabel("Buffer (kB)")
        axes[1].set_yscale("log"); axes[1].legend(); axes[1].grid(alpha=0.3)
        axes[2].set_title("Gói rơi tại queue disc")
        axes[2].set_ylabel("Số gói"); axes[2].set_xlabel("Buffer (kB)")
        axes[2].legend(); axes[2].grid(alpha=0.3)
        fig.suptitle(f"Kịch bản LAN — cửa sổ TCP = {win} kB (ns-3, trung bình 2 seed)")
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, f"lan_win{win}.png"), dpi=130)
        plt.close(fig)
    print("Saved lan_win*.png")


def plot_wan():
    df, agg = load("wan_results.csv")
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
    for cfg in ["dt", "red", "ecn"]:
        s = agg[agg["config"] == cfg].sort_values("bufferKb")
        if s.empty:
            continue
        axes[0].errorbar(s["bufferKb"], s["bulkMean"], yerr=s["bulkStd"].fillna(0),
                         color=COLORS[cfg], marker=MARKERS[cfg], label=LABELS[cfg], capsize=3)
        axes[1].plot(s["bufferKb"], s["telnetAvgDelay"], color=COLORS[cfg],
                     marker=MARKERS[cfg], label=LABELS[cfg])
        axes[1].plot(s["bufferKb"], s["telnetWorstDelay"], color=COLORS[cfg],
                     marker=MARKERS[cfg], linestyle="--", alpha=0.5)
        axes[2].bar(s["bufferKb"] + (["dt", "red", "ecn"].index(cfg) - 1) * 8,
                    s["drops"], width=6, color=COLORS[cfg], label=LABELS[cfg])
    axes[0].set_title("Thông lượng bulk tổng (WAN)")
    axes[0].set_ylabel("Mbps"); axes[0].set_xlabel("Buffer (kB)")
    axes[0].legend(); axes[0].grid(alpha=0.3)
    axes[1].set_title("Độ trễ telnet (đậm: TB, nhạt: cao nhất)")
    axes[1].set_ylabel("ms (log)"); axes[1].set_xlabel("Buffer (kB)")
    axes[1].set_yscale("log"); axes[1].legend(); axes[1].grid(alpha=0.3)
    axes[2].set_title("Gói rơi tại queue disc")
    axes[2].set_ylabel("Số gói"); axes[2].set_xlabel("Buffer (kB)")
    axes[2].legend(); axes[2].grid(alpha=0.3)
    fig.suptitle("Kịch bản WAN — cửa sổ TCP = 64 kB (ns-3, trung bình 2 seed)")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "wan_results.png"), dpi=130)
    plt.close(fig)
    print("Saved wan_results.png")


if __name__ == "__main__":
    plot_lan()
    plot_wan()
