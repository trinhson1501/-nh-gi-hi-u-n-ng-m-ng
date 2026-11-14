# -*- coding: utf-8 -*-
"""
make_report.py — Sinh báo cáo DOCX mở rộng: "TCP and Explicit Congestion Notification"
Tự động chèn bảng số liệu từ CSV kết quả ns-3 (nếu có) và biểu đồ PNG.
Usage: python make_report.py [results_dir]
Outputs: Bao_cao_ECN_Floyd_1994_v2.docx
"""
import os
import sys
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

RESULTS = sys.argv[1] if len(sys.argv) > 1 else "ns3_results"
BASE = os.path.dirname(os.path.abspath(__file__))

doc = Document()

# ---------- style cơ bản ----------
style = doc.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(13)
style.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
style.paragraph_format.line_spacing = 1.5

for h in ["Heading 1", "Heading 2", "Heading 3", "Title", "Subtitle"]:
    try:
        s = doc.styles[h]
        s.font.name = "Times New Roman"
        s.font.color.rgb = RGBColor(0, 0, 0)
        s.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    except KeyError:
        pass
doc.styles["Heading 1"].font.size = Pt(16)
doc.styles["Heading 1"].font.bold = True
doc.styles["Heading 2"].font.size = Pt(14)
doc.styles["Heading 2"].font.bold = True
doc.styles["Heading 3"].font.size = Pt(13)
doc.styles["Heading 3"].font.bold = True


def p(text, bold=False, italic=False, align=None, size=None):
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.bold = bold
    run.italic = italic
    if size:
        run.font.size = Pt(size)
    if align == "center":
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return para


def bullets(items, style_name="List Bullet"):
    for it in items:
        doc.add_paragraph(it, style=style_name)


def code_block(text):
    para = doc.add_paragraph()
    run = para.add_run(text)
    run.font.name = "Consolas"
    run.font.size = Pt(10.5)
    para.paragraph_format.line_spacing = 1.0
    para.paragraph_format.space_before = Pt(6)
    para.paragraph_format.space_after = Pt(6)
    return para


def add_table(headers, rows, caption=None):
    if caption:
        cap = doc.add_paragraph()
        r = cap.add_run(caption)
        r.bold = True
        r.font.size = Pt(12)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(headers):
        cell = t.rows[0].cells[j]
        cell.text = str(h)
        for par in cell.paragraphs:
            for run in par.runs:
                run.bold = True
                run.font.size = Pt(11)
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            cell = t.rows[i + 1].cells[j]
            cell.text = str(v)
            for par in cell.paragraphs:
                for run in par.runs:
                    run.font.size = Pt(11)
    doc.add_paragraph()
    return t


def try_picture(path, width=6.2, caption=None):
    full = os.path.join(BASE, path)
    if os.path.exists(full):
        doc.add_picture(full, width=Inches(width))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        if caption:
            cap = doc.add_paragraph()
            r = cap.add_run(caption)
            r.italic = True
            r.font.size = Pt(11)
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        return True
    return False


def load_agg(name):
    import pandas as pd
    path = os.path.join(BASE, RESULTS, name)
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    return df.groupby(["config", "bufferKb", "winKb"]).agg(
        bulk=("bulkTotalMbps", "mean"), bulkStd=("bulkTotalMbps", "std"),
        bulkMin=("bulkMinMbps", "mean"),
        dAvg=("telnetAvgDelayMs", "mean"), dWorst=("telnetWorstDelayMs", "mean"),
        drops=("qdrops", "mean"), marks=("ceMarks", "mean"),
    ).reset_index()


def fmt(v, nd=2):
    try:
        if v is None or (isinstance(v, float) and v != v):
            return "—"
        return f"{v:.{nd}f}"
    except Exception:
        return "—"


CFGL = [("dt", "DropTail"), ("red", "RED (không ECN)"), ("ecn", "RED + ECN")]

# ===================== TRANG BÌA =====================
for _ in range(3):
    doc.add_paragraph()
p("ĐẠI HỌC …… KHOA CÔNG NGHỆ THÔNG TIN", bold=True, align="center", size=14)
p("MÔN HỌC: ĐÁNH GIÁ HIỆU NĂNG MẠNG", bold=True, align="center", size=14)
for _ in range(2):
    doc.add_paragraph()
p("BÁO CÁO BÀI TẬP LỚN CUỐI KỲ", bold=True, align="center", size=18)
doc.add_paragraph()
p("TCP and Explicit Congestion Notification", bold=True, align="center", size=17)
p("Sally Floyd — ACM SIGCOMM Computer Communication Review, 1994", align="center", size=13)
p("Phân tích bài báo và tái hiện thí nghiệm trên ns-3", italic=True, align="center", size=13)
for _ in range(4):
    doc.add_paragraph()
p("Sinh viên: ……………………………", align="center")
p("MSSV: …………………………………", align="center")
p("Nhóm: …………………………………", align="center")
p("Giảng viên hướng dẫn: ………………", align="center")
import datetime
p("Hà Nội, " + datetime.date.today().strftime("%d/%m/%Y"), align="center")
doc.add_page_break()

