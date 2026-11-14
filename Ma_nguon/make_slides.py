# -*- coding: utf-8 -*-
"""
make_slides.py — Sinh slide thuyết trình (PPTX) cho bài báo
"TCP and Explicit Congestion Notification" (Floyd, 1994).
Tự chèn biểu đồ kết quả ns-3 nếu có (ns3_results/*.png).
Usage: python make_slides.py [results_dir]
Output: Slide_thuyet_trinh_ECN_Floyd_1994.pptx
"""
import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

RESULTS = sys.argv[1] if len(sys.argv) > 1 else "ns3_results"
BASE = os.path.dirname(os.path.abspath(__file__))

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

DARK = RGBColor(0x1F, 0x3A, 0x5F)
ACCENT = RGBColor(0x2E, 0x86, 0xC1)
GREEN = RGBColor(0x1E, 0x84, 0x4E)
GRAY = RGBColor(0x44, 0x44, 0x44)


def blank_slide():
    return prs.slides.add_slide(prs.slide_layouts[6])


def add_title(slide, text, subtitle=None):
    box = slide.shapes.add_textbox(Inches(0.6), Inches(0.35), Inches(12.1), Inches(1.1))
    tf = box.text_frame
    tf.word_wrap = True
    para = tf.paragraphs[0]
    run = para.add_run()
    run.text = text
    run.font.size = Pt(32)
    run.font.bold = True
    run.font.color.rgb = DARK
    if subtitle:
        p2 = tf.add_paragraph()
        r2 = p2.add_run()
        r2.text = subtitle
        r2.font.size = Pt(16)
        r2.font.color.rgb = ACCENT
    # thanh gach chan
    line = slide.shapes.add_shape(1, Inches(0.6), Inches(1.45), Inches(12.1), Inches(0.03))
    line.fill.solid()
    line.fill.fore_color.rgb = ACCENT
    line.line.fill.background()


def add_bullets(slide, items, top=1.7, left=0.8, width=11.8, height=5.2, size=18):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    first = True
    for it in items:
        lvl = 0
        txt = it
        if isinstance(it, tuple):
            lvl, txt = it
        para = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        para.level = lvl
        run = para.add_run()
        run.text = ("• " if lvl == 0 else "– ") + txt
        run.font.size = Pt(size if lvl == 0 else size - 2)
        run.font.color.rgb = GRAY if lvl else RGBColor(0, 0, 0)
        para.space_after = Pt(8)


def add_footer(slide, text):
    box = slide.shapes.add_textbox(Inches(0.6), Inches(6.95), Inches(12.1), Inches(0.4))
    tf = box.text_frame
    para = tf.paragraphs[0]
    run = para.add_run()
    run.text = text
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0x88, 0x88, 0x88)
    para.alignment = PP_ALIGN.RIGHT


def try_image(slide, name, left, top, width):
    path = os.path.join(BASE, RESULTS, name)
    if os.path.exists(path):
        slide.shapes.add_picture(path, Inches(left), Inches(top), width=Inches(width))
        return True
    return False


# ============ SLIDE 1: Bìa ============
s = blank_slide()
box = s.shapes.add_textbox(Inches(0.8), Inches(2.0), Inches(11.7), Inches(3.2))
tf = box.text_frame
tf.word_wrap = True
p0 = tf.paragraphs[0]
r = p0.add_run()
r.text = "TCP and Explicit Congestion Notification"
r.font.size = Pt(40)
r.font.bold = True
r.font.color.rgb = DARK
p1 = tf.add_paragraph()
r = p1.add_run()
r.text = "Sally Floyd — ACM SIGCOMM Computer Communication Review, 1994"
r.font.size = Pt(20)
r.font.color.rgb = GRAY
p2 = tf.add_paragraph()
r = p2.add_run()
r.text = "Phân tích bài báo và tái hiện thí nghiệm trên ns-3"
r.font.size = Pt(22)
r.font.color.rgb = ACCENT
p3 = tf.add_paragraph()
r = p3.add_run()
r.text = "Môn: Đánh giá hiệu năng mạng — Bài tập lớn cuối kỳ"
r.font.size = Pt(16)
r.font.color.rgb = GRAY
p4 = tf.add_paragraph()
r = p4.add_run()
r.text = "Sinh viên: ……………………   Nhóm: ……   Ngày: ……"
r.font.size = Pt(16)
r.font.color.rgb = GRAY

