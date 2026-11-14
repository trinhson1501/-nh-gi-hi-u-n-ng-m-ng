#!/bin/bash
# Lấy đường dẫn tuyệt đối của thư mục chứa script -> chạy được từ mọi nơi
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /root/ns-allinone-3.44/ns-3.44
cp "$SRC/ecn-lan.cc" "$SRC/ecn-wan.cc" scratch/
ninja -C build 2>&1 | tail -2
BIN=build/scratch
echo "=========== SMOKE: LAN RED+ECN (15s) ==========="
$BIN/ns3.44-ecn-lan-default --config=ecn --bufferKb=120 --winKb=64 --run=1
echo "=========== SMOKE: LAN DropTail (15s) ==========="
$BIN/ns3.44-ecn-lan-default --config=dt --bufferKb=120 --winKb=64 --run=1
echo "=========== SMOKE: LAN RED khong ECN (15s) ==========="
$BIN/ns3.44-ecn-lan-default --config=red --bufferKb=120 --winKb=64 --run=1