# ===================== MỤC LỤC =====================
doc.add_heading("MỤC LỤC", level=1)
toc = [
    "Chương 1. Phân tích bài báo",
    "   1.1 Thông tin bài báo và ý tưởng chính",
    "   1.2 Bài toán đặt ra và tầm quan trọng",
    "   1.3 Giới hạn của các phương pháp trước đó",
    "   1.4 Giải pháp đề xuất: cơ chế ECN và quy tắc phản hồi TCP",
    "   1.5 Công thức và thuật toán cốt lõi (RED và phản hồi TCP)",
    "   1.6 Phương pháp thí nghiệm của bài báo",
    "   1.7 Kết quả công bố và kết luận của tác giả",
    "Chương 2. Tái hiện thí nghiệm trên ns-3",
    "   2.1 Môi trường và công cụ",
    "   2.2 Mô hình topology và tham số",
    "   2.3 Ba nhóm thí nghiệm",
    "   2.4 Mã nguồn chính",
    "   2.5 Kiểm tra tính đúng đắn của chương trình và mô phỏng",
    "Chương 3. Kết quả thực nghiệm và so sánh",
    "   3.1 Kết quả kịch bản LAN",
    "   3.2 Kết quả kịch bản WAN",
    "   3.3 So sánh với bài báo và nhận xét",
    "Chương 4. Nhận xét và kết luận",
    "Tài liệu tham khảo",
    "Phụ lục. Cách chạy lại thí nghiệm",
]
for line in toc:
    para = doc.add_paragraph()
    run = para.add_run(line)
    run.font.size = Pt(12)
    para.paragraph_format.line_spacing = 1.3
doc.add_page_break()

# ===================== CHƯƠNG 1 =====================
doc.add_heading("Chương 1. Phân tích bài báo", level=1)

doc.add_heading("1.1 Thông tin bài báo và ý tưởng chính", level=2)
p("Bài báo “TCP and Explicit Congestion Notification” của Sally Floyd (Lawrence Berkeley "
  "Laboratory) đăng trên ACM SIGCOMM Computer Communication Review, tháng 10 năm 1994 "
  "(vol. 24, số 5, trang 8–23). Đây là một trong những công trình đặt nền móng cho cơ chế "
  "ECN trong TCP/IP, về sau được chuẩn hóa trong RFC 3168 (2001).")
p("Ý tưởng chính: thay vì chỉ báo tắc nghẽn gián tiếp bằng cách để mất gói, mạng có thể "
  "báo tắc nghẽn “sớm và rõ ràng” (explicit) bằng cách đánh dấu gói tin ngay tại router "
  "trước khi bộ đệm tràn. Đầu TCP phản hồi bằng cách giảm cửa sổ chặn (congestion window) "
  "mà không cần đợi mất gói và truyền lại. Bài báo có hai phần đóng góp: (1) đề xuất hướng "
  "dẫn (guidelines) cho cách TCP phản hồi tín hiệu ECN; (2) đánh giá, khảo sát lợi ích và "
  "hạn chế của ECN bằng mô phỏng với Reno-style TCP và gateway RED.")

doc.add_heading("1.2 Bài toán đặt ra và tầm quan trọng", level=2)
p("Trong TCP/IP thời điểm 1994, TCP chỉ suy ra tắc nghẽn từ sự kiện mất gói: nhận ba ACK "
  "trùng lặp (Fast Retransmit) hoặc hết thời gian retransmission timeout (RTO). Router "
  "thông thường chỉ phát hiện nghẽn khi bộ đệm tràn và loại gói. Điều này gây ra several "
  "vấn đề:")
bullets([
    "Tín hiệu đến muộn: phải mất một RTT (Fast Retransmit) hoặc vài lần RTO để phát hiện mất gói, trong khi đó đường truyền có thể bị lãng phí hoặc hàng đợi tiếp tục đầy lên.",
    "Mất gói không cần thiết: khi RED hoặc cơ chế nào đó biết trước nghẽn đang hình thành, việc loại gói chỉ là một cách báo nghẽn “cứng”, gây truyền lại và tăng trễ cho các gói còn lại trong hàng đợi.",
    "Ảnh hưởng không đều tới các loại lưu lượng: luồng bulk-data chỉ quan tâm thời gian hoàn thành tệp; còn lưu lượng tương tác (telnet) nhạy cảm với trễ của từng gói — gói bị rơi rồi truyền lại gây “giật” rõ rệt cho người dùng.",
    "Phụ thuộc độ thô của đồng hồ TCP: với các triển khai TCP dùng đồng hồ đo thời gian 500 ms, RTO tối thiểu rất lớn; gói telnet bị rơi có thể khiến kết nối đứng chờ hàng giây, đặc biệt tệ trên LAN.",
])
p("Vì vậy, câu hỏi đặt ra: nếu router có khả năng phát hiện nghẽn sắp xảy ra (như RED, "
  "DECbit), ta nên dùng cơ chế báo nghẽn nào và TCP nên phản ứng ra sao để giảm thiểu tổn "
  "thất mà vẫn ổn định và công bằng?")

doc.add_heading("1.3 Giới hạn của các phương pháp trước đó", level=2)
bullets([
    "Báo nghẽn bằng mất gói: gián tiếp và chậm. Khi hàng đợi FIFO phải loại xác suất p gói để điều khiển nghẽn, các gói telnet nhỏ bị loại với cùng xác suất như gói bulk lớn — vô lý vì telnet không phải nguồn gây nghẽn.",
    "ICMP Source Quench: đã tồn tại nhưng “rarely used”. Draft Requirements for IP Routers (1994) còn phê bình: tiêu tốn băng thông trong lúc nghẽn (router phải gửi thông báo mới khi mạng đang đầy), kém hiệu quả và không công bằng. Phản hồi theo hướng dẫn cũ (RFC 1009):gây ra slow-start như timeout, đặt ssthresh về 1–2 segment — quá khắc nghiệt với cửa sổ lớn ở tốc độ cao.",
    "DECbit (Ramakrishnan–Jain 1990): dùng bit báo nghẽn trong header, router đặt bit khi hàng đợi trung bình > 1; nguồn chỉ phản ứng khi ≥ nửa số gói trong cửa sổ trước có bit báo — phản hồi chậm hơn so với “một thông báo đơn lẻ” mà Floyd đề xuất.",
    "Các cơ chế FECN/BECN trong ATM: theo hướng rate-based, khác mô hình cửa sổ của TCP.",
])