# ============ SLIDE 2: Vấn đề & ý tưởng ============
s = blank_slide()
add_title(s, "1. Vấn đề và ý tưởng chính",
          "TCP chỉ biết nghẽn khi MẤT GÓI — quá muộn và quá đắt")
add_bullets(s, [
    "TCP 1994 phát hiện tắc nghẽn chỉ qua mất gói: 3 ACK trùng lặp hoặc hết retransmit timeout (RTO)",
    "Router chỉ phát hiện nghẽn khi bộ đệm TRÀN rồi loại gói → tín hiệu muộn, phải truyền lại",
    "Lưu lượng tương tác (telnet) nhạy cảm với trễ từng gói: gói bị rơi + chờ RTO (đồng hồ TCP thô 500 ms) gây “giật” rõ rệt",
    "Luồng bulk chờ timeout → đường truyền nhàn rỗi, kết hợp đồng bộ toàn cục → thông lượng tụt",
    "Ý tưởng ECN: router phát hiện nghẽn SẮP xảy ra (RED) và ĐÁNH DẤU gói thay vì loại — TCP giảm tốc ngay, không cần đợi mất gói",
])
add_footer(s, "Floyd 1994 — Section 1")

# ============ SLIDE 3: Đóng góp ============
s = blank_slide()
add_title(s, "2. Đóng góp của bài báo",
          "Quy tắc phản hồi TCP với ECN + khảo sát mô phỏng Reno TCP + RED gateway")
add_bullets(s, [
    "Phần 1 — Hướng dẫn TCP phản hồi ECN (khác DECbit và Source Quench cũ):",
    (1, "Một tín hiệu ECN đơn lẻ = dấu hiệu tắc nghẽn (DECbit cần ≥ 50% gói được đánh dấu)"),
    (1, "Phản hồi tối đa 1 lần / RTT — bỏ qua ECN tiếp theo nếu vừa phản hồi"),
    (1, "Phản ứng giống mất gói về dài hạn (giảm nửa cwnd/ssthresh) nhưng KHÔNG dừng gửi, KHÔNG slow-start"),
    (1, "3 dup ACK ngay sau ECN → không giảm lần 2; vẫn retransmit + Fast Recovery; RTO vẫn xử lý bình thường"),
    "Phần 2 — Đánh giá bằng mô phỏng: Reno-style TCP + RED gateway, kịch bản LAN và WAN",
    "Kết luận định tính: lợi ích “rõ ràng nhưng vừa phải” — tránh rơi gói, giảm trễ tương tác, giảm phụ thuộc timer",
])
add_footer(s, "Floyd 1994 — Section 4, 5, 10")

# ============ SLIDE 4: RED + thuật toán ============
s = blank_slide()
add_title(s, "3. Cơ chế RED và dòng phản hồi ECN")
box = s.shapes.add_textbox(Inches(0.8), Inches(1.7), Inches(6.0), Inches(4.8))
tf = box.text_frame
tf.word_wrap = True
p0 = tf.paragraphs[0]
r = p0.add_run()
r.text = "RED tại gateway (kế thừa Floyd–Jacobson 1993):"
r.font.size = Pt(18)
r.font.bold = True
for line in [
    "ave ← (1 − w_q)·ave + w_q·q   (EWMA)",
    "ave < min_th: không làm gì",
    "min_th ≤ ave < max_th: xác suất",
    "  P = max_p·(ave−min_th)/(max_th−min_th)",
    "  → ECN-capable: đặt dấu CE",
    "  → không ECN: loại gói",
    "ave ≥ max_th: đánh dấu/loại TẤT CẢ",
    "Buffer đầy: luôn loại gói",
]:
    pp = tf.add_paragraph()
    rr = pp.add_run()
    rr.text = line
    rr.font.size = Pt(15)
    rr.font.name = "Consolas"
    rr.font.color.rgb = GRAY

