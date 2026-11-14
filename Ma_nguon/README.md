# Mã nguồn — Báo cáo Bài tập lớn: TCP and Explicit Congestion Notification (ECN)

**Bài báo:** Sally Floyd, *"TCP and Explicit Congestion Notification"*, ACM SIGCOMM Computer Communication Review, vol. 24, no. 5, pp. 8–23, 1994.

**Môn:** Đánh giá hiệu năng mạng — Tái hiện thí nghiệm bài báo trên ns-3.

**Sinh viên:** Trịnh Văn Sơn — 24022829 | **Giảng viên:** Thầy Đặng Minh Công

**Hạn nộp:** Trước 00:00 ngày 22/11/2026 (nộp sớm trước 15/11/2026 được +0.5 điểm).

---

## Cấu trúc gói nộp

```
Nop_bao_cao/
├── Bao_cao_ECN_Floyd_1994_Trịnh Văn Sơn _ 24022829.pdf   # Báo cáo chính (19 trang, 4 chương, 11 bảng, 3 biểu đồ)
├── Bao_cao_ECN_Floyd_1994_v2.docx                        # Bản Word (nguồn để chỉnh sửa / in ấn)
└── Ma_nguon/                                             # Thư mục này — toàn bộ mã nguồn & số liệu
    ├── README.md                 # Tài liệu này
    ├── ecn-lan.cc                # Kịch bản LAN (C++ / ns-3)
    ├── ecn-wan.cc                # Kịch bản WAN (C++ / ns-3)
    ├── build.sh                  # Cấu hình + biên dịch ns-3 với 2 kịch bản
    ├── smoke.sh                  # Kiểm tra nhanh 3 cấu hình (dt / red / ecn)
    ├── run_experiments.sh        # Sweep toàn bộ → CSV (48 LAN + 18 WAN runs)
    ├── plot_results.py           # Vẽ biểu đồ từ CSV
    ├── make_report.py            # Sinh báo cáo DOCX từ số liệu
    ├── make_slides.py            # Sinh slide thuyết trình PPTX
    └── ns3_results/              # Số liệu & biểu đồ thực nghiệm
        ├── lan_results.csv       # 48 lần chạy LAN
        ├── wan_results.csv       # 18 lần chạy WAN
        ├── lan_win64.png         # Biểu đồ LAN, cửa sổ 64 kB
        ├── lan_win8.png          # Biểu đồ LAN, cửa sổ 8 kB
        └── wan_results.png       # Biểu đồ WAN
```

## Đối chiếu với yêu cầu Bài tập lớn

| Yêu cầu (Hướng dẫn Bài tập lớn) | Nơi thực hiện |
|---|---|
| 1. Xác định ý tưởng chính của bài báo | Báo cáo — Chương 1 (1.1–1.2) |
| 2. Cải tiến / mô hình được đề xuất | Báo cáo — Chương 1 (1.4–1.6): ECN + RED, quy tắc phản hồi TCP |
| 3. Cài đặt mô hình trên ns-3 | `ecn-lan.cc`, `ecn-wan.cc` — Báo cáo Chương 2 |
| 4. Kiểm tra tính đúng đắn của chương trình & mô phỏng | `smoke.sh` + checklist ở Báo cáo Chương 2.5 |
| 5. Chạy thí nghiệm trên kịch bản và thu kết quả | `run_experiments.sh` → `ns3_results/*.csv` — Báo cáo Chương 3 |
| 6. So sánh với kết quả công bố và nhận xét | `plot_results.py` (biểu đồ) — Báo cáo Chương 3.3 và Chương 4 |

---

## Môi trường

- **ns-3.44** (ns-allinone), biên dịch bằng CMake + Ninja, GCC trên **Ubuntu 22.04 (WSL2)**.
- Python 3: `pandas`, `matplotlib` (vẽ biểu đồ), `python-docx`, `python-pptx` (sinh báo cáo/slide).
- 2 kịch bản dùng các module: `core;network;internet;applications;point-to-point;traffic-control;flow-monitor`.

## Cách chạy lại từ đầu