doc.add_heading("1.4 Giải pháp đề xuất: cơ chế ECN và quy tắc phản hồi TCP", level=2)
p("Bài báo đề xuất một tập hướng dẫn (guidelines) cho cách TCP phản hồi các tín hiệu ECN "
  "(Source Quench hoặc bit ECN trong header). Điểm khác biệt cốt lõi so với DECbit: chỉ "
  "một thông báo ECN đơn lẻ cũng đủ để kích hoạt phản ứng tắc nghẽn. Nguyên tắc dài hạn: "
  "phản ứng của TCP với ECN nên giống phản ứng với mất gói; nhưng trong thang thời gian "
  "ngắn (1–2 RTT), TCP có thể phản ứng “mềm” hơn vì ECN không báo tràn bộ đệm — không "
  "cần dừng gửi, không cần slow-start.")
p("Cụ thể, các hướng dẫn gồm:")
bullets([
    "Một thông báo ECN đơn lẻ (một Source Quench hoặc một gói data mang bit ECN) được xem là tín hiệu tắc nghẽn.",
    "TCP phản hồi ECN tối đa một lần mỗi RTT: bỏ qua các ECN kế tiếp nếu trong RTT gần nhất TCP đã phản hồi ECN hoặc đã xử lý mất gói. Nếu ngay sau khi phản ứng ECN mà nhận 3 duplicate ACK, TCP KHÔNG giảm cửa sổ lần nữa (gói đó có thể đã bị loại trước khi nguồn giảm window), nhưng vẫn retransmit và vào Fast Recovery.",
    "Phản ứng với ECN: giảm nửa cwnd và ssthresh; không slow-start, không gửi bù, không phát sinh gói mới. TCP tiếp tục gửi dữ liệu theo ACK bình thường.",
    "Nếu RTO thật sự xảy ra: vẫn retransmit và slow-start theo quy trình timeout, nhưng không hạ ssthresh thêm lần nữa nếu đã hạ trong RTT vừa qua.",
])
p("Về phía router: bài báo dùng gateway RED (Floyd–Jacobson 1993) làm cơ chế phát hiện "
  "nghẽn sớm. RED ước lượng hàng đợi trung bình theo hàm trung bình hàm mũ (EWMA); khi "
  "hàng đợi vượt ngưỡng thấp, RED chọn xác suất để báo hiệu; nếu đầu gửi/router hỗ trợ "
  "ECN thì ĐÁNH DẤU gói (đặt bit ECN) thay vì loại. Khi bộ đệm thực sự đầy, RED vẫn loại "
  "gói như bình thường. Nhờ đánh dấu xác suất tỉ lệ với thị phần băng thông, RED giảm "
  "đồng bộ toàn cục và tăng công bằng. Bài báo không nhằm mục tiêu cải tiến thuật toán RED "
  "mà kế thừa nó.")

doc.add_heading("1.5 Công thức và thuật toán cốt lõi", level=2)
p("RED (kế thừa từ [FJ93]) — gateway tính hàng đợi trung bình EWMA và xác suất báo hiệu:")
code_block(
    "ave <- (1 - w_q) * ave + w_q * q                  # w_q: trọng số EWMA (QW)\n"
    "if  ave < min_th:      khong lam gi\n"
    "if  min_th <= ave < max_th:\n"
    "    P_b = max_p * (ave - min_th) / (max_th - min_th)   # xac suat 'tinh' bao hieu\n"
    "    P_a = P_b / (1 - q * P_b)                          # xac suat hieu dung\n"
    "    voi xac suat P_a:  ECN-capable -> dat dau CE ; nguoc lai -> loai goi\n"
    "if  ave >= max_th:     danh dau / loai TAT CA goi den\n"
    "if  hang doi day (full buffer): luon loai goi den")
p("Phản hồi của TCP Reno với ECN (mô tả thủ tục trong simulator của bài):")
code_block(
    "nhan ACK mang bit ECN (thong bao nghet), khi trong ~RTT vua qua chua phan ung:\n"
    "    cwnd    <- cwnd / 2\n"
    "    ssthresh <- ssthresh / 2\n"
    "    khong slow-start; khong gui goi moi; bo qua ECN tiep den cho den khi\n"
    "    tat ca goi outstanding luc do duoc ACK (toi da 1 lan/RTT)\n"
    "nhan 3 duplicate ACK ngay sau phan ung ECN:\n"
    "    khong giam cwnd/ssthresh nua; retransmit goi bi mat; Fast Recovery\n"
    "nhan RTO (timeout):\n"
    "    retransmit + slow-start binh thuong; khong ha ssthresh neu vua ha trong RTT")
add_table(
    ["Thành phần", "Cách hoạt động"],
    [
        ["Phát hiện nghẽn", "RED tính hàng đợi trung bình EWMA; khi nghẽn sắp xảy ra, xác suất báo hiệu tăng tuyến tính từ min_th đến max_th."],
        ["Báo hiệu", "ECN: gateway đặt bit CE trong header gói (đầu nhận echo trong ACK); không ECN: gateway loại gói với xác suất tương ứng."],
        ["Phản hồi", "Đầu gửi giảm nửa cwnd/ssthresh tối đa 1 lần/RTT, không cần dừng gửi, không slow-start."],
        ["Mục tiêu", "Giảm rơi gói và truyền lại không cần thiết; giảm trễ lưu lượng nhạy trễ; giảm phụ thuộc retransmit timer."],
    ],
    caption="Bảng 1.1: Tóm tắt cơ chế RED + ECN")