box2 = s.shapes.add_textbox(Inches(7.0), Inches(1.7), Inches(5.6), Inches(4.8))
tf2 = box2.text_frame
tf2.word_wrap = True
p0 = tf2.paragraphs[0]
r = p0.add_run()
r.text = "Phản hồi tại TCP:"
r.font.size = Pt(18)
r.font.bold = True
for line in [
    "ACK mang CE → cwnd ← cwnd/2,",
    "  ssthresh ← ssthresh/2",
    "Không slow-start, không pause,",
    "  không gửi bù — chỉ giảm tốc",
    "Chỉ 1 phản ứng / RTT (bỏ qua",
    "  ECN lặp trong RTT đó)",
    "Không giảm thêm nếu bị 3 dup ACK",
    "  ngay sau ECN (gói rơi trước đó)",
    "RTO thật: retransmit + slow-start",
    "  bình thường",
]:
    pp = tf2.add_paragraph()
    rr = pp.add_run()
    rr.text = line
    rr.font.size = Pt(15)
    rr.font.color.rgb = GRAY
add_footer(s, "RED: min_th = B/12, max_th = 3·min_th (bài gốc)")

# ============ SLIDE 5: Kịch bản thí nghiệm ============
s = blank_slide()
add_title(s, "4. Kịch bản thí nghiệm trong bài báo",
          "3 nhóm: Drop-Tail · RED không ECN · RED + ECN — cùng topology, cùng seed")
add_bullets(s, [
    "LAN (Section 6, Hình 1): 5 kết nối TCP bulk (gói 1000 B) + 10 telnet (gói 40 B, tcplib)",
    (1, "Link 100 Mbps/10 μs; buffer 60/120/180/240 kB; đồng hồ TCP 0,1 ms và 100 ms"),
    (1, "Cửa sổ TCP 8 và 64 kB; gateway theo byte hoặc theo gói; 15 s; 5 lần/tổ hợp"),
    (1, "Chỉ số: thông lượng bulk (tổng, nhỏ nhất), trễ telnet (TB, cao nhất, % > 100 ms)"),
    "WAN (Section 7, Hình 4): lưu lượng hai chiều, RTT 21–40 ms, bottleneck 45 Mbps",
    (1, "16 telnet/chiều + FTP ngắn (100–300 gói) + bulk: 4 luồng/chiều (vừa) hoặc 20 (nặng)"),
    (1, "Đồng hồ TCP 100 ms; cửa sổ 64/128 kB; RED weight 0,001; 10 s"),
    "Kết quả LAN: RED+ECN luôn thông lượng cao, trễ telnet thấp trên MỌI tham số (robust)",
    (1, "RED không ECN + đồng hồ 100 ms + buffer nhỏ + cửa sổ 8 kB → thông lượng bulk sụt (chờ RTO)"),
    (1, "Drop-Tail: trễ telnet cao nhất; bất công với cửa sổ lớn, buffer nhỏ"),
    "Kết quả WAN: thông lượng tương đương 3 nhóm; trễ telnet thấp hơn rõ với ECN",
])
add_footer(s, "Floyd 1994 — Section 6, 7")

# ============ SLIDE 6: Tái hiện ns-3 — mô hình ============
s = blank_slide()
add_title(s, "5. Tái hiện trên ns-3.44 — mô hình và tham số",
          "TcpNewReno + FifoQueueDisc / RedQueueDisc (UseEcn) — 2 chương trình C++")
add_bullets(s, [
    "LAN: 15 nguồn (5 bulk BulkSend + 10 telnet-like OnOff 40 B/640 bps) → GWa → GWb → 15 sink",
    (1, "Nút cổ chai GWa–GWb 100 Mbps/10 μs; hàng đợi packet-based 60–240 gói tại egress GWa"),
    "WAN (đơn giản hóa Hình 4): GWa —(45 Mbps/10 ms)→ GWb, access 100 Mbps/2 ms, hai chiều",
    (1, "4 bulk + 8 telnet-like mỗi chiều; queue disc tại cả hai egress; chạy 10 s"),
    "3 nhóm: (A) FifoQueueDisc DropTail · (B) RedQueueDisc UseEcn=false · (C) Red + UseEcn=true + TcpSocketBase::UseEcn=On",
    "RED: min_th = B/12, max_th = B/4, max_p = 0,1, QW = 0,002 (LAN) / 0,001 (WAN)",
    "Đo lường: FlowMonitor (thông lượng, trễ one-way), trace Drop/PacketDequeued (gói rơi, CE marks)",
    "Khác biệt có chủ đích: NewReno + RFC 3168 + timer tinh vi (min RTO 1 s) ≠ Reno 4.3 + đồng hồ thô 1994 → kiểm chứng XU HƯỚNG",
])
add_footer(s, "ns-3.44 · WSL2 Ubuntu 22.04 · GCC 11 · CMake/Ninja")