```bash
# 0) Cài công cụ biên dịch
sudo apt update && sudo apt install -y cmake ninja-build g++ python3 python3-pip
pip install pandas matplotlib python-docx python-pptx

# 1) Tải và giải nén ns-3.44
curl -sfL -O https://www.nsnam.org/releases/ns-allinone-3.44.tar.bz2
tar -xjf ns-allinone-3.44.tar.bz2
# ns3dir: <thư mục giải nén>/ns-allinone-3.44/ns-3.44

# 2) Biên dịch (tự động copy ecn-lan.cc, ecn-wan.cc vào scratch/ rồi build)
bash build.sh

# 3) Kiểm tra nhanh 3 cấu hình (DropTail / RED không ECN / RED+ECN)
bash smoke.sh

# 4) Sweep toàn bộ thí nghiệm: LAN 48 runs + WAN 18 runs (~25 phút)
#    Kết quả ghi vào /root/ecn-results/{lan,wan}_results.csv
bash run_experiments.sh

# 5) Vẽ biểu đồ từ CSV
python plot_results.py /root/ecn-results ./ns3_results

# 6) (Tuỳ chọn) Sinh lại báo cáo DOCX / slide PPTX từ số liệu mới
python make_report.py ./ns3_results     # -> Bao_cao_ECN_Floyd_1994_v2.docx (cùng thư mục)
python make_slides.py ./ns3_results     # -> Slide_thuyet_trinh_ECN_Floyd_1994.pptx
```

> `build.sh` và `smoke.sh` tự xác định đường dẫn thư mục chứa script, nên chạy được từ mọi vị trí.
> File ns-3 cần có quyền thực thi: `chmod +x *.sh`.
> **Lưu ý:** chạy `make_report.py` sẽ ghi đè file `Bao_cao_ECN_Floyd_1994_v2.docx` trong thư mục này.

### Chạy riêng lẻ 1 cấu hình

```bash
./build/scratch/ns3.44-ecn-lan-default --config=ecn --bufferKb=120 --winKb=64 --run=1
# --config: dt (DropTail) | red (RED không ECN) | ecn (RED + ECN)
# --bufferKb: 60|120|180|240   --winKb: 8|64   --run: seed
```

## Thiết kế thí nghiệm

**Kịch bản LAN** (`ecn-lan.cc`): 5 luồng BulkSend + 10 luồng Telnet qua nút chuyển có queue disc; 3 cấu hình (DropTail / RED / RED+ECN); sweep buffer 60–240 kB × cửa sổ 8–64 kB × 2 seed = **48 lần chạy**; ghi lại thông lượng, độ trễ telnet, gói rơi (qdrops) và CE marks.

**Kịch bản WAN** (`ecn-wan.cc`): đường truyền hai chiều, bottleneck 45 Mbps; 3 cấu hình × 3 buffer × 2 seed = **18 lần chạy**.

**Độ đúng đắn:** ECN được thương lượng qua SYN (`UseEcn = On`), số CE marks > 0 khi nghẽn, số gói rơi giảm tương ứng; số liệu được tổng hợp trung bình ± std theo 2 seed.

## Kết quả chính (LAN — toàn bộ 48 lần chạy, mỗi cấu hình trung bình 2 seed)

| Cấu hình | Thông lượng bulk | Trễ telnet TB | Trễ telnet cao nhất | Gói rơi | CE marks |
|---|---|---|---|---|---|
| DropTail | 99,1 Mbps (không đổi theo buffer) | 1,7–7,4 ms | tới 21 ms | 0–906 | 0 |
| RED không ECN | 53,7–99,1 Mbps (**sụt còn 54–87 Mbps** ở cửa sổ 64 kB) | 0,5–0,9 ms | tới 5 ms | 275–2.113 | 0 |
| **RED + ECN** | **97,9–99,1 Mbps** | **0,5–1,0 ms** | **tới 4 ms** | **1–141 (gần 0)** | 9k–170k |

→ **Khớp định tính với Floyd 1994:** ECN giữ nguyên thông lượng bulk, giảm trễ telnet và gần như loại bỏ rơi gói (thay bằng CE marks); RED không ECN đánh đổi bằng rơi gói khiến thông lượng sụt; DropTail trễ tăng theo buffer và trễ cực đại kém gấp nhiều lần.

## Ghi chú

- Số liệu là kiểm chứng **xu hướng** (NewReno + RFC 3168 + timer ns-3 hiện đại ≠ Reno 4.3 BSD + đồng hồ thô 1994) — báo cáo đã ghi rõ các khác biệt này.
- Muốn tăng độ tin cậy: thêm seed trong `run_experiments.sh` và chạy lại (~30 phút).
- Slide thuyết trình (`Slide_thuyet_trinh_ECN_Floyd_1994.pptx`) nộp riêng, không nằm trong gói này.