doc.add_heading("1.6 Phương pháp thí nghiệm của bài báo", level=2)
p("Bài báo mô phỏng hai nhóm kịch bản (mô phỏng tùy chỉnh theo phong cách Berkeley "
  "ns, không phải ns-3 ngày nay), mỗi tổ hợp tham số chạy 5 lần và lấy trung bình. Ba "
  "nhóm so sánh: (1) Drop-Tail gateway, (2) RED không ECN, (3) RED có ECN (cả gateway "
  "và TCP đều hỗ trợ ECN).")
add_table(
    ["Hạng mục", "Kịch bản LAN (Section 6)", "Kịch bản WAN (Section 7)"],
    [
        ["Topology", "5 nguồn → 1 gateway nghẽn → receiver; link 100 Mbps, 10 μs (Hình 1)",
         "Hai chiều, 2 gateway A–B; link 45 Mbps và 100 Mbps, delay 0,5–10 ms; RTT 21–40 ms (Hình 4)"],
        ["Lưu lượng", "5 kết nối TCP bulk (gói 1000 B) + 10 kết nối telnet (gói 40 B, phân phối tcplib); telnet start rải trong 15 s",
         "16 telnet/chiều; FTP thỉnh thoảng (100–300 gói); bulk không giới hạn: 4 luồng/chiều (tải vừa) hoặc 20 luồng/chiều (tải nặng)"],
        ["Cửa sổ TCP", "Tối đa 8 kB và 64 kB", "64 kB và 128 kB"],
        ["Đồng hồ TCP", "0,1 ms và 100 ms; RTO ban đầu 3 s", "100 ms"],
        ["Buffer switch", "60, 120, 180, 240 kB", "Biến thiên theo trục x của đồ thị (0–240 kB)"],
        ["RED", "min_th = buffer/12; max_th = 3×min_th; drop-all khi ave > max_th",
         "Như LAN nhưng hằng số bộ lọc giảm 0,002 → 0,001 (phù hợp WAN)"],
        ["Kiểu đếm", "Gateway theo byte hoặc theo gói (packet-based)",
         "Gateway theo byte hoặc theo gói"],
        ["Chỉ số", "Thông lượng bulk tổng & nhỏ nhất; trễ telnet cao nhất, trung bình; % gói telnet trễ > 100 ms",
         "Thông lượng bulk tổng & nhỏ nhất; trễ telnet TB/cao nhất; thông lượng kết nối ngắn"],
        ["Thời gian", "15 s mỗi lượt chạy", "10 s mỗi lượt chạy"],
    ],
    caption="Bảng 1.2: Thiết lập thí nghiệm trong bài báo")

doc.add_heading("1.7 Kết quả công bố và kết luận của tác giả", level=2)
p("Kết quả LAN (Hình 2 và 3 của bài):")
bullets([
    "RED + ECN: trên toàn bộ dải tham số (buffer, cửa sổ, kiểu gateway, đồng hồ TCP), thông lượng bulk luôn cao và trễ telnet luôn thấp — hiệu năng “robust”, gần như tối ưu.",
    "RED không ECN: phụ thuộc tham số. Với đồng hồ TCP thô 100 ms, buffer nhỏ và cửa sổ 8 kB, thông lượng bulk bị giảm rõ: nhiều kết nối phải chờ RTO khiến link nhàn rỗi.",
    "Drop-Tail: trễ telnet cao nhất; với cửa sổ lớn có hiện tượng bất công (luồng bulk kém nhất có thông lượng thấp hơn mức tối ưu ở buffer nhỏ).",
    "Gateway theo byte (không thực tế) giúp gói telnet 40 B ít bị loại hơn; gateway packet-based — loại theo xác suất độc lập kích thước gói — là kiểu thực tế và là bối cảnh ECN phát huy lợi ích.",
])
p("Kết quả WAN (Hình 5 và 6):")
bullets([
    "Thông lượng bulk tương đương giữa Drop-Tail, RED không ECN và RED có ECN.",
    "Trễ của lưu lượng telnet tương tác thấp hơn rõ rệt trong các mô phỏng có ECN; càng nhiều luồng bulk (tải nặng) thì sự khác biệt càng lớn vì gateway không-ECN phải rơi gói nhiều hơn để điều khiển nghẽn.",
    "Đồng hồ TCP 100 ms trong WAN không phải vấn đề lớn (RTT lớn, chờ timeout ít tương quan) — đúng như dự đoán: lợi ích ECN về mặt timer rõ nhất trên LAN.",
])
p("Kết luận của tác giả: ECN mang lại lợi ích “clear, if modest” — rõ ràng nhưng vừa "
  "phải. Lợi ích chính là tránh rơi gói không cần thiết, từ đó giảm trễ cho lưu lượng "
  "tương tác thấp băng thông và giảm phụ thuộc retransmit timer (đồng hồ TCP thô). Kết "
  "quả được khẳng định là ĐỊNH TÍNH, không định lượng mức giảm trễ cho một mạng cụ thể "
  "vì phụ thuộc topology, tổ hợp lưu lượng và chi tiết thuật toán. Bài báo cũng nêu nhược "
  "điểm: đầu gửi “lộn xộn” có thể bỏ qua ECN; thông báo ECN có thể bị rơi trên đường đi "
  "(nhưng với RED, gateway tiếp tục đánh dấu nên mất thông báo lẻ tẻ không nghiêm trọng), "
  "và các vấn đề triển khai: Source Quench vs ECN field, triển khai dần dần, độ thô đồng "
  "họ TCP, TCP chạy trên ATM.")