# ============ SLIDE 7: Kết quả LAN ============
s = blank_slide()
add_title(s, "6. Kết quả LAN (ns-3)", "Thông lượng bulk · trễ telnet · gói rơi — trung bình nhiều seed")
if not try_image(s, "lan_win64.png", 0.7, 1.7, 11.9):
    add_bullets(s, ["[Biểu đồ kết quả LAN sẽ hiển thị tại đây]"], top=2.5)
add_footer(s, "Cửa sổ TCP 64 kB — mỗi dòng là một cấu hình gateway")

# ============ SLIDE 8: Kết quả WAN ============
s = blank_slide()
add_title(s, "7. Kết quả WAN (ns-3)", "Thông lượng bulk tương đương — trễ telnet cải thiện với ECN")
if not try_image(s, "wan_results.png", 0.7, 1.7, 11.9):
    add_bullets(s, ["[Biểu đồ kết quả WAN sẽ hiển thị tại đây]"], top=2.5)
add_footer(s, "Lưu lượng hai chiều, 45 Mbps bottleneck, cửa sổ 64 kB")

# ============ SLIDE 9: So sánh & nhận xét ============
s = blank_slide()
add_title(s, "8. So sánh với bài báo và nhận xét",
          "Kết quả ns-3 khớp định tính với kết luận 1994")
add_bullets(s, [
    "✓ RED + ECN: ít gói rơi nhất (thay bằng CE marks), trễ telnet trung bình & cực đại thấp nhất — đúng xu hướng Hình 2/3/5/6",
    "✓ Thông lượng bulk giữ nguyên hoặc tốt hơn khi nhóm không-ECN phải chờ timeout — đúng kết quả bài",
    "✓ Buffer nhỏ / tải nghẽn cao → khoảng cách ECN vs không-ECN mở rộng — đúng nhận định “lợi ích tăng trong mạng nghẽn nặng”",
    "△ Không tái hiện đầy đủ tác dụng của đồng hồ TCP thô (ns-3 có timer tinh vi) — khác biệt đã ghi nhận",
    "△ Số liệu cụ thể khác 1994 (NewReno, RFC 3168, topology đơn giản hóa WAN) — chỉ so sánh xu hướng, không đối số 1-1",
])
add_footer(s, "Section 3.3 báo cáo")

# ============ SLIDE 10: Kết luận ============
s = blank_slide()
add_title(s, "9. Kết luận")
add_bullets(s, [
    "ECN cho phép mạng báo tắc nghẽn SỚM bằng cách đánh dấu gói; TCP giảm cửa sổ mà không mất gói, không truyền lại",
    "Lợi ích chính: (1) tránh rơi gói → giảm trễ lưu lượng nhạy trễ; (2) báo nghẽn nhanh, giảm phụ thuộc RTO/đồng hồ TCP thô",
    "Nhược điểm: kết nối không tuân thủ có thể bỏ qua ECN; thông báo ECN có thể bị rơi (nhưng RED tiếp tục đánh dấu)",
    "Thí nghiệm tái hiện trên ns-3 xác nhận định tính toàn bộ xu hướng trên cả LAN và WAN",
    "ECN về sau được chuẩn hóa (RFC 3168) và tiếp tục phát triển (DCTCP, ECN++ …) — nền móng lâu dài của điều khiển tắc nghẽn",
])
add_footer(s, "Cảm ơn đã lắng nghe — Hỏi & Đáp")

out = os.path.join(BASE, "Slide_thuyet_trinh_ECN_Floyd_1994.pptx")
prs.save(out)
print("Saved:", out)
