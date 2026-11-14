#!/bin/bash
# run_experiments.sh — Sweep LAN + WAN cho báo cáo ECN (Floyd 1994)
# Chạy SAU khi build xong (build.sh). Gọi trực tiếp binary trong build/scratch.
set -e
NS3DIR=/root/ns-allinone-3.44/ns-3.44
OUT=/root/ecn-results
mkdir -p "$OUT"
LAN_CSV="$OUT/lan_results.csv"
WAN_CSV="$OUT/wan_results.csv"

LAN_BIN=$(find "$NS3DIR/build/scratch" -maxdepth 1 -type f -name "*ecn-lan*" | head -1)
WAN_BIN=$(find "$NS3DIR/build/scratch" -maxdepth 1 -type f -name "*ecn-wan*" | head -1)
echo "LAN_BIN=$LAN_BIN"
echo "WAN_BIN=$WAN_BIN"

echo "config,bufferKb,winKb,run,bulkTotalMbps,bulkMinMbps,telnetAvgDelayMs,telnetWorstDelayMs,qdrops,ceMarks,lost" > "$LAN_CSV"
echo "config,bufferKb,winKb,run,bulkTotalMbps,bulkMinMbps,telnetAvgDelayMs,telnetWorstDelayMs,qdrops,ceMarks,lost" > "$WAN_CSV"

echo "[LAN] 3 configs x 4 buffers x 2 windows x 2 runs = 48 runs (15s sim)"
for cfg in dt red ecn; do
  for buf in 60 120 180 240; do
    for win in 8 64; do
      for run in 1 2; do
        "$LAN_BIN" --config="$cfg" --bufferKb="$buf" --winKb="$win" --run="$run" --csv="$LAN_CSV" > /dev/null 2>&1 \
          || echo "FAIL lan $cfg $buf $win $run"
      done
    done
  done
done
echo "[LAN] done -> $LAN_CSV"
wc -l "$LAN_CSV"

echo "[WAN] 3 configs x 3 buffers x 2 runs = 18 runs (10s sim)"
for cfg in dt red ecn; do
  for buf in 60 120 240; do
    for run in 1 2; do
      "$WAN_BIN" --config="$cfg" --bufferKb="$buf" --winKb=64 --run="$run" --csv="$WAN_CSV" > /dev/null 2>&1 \
        || echo "FAIL wan $cfg $buf $run"
    done
  done
done
echo "[WAN] done -> $WAN_CSV"
wc -l "$WAN_CSV"
echo ALL_DONE