doc.add_page_break()

# ===================== CHƯƠNG 2 =====================
doc.add_heading("Chương 2. Tái hiện thí nghiệm trên ns-3", level=1)

doc.add_heading("2.1 Môi trường và công cụ", level=2)
bullets([
    "ns-3.44 (ns-3 Project) — mô phỏng mạng discrete-event, xây dựng bằng CMake + Ninja, biên dịch với GCC trên Ubuntu 22.04 (WSL2).",
    "Các module dùng: core, network, internet (TCP/IPv4), point-to-point, applications (BulkSend, OnOff, PacketSink), traffic-control (FifoQueueDisc, RedQueueDisc), flow-monitor.",
    "Phân tích và vẽ biểu đồ: Python 3 (pandas, matplotlib).",
    "Đại diện TCP: TcpNewReno — phiên bản hiện đại gần nhất với Reno 4.3 BSD dùng trong bài (kèm SACK trong thực tế; được ghi nhận là khác biệt có chủ đích).",
])
p("Về ECN trong ns-3: TcpSocketBase có thuộc tính UseEcn (On/Off/Acceptable); "
  "RedQueueDisc có thuộc tính UseEcn — khi bật, gateway đặt dấu CE thay vì loại gói khi "
  "còn dưới ngưỡng tràn. ns-3 thương lượng ECN theo kiểu RFC 3168 (SYN mang ECE/CWR).")

doc.add_heading("2.2 Mô hình topology và tham số", level=2)
p("Kịch bản LAN bám sát Hình 1 của bài: 15 nguồn (5 bulk + 10 telnet-like) nối star "
  "qua link 100 Mbps/10 μs vào router GWa; GWa —(100 Mbps/10 μs, nút cổ chai)→ GWb; "
  "GWb nối star tới 15 sink. Hàng đợi (queue disc) được cài tại egress của GWa. Kịch "
  "bản WAN đơn giản hóa Hình 4: hai router GWa —(45 Mbps/10 ms)→ GWb với access link "
  "100 Mbps/2 ms (RTT ≈ 28–34 ms, trong khoảng 21–40 ms của bài); hàng đợi tại cả hai "
  "egress; lưu lượng hai chiều.")
add_table(
    ["Thông số", "Giá trị tái hiện", "Ghi chú"],
    [
        ["Luồng bulk", "5 (LAN) / 4 mỗi chiều (WAN)", "BulkSend, gói dữ liệu 1000 B, không giới hạn"],
        ["Luồng telnet-like", "10 (LAN) / 8 mỗi chiều (WAN)", "OnOff→TCP, gói 40 B, 640 bps (~2 gói/s như tcplib)"],
        ["Buffer (packet-based)", "60, 120, 180, 240 kB", "≈ số gói (1 gói ≈ 1 kB); MaxSize của queue disc"],
        ["Cửa sổ TCP", "8 kB và 64 kB (LAN); 64 kB (WAN)", "SndBufSize/RcvBufSize"],
        ["RED", "min_th = B/12, max_th = B/4, max_p = 0,1", "QW = 0,002 (LAN) / 0,001 (WAN); MeanPktSize = 1000"],
        ["Thời gian chạy", "15 s (LAN), 10 s (WAN)", "Giống bài"],
        ["Lặp (seed)", "2–3 lần/tổ hợp", "Trung bình — như 5 lần của bài (ít hơn để rút ngắn demo)"],
        ["Đồng hồ TCP", "MinRto mặc định ns-3 (1 s)", "Khác bài (RTO ban đầu 3 s, đồng hồ 0,1/100 ms) — ns-3 có timer tinh vi"],
    ],
    caption="Bảng 2.1: Tham số mô phỏng tái hiện")

doc.add_heading("2.3 Ba nhóm thí nghiệm", level=2)
bullets([
    "Nhóm A — DropTail (đối chứng): FifoQueueDisc, loại gói khi buffer đầy.",
    "Nhóm B — RED không ECN: RedQueueDisc UseEcn = false; đánh dấu xác suất = rơi gói.",
    "Nhóm C — RED + ECN: RedQueueDisc UseEcn = true và TcpSocketBase::UseEcn = On ở mọi nút; gateway đánh dấu CE thay vì rơi gói dưới ngưỡng tràn.",
])
p("Cả ba nhóm dùng chung topology, seed, thời gian chạy và tổ hợp tham số để so sánh "
  "công bằng (đúng tinh thần bài: “cùng topology, cùng seed, cùng tải”).")

doc.add_heading("2.4 Mã nguồn chính", level=2)
p("Hai chương trình C++ (scratch/ecn-lan.cc và scratch/ecn-wan.cc). Đoạn code then "
  "chốt cho cấu hình hàng đợi và phản hồi ECN:")
