#!/bin/bash
set -e
# Lấy đường dẫn tuyệt đối của thư mục chứa script -> chạy được từ mọi nơi
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NS3DIR=/root/ns-allinone-3.44/ns-3.44
cp "$SRC/ecn-lan.cc" "$SRC/ecn-wan.cc" "$NS3DIR/scratch/"
cd "$NS3DIR"
cmake -S . -B build -G Ninja \
  -DNS3_BUILD_PROFILE=optimized \
  -DNS3_EXAMPLES=OFF \
  -DNS3_TESTS=OFF \
  -DNS3_ENABLED_MODULES="core;network;internet;applications;point-to-point;traffic-control;flow-monitor" 2>&1 | tail -4
ninja -C build 2>&1 | tail -6
echo BUILD_DONE
ls build/scratch/ | head -20