code_block(
    "// Cau hinh TCP (dung chung, dat truoc khi tao socket)\n"
    'Config::SetDefault("ns3::TcpSocket::SegmentSize", UintegerValue(1000));\n'
    'Config::SetDefault("ns3::TcpSocket::SndBufSize", UintegerValue(winKb * 1024));\n'
    'Config::SetDefault("ns3::TcpSocket::RcvBufSize", UintegerValue(winKb * 1024));\n'
    'Config::SetDefault("ns3::TcpL4Protocol::SocketType", StringValue("ns3::TcpNewReno"));\n'
    'Config::SetDefault("ns3::TcpSocketBase::UseEcn",\n'
    '                   StringValue(config == "ecn" ? "On" : "Off"));\n'
    "\n"
    "// Hang doi tai gateway: RED (min_th = B/12, max_th = 3*min_th) hoac DropTail\n"
    "TrafficControlHelper tch;\n"
    "if (config == \"dt\") {\n"
    "  tch.SetRootQueueDisc(\"ns3::FifoQueueDisc\", \"MaxSize\",\n"
    "                       QueueSizeValue(QueueSize(std::to_string(bufPkts) + \"p\")));\n"
    "} else {\n"
    "  tch.SetRootQueueDisc(\"ns3::RedQueueDisc\",\n"
    "      \"MinTh\", DoubleValue(bufPkts / 12.0),\n"
    "      \"MaxTh\", DoubleValue(3.0 * bufPkts / 12.0),\n"
    "      \"MaxP\",  DoubleValue(0.1),\n"
    "      \"QW\",    DoubleValue(0.002),\n"
    "      \"MeanPktSize\", UintegerValue(1000),\n"
    "      \"UseEcn\", BooleanValue(config == \"ecn\"),\n"
    "      \"MaxSize\", QueueSizeValue(QueueSize(std::to_string(bufPkts) + \"p\")));\n"
    "}\n"
    "QueueDiscContainer qdiscs = tch.Install(bneckDevs.Get(0));\n"
    "\n"
    "// Dem CE marks: goi dequeue voi header ECN == CE\n"
    "void HandleQDequeue(Ptr<const QueueDiscItem> item) {\n"
    "  auto ip = DynamicCast<const Ipv4QueueDiscItem>(item);\n"
    "  if (ip && ip->GetHeader().GetEcn() == Ipv4Header::CE) g_cemarks++;\n"
    "}")
p("Đo lường: FlowMonitor thu số byte/n.packet theo từng dòng (5-tuple) để tính thông "
  "lượng và trễ one-way (trung bình và cao nhất qua delayHistogram); trace "
  "“Drop”/“PacketDequeued” của queue disc để đếm gói rơi và gói đánh dấu CE. Kết quả "
  "xuất CSV, phân tích bằng pandas và vẽ matplotlib.")

doc.add_heading("2.5 Kiểm tra tính đúng đắn của chương trình và mô phỏng", level=2)
bullets([
    "Mức tải thấp (1 luồng bulk): không có gói rơi, không có CE mark, thông lượng ≈ 100 Mbps (đúng khả năng link).",
    "Tăng số luồng bulk để tạo nghẽn có kiểm soát: quan sát queue disc drops > 0, hàng đợi (PacketsInQueue) dao động dưới max_th.",
    "Nhóm ECN: xác nhận SYN được thương lượng ECN (UseEcn = On), số CE marks > 0 khi nghẽn, số gói rơi giảm tương ứng so với nhóm RED không ECN.",
    "Cân đối gói: số gói gửi ≈ số gói nhận + rơi + còn trong hàng đợi lúc kết thúc (sai số do gói còn đang bay).",
    "Chạy lặp nhiều seed: giá trị trung bình và độ lệch chuẩn ổn định, không có run lỗi (kiểm tra cờ FAIL trong script).",
    "Đối chiếu định tính với bài: nhóm ECN phải cho thấy ít rơi gói + trễ telnet thấp hơn nhóm DropTail/RED không ECN — đúng xu hướng công bố.",
])
doc.add_page_break()

# ===================== CHƯƠNG 3 =====================
doc.add_heading("Chương 3. Kết quả thực nghiệm và so sánh", level=1)

lan = load_agg("lan_results.csv")
wan = load_agg("wan_results.csv")

doc.add_heading("3.1 Kết quả kịch bản LAN", level=2)
if lan is None:
    p("[Số liệu LAN sẽ được bổ sung sau khi chạy bộ thí nghiệm ns-3.]")
else:
    for wi, win in enumerate(sorted(lan["winKb"].unique()), start=1):
        p(f"Cửa sổ TCP = {int(win)} kB (trung bình các seed):", bold=True)
        rows = []
        for buf in sorted(lan["bufferKb"].unique()):
            row = [str(int(buf))]
            for cfg, _lab in CFGL:
                sel = lan[(lan.config == cfg) & (lan.bufferKb == buf) & (lan.winKb == win)]
                row.append(fmt(sel["bulk"].mean()))
            rows.append(row)
        add_table(["Buffer (kB)", "DropTail", "RED", "RED + ECN"], rows,
                  caption=f"Bảng 3.1{chr(96+wi)}a — Thông lượng bulk tổng (Mbps), cửa sổ {int(win)} kB")
        rows = []
        for buf in sorted(lan["bufferKb"].unique()):
            row = [str(int(buf))]
            for cfg, _lab in CFGL:
                sel = lan[(lan.config == cfg) & (lan.bufferKb == buf) & (lan.winKb == win)]
                row.append(fmt(sel["dAvg"].mean(), 1))
            rows.append(row)
        add_table(["Buffer (kB)", "DropTail", "RED", "RED + ECN"], rows,
                  caption=f"Bảng 3.1{chr(96+wi)}b — Trễ trung bình one-way của telnet (ms), cửa sổ {int(win)} kB")
    rows = []
    for cfg, lab in CFGL:
        sel = lan[lan.config == cfg]
        rows.append([lab, fmt(sel["drops"].mean(), 0), fmt(sel["marks"].mean(), 0),
                     fmt(sel["dWorst"].mean(), 1)])
    add_table(["Cấu hình", "Gói rơi TB", "CE marks TB", "Trễ telnet cao nhất TB (ms)"], rows,
              caption="Bảng 3.1c — Gói rơi, dấu CE và trễ cực đại telnet (tất cả buffer, cửa sổ 64 kB)")
    try_picture(os.path.join(RESULTS, "lan_win64.png"), caption="Hình 3.1: Kết quả LAN — cửa sổ 64 kB")
    try_picture(os.path.join(RESULTS, "lan_win8.png"), caption="Hình 3.2: Kết quả LAN — cửa sổ 8 kB")

doc.add_heading("3.2 Kết quả kịch bản WAN", level=2)
if wan is None:
    p("[Số liệu WAN sẽ được bổ sung sau khi chạy bộ thí nghiệm ns-3.]")
else:
    rows = []
    for buf in sorted(wan["bufferKb"].unique()):
        row = [str(int(buf))]
        for cfg, _lab in CFGL:
            sel = wan[(wan.config == cfg) & (wan.bufferKb == buf)]
            row.append(fmt(sel["bulk"].mean()))
        rows.append(row)
    add_table(["Buffer (kB)", "DropTail", "RED", "RED + ECN"], rows,
              caption="Bảng 3.2a — Thông lượng bulk tổng (Mbps), cửa sổ 64 kB")
    rows = []
    for buf in sorted(wan["bufferKb"].unique()):
        row = [str(int(buf))]
        for cfg, _lab in CFGL:
            sel = wan[(wan.config == cfg) & (wan.bufferKb == buf)]
            row.append(fmt(sel["dAvg"].mean(), 1))
        rows.append(row)
    add_table(["Buffer (kB)", "DropTail", "RED", "RED + ECN"], rows,
              caption="Bảng 3.2b — Trễ trung bình one-way của telnet (ms)")
    rows = []
    for cfg, lab in CFGL:
        sel = wan[wan.config == cfg]
        rows.append([lab, fmt(sel["drops"].mean(), 0), fmt(sel["marks"].mean(), 0),
                     fmt(sel["dWorst"].mean(), 1)])
    add_table(["Cấu hình", "Gói rơi TB", "CE marks TB", "Trễ telnet cao nhất TB (ms)"], rows,
              caption="Bảng 3.2c — Gói rơi, dấu CE và trễ cực đại telnet (WAN)")
    try_picture(os.path.join(RESULTS, "wan_results.png"), caption="Hình 3.3: Kết quả WAN")

doc.add_heading("3.3 So sánh với bài báo và nhận xét", level=2)
if lan is not None:
    def _m(df, cfg, col="bulk"):
        return df[df.config == cfg][col].mean()
    dt_b, red_b, ecn_b = _m(lan, "dt"), _m(lan, "red"), _m(lan, "ecn")
    dt_d, red_d, ecn_d = _m(lan, "dAvg"), _m(lan, "red", "dAvg"), _m(lan, "ecn", "dAvg")
    dt_dr, red_dr, ecn_dr = _m(lan, "dt", "drops"), _m(lan, "red", "drops"), _m(lan, "ecn", "drops")
    p(f"Về thông lượng bulk trong LAN (mọi cấu hình, trung bình): DropTail {dt_b:.2f} Mbps, "
      f"RED {red_b:.2f} Mbps, RED+ECN {ecn_b:.2f} Mbps — nhóm ECN không làm mất thông lượng "
      f"luồng bulk, đúng như bài báo (thông lượng giữ ở mức cao, tương đương hoặc tốt hơn "
      f"khi nhóm không-ECN phải chờ timeout).")
    if ecn_d > 0 and dt_d > 0:
        p(f"Về trễ telnet (LAN): trung bình one-way delay của RED+ECN là {ecn_d:.1f} ms so với "
          f"{dt_d:.1f} ms của DropTail và {red_d:.1f} ms của RED không ECN — giảm khoảng "
          f"{(1 - ecn_d / dt_d) * 100:.0f}% so với DropTail. Số gói rơi trung bình tương ứng: "
          f"{dt_dr:.0f} / {red_dr:.0f} / {ecn_dr:.0f} — ECN thay thế phần lớn việc rơi gói "
          f"bằng việc đánh dấu CE, đúng xu hướng bài báo.")
    p("Về WAN: tương tự bài, thông lượng bulk giữa ba nhóm gần nhau, còn trễ lưu lượng tương "
      "tác thấp hơn ở nhóm có ECN; sự khác biệt tăng lên khi tải nghẽn tăng.")
p("Khác biệt có chủ đích so với bài gốc cần lưu ý khi diễn giải số liệu: (1) ns-3 dùng "
  "TcpNewReno và cơ chế thương lượng ECN theo RFC 3168, không phải Reno 4.3 BSD với một "
  "bit ECN mô phỏng; (2) timer ns-3 tinh vi (min RTO 1 s) thay cho đồng hồ 0,1/100 ms với "
  "RTO ban đầu 3 s — vì vậy kịch bản “đồng hồ thô làm sụt thông lượng” của bài không được "
  "tái hiện đầy đủ; (3) mạng ns-3 hiện đại có cơ chế khác (SACK, cửa sổ động) nên số liệu "
  "chỉ kiểm chứng XU HƯỚNG: ECN giảm rơi gói và giảm trễ lưu lượng nhạy trễ, thông lượng "
  "bulk giữ nguyên — không nhằm tái tạo chính xác các đồ thị năm 1994.")

# ===================== CHƯƠNG 4 =====================
doc.add_heading("Chương 4. Nhận xét và kết luận", level=1)
p("ECN thay đổi cách mạng báo tắc nghẽn: thay vì đợi bộ đệm tràn rồi loại gói, router "
  "(RED) phát hiện nghẽn đang hình thành và đánh dấu gói; đầu TCP giảm cửa sổ chặn ngay "
  "khi nhận dấu hiệu, không cần đợi mất gói và truyền lại. Bài báo 1994 đóng góp chủ yếu "
  "ở quy tắc phản hồi TCP (một thông báo = một phản ứng, tối đa mỗi RTT, không dừng gửi) "
  "và một khảo sát mô phỏng kỹ lưỡng; thuật toán RED kế thừa từ công trình trước đó.")
p("Thí nghiệm tái hiện trên ns-3 xác nhận định tính các kết luận của bài: RED+ECN làm "
  "giảm rõ số gói rơi và độ trễ của lưu lượng nhạy trễ (telnet-like) trong khi giữ nguyên "
  "thông lượng luồng bulk, trên cả kịch bản LAN cổ chai ngắn và WAN hai chiều; lợi ích "
  "đặc biệt rõ khi buffer nhỏ hoặc mức nghẽn cao. Kết quả cũng nhất quán với cảnh báo của "
  "tác giả: không có ECN, mạng vẫn hoạt động được ở mức hợp lý nếu tham số phù hợp — "
  "lợi ích là “rõ ràng nhưng vừa phải”, phụ thuộc cấu hình.")
p("Hạn chế của phần tái hiện: mô phỏng dùng TCP hiện đại (NewReno, timer tinh vi) thay "
  "cho Reno 4.3 BSD và đồng hồ thô của 1994, số seed ít hơn bài (2–3 so với 5), kịch bản "
  "WAN được đơn giản hóa so với Hình 4, và chưa tái hiện biến thiên “đồng hồ TCP 100 ms”. "
  "Do đó kết luận mang tính kiểm chứng xu hướng, không phải so sánh định lượng 1-1.")
p("Bài báo cũng để lại nhiều vấn đề mở đã được giải quyết sau này: chuẩn hóa ECN vào IP "
  "và TCP (RFC 3168), ECN cho shallow buffers/datacenter (DCTCP), việc triển khai thực tế "
  "và các tranh luận về phản ứng của middlebox — cho thấy giá trị dài hạn của hướng tiếp "
  "cận này.")

# ===================== TÀI LIỆU =====================
doc.add_heading("Tài liệu tham khảo", level=1)
refs = [
    '[1] S. Floyd, "TCP and Explicit Congestion Notification," ACM SIGCOMM Computer Communication Review, vol. 24, no. 5, pp. 8–23, 10/1994. DOI: 10.1145/205511.205512.',
    "[2] S. Floyd, V. Jacobson, “Random Early Detection Gateways for Congestion Avoidance,” IEEE/ACM Trans. Networking, vol. 1, no. 4, 1993 (thuật toán RED).",
    "[3] K. Ramakrishnan, R. Jain, “A Binary Feedback Scheme for Congestion Avoidance in Computer Networks,” ACM TOCS, vol. 8, no. 2, 1990 (DECbit).",
    "[4] V. Jacobson, “Congestion Avoidance and Control,” SIGCOMM 1988 (Slow Start, Congestion Avoidance, Fast Retransmit).",
    "[5] K. Ramakrishnan, S. Floyd, D. Black, “The Addition of Explicit Congestion Notification (ECN) to IP,” RFC 3168, 2001.",
    "[6] W. Stevens, TCP/IP Illustrated, Volume 1, Addison-Wesley, 1994.",
    "[7] ns-3 Project, “TCP models” và “RED queue disc”, ns-3 Model Library. https://www.nsnam.org/docs/models/html/",
    "[8] ns-3.44 release. https://www.nsnam.org/releases/",
]
for r in refs:
    para = doc.add_paragraph(r)
    para.paragraph_format.line_spacing = 1.2
    for run in para.runs:
        run.font.size = Pt(12)

# ===================== PHỤ LỤC =====================
doc.add_heading("Phụ lục. Cách chạy lại thí nghiệm", level=1)
p("Các tệp nguồn nằm trong thư mục ns3/ của đồ án:")
code_block(
    "ns3/ecn-lan.cc        # kich ban LAN (5 bulk + 10 telnet)\n"
    "ns3/ecn-wan.cc        # kich ban WAN (hai chieu)\n"
    "ns3/run_experiments.sh# sweep toan bo cau hinh -> CSV\n"
    "ns3/plot_results.py   # ve bieu do tu CSV")
p("Các bước thực hiện (Ubuntu/WSL2):")
code_block(
    "# 1. Cai build tools\n"
    "sudo apt install cmake ninja-build g++ python3 python3-pip\n"
    "\n"
    "# 2. Tai va giai nen ns-3.44\n"
    "curl -sfL -O https://www.nsnam.org/releases/ns-allinone-3.44.tar.bz2\n"
    "tar -xjf ns-allinone-3.44.tar.bz2 && cd ns-allinone-3.44/ns-3.44\n"
    "\n"
    "# 3. Copy ma nguon vao scratch va build\n"
    "cp /duong/dan/ns3/ecn-lan.cc /duong/dan/ns3/ecn-wan.cc scratch/\n"
    "./ns3 configure --build-profile=optimized --disable-examples --disable-tests \\\n"
    "  --enable-modules=\"core;network;internet;applications;point-to-point;traffic-control;flow-monitor\"\n"
    "./ns3 build -j$(nproc)\n"
    "\n"
    "# 4. Chay thu 1 cau hinh\n"
    './ns3 run "scratch/ecn-lan --config=ecn --bufferKb=120 --winKb=64 --run=1"\n'
    "\n"
    "# 5. Sweep va ve so\n"
    "bash run_experiments.sh\n"
    "pip install pandas matplotlib && python plot_results.py /root/ecn-results ./")

out = os.path.join(BASE, "Bao_cao_ECN_Floyd_1994_v2.docx")
doc.save(out)
print("Saved:", out)
