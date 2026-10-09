# Task Log — VBridge-Dyn

> Append-only. KHÔNG sửa entry cũ. Mỗi entry là 1 mốc thời gian / quyết định /
> task done. Format: `## YYYY-MM-DD — <Tiêu đề ngắn>`.

---

## 2026-09-12 — SB29: vá mô hình tĩnh đối chứng, chạy sạch 6 loại phân tích

**Bối cảnh**: track mới từ 2026-09-11 — mô hình đối chứng cầu SB29 (Km116+097,
ĐSTĐC Hà Nội–Quảng Ninh, 40,85+64+40,85 m), ngoài repo tại
`1_du_an/SB29_HNQN/`. Vào phiên, kiểm tra thì phân tích
tĩnh đã chạy nhưng kết quả thuộc file khác và 6/15 case cho kết quả bằng 0.

**Quyết định**:
- Giữ `.mct` là nguồn cho những gì nó diễn tả đúng được; các khối mà cú pháp MCT
  chưa kiểm chứng (gradient, lún, phổ phản ứng, quy đổi khối lượng) **chỉ** tạo
  qua MAPI, và ghi chú rõ trong `.mct` — thà thiếu còn hơn tạo file sai âm thầm.
- Phạm vi mô hình chốt là **145,70 m** (P1→P4); hai nhịp dẫn 32,65 m không mô
  hình (thuyết minh trước ghi 209 m gây hiểu nhầm, đã sửa).

**Đã làm**:
- **Gối P1/P4 thả phương đứng** — lỗi nặng nhất. Elastic link nối nút dầm (z=0)
  xuống đỉnh trụ nên trục x cục bộ là trục ĐỨNG; bản cũ khai `SDx = 0` định thả
  phương dọc. Hệ quả: hai nhịp biên chạy như công xôn 40,85 m, đầu dầm võng
  74,5 mm dưới DC, mô men âm tại P2 = −235 602 kN·m. midas **không** báo lỗi vì
  phương ngang + xoắn vẫn khoá. Xác định trục đúng bằng thí nghiệm 3 biến thể
  SDR trên chính midas (tiêu chí: lực hãm về P1/P4 phải = 0) → `SDx = SDy = ∞,
  SDz = 0`. Sau khi sửa: đầu dầm 1,56 mm, mô men tại P2 −124 117 kN·m.
- `CS` đổi `LCTYPE` `CS`→`T` (kiểu `CS` chỉ giải trong construction stage).
- `Q_LAK` dùng tải rải từng phần → đúng 1 000 kN / 30,30 m (trước 1 031 kN).
- `DT_P/DT_M` (gradient +15/−8 °C, EN 1991-1-5 B.6.1 Type 3), `SET` (4 nhóm lún
  10 mm + case đường bao), `EQ_X/EQ_Y` (phổ EN 1998-1 Type 1 nền E, a_gR=0,12g,
  q=1,5) — trước là case rỗng kiểu USER, kết quả bằng 0.
- **LM71 chưa từng được đẩy vào midas**: có trong `.mct` nhưng `push_to_midas.py`
  không gửi bảng moving load. Bổ sung code/lane/vehicle/2 case.
- 17 tổ hợp (12 ULS + 5 SLS) dùng đúng loại `ST`/`MV`/`SM`/`RS`.
- Thêm `scripts/report_results.py` xuất bảng kết quả.

**Số liệu chốt**: cân bằng DC 146 652 / DC2 20 398 / Q_LBK 2 914 / Q_LAK 1 000,0 kN.
f₁ = 2,14 Hz, tổng khối lượng 17 035 t, tham gia X/Y = 90,6/92,4 %.
My chi phối: ULS-1D +124 682, ULS-1E −416 829 kN·m. Độ võng LM71×Φ nhịp 64 m =
9,40 mm = L/6 809 (giới hạn L/600) → đạt. **Động đất chi phối phần dưới**: mô men
đáy bệ P2 tới 191 803 kN·m (ULS-4B) so với 35 307 kN·m (ULS-3A).

**Hai bẫy MAPI đã trả giá** (chi tiết ở `docs/01_THUYET_MINH_MO_HINH.md` §7):
1. `/doc/anal` trên tài liệu `Untitled` → midas bật Save As và **treo cả API lẫn
   GUI**, phải can thiệp tay. midas còn tự bật hộp thoại lưu sau một lúc nếu tài
   liệu chưa có tên → có thể nổ giữa lúc đang đẩy dữ liệu. Nay `push_to_midas.py`
   `/doc/saveas` ngay sau `/doc/new`.
2. `Convert Self-weight into Mass`: phải `PUT /db/styp` với bản ghi đầy đủ **kèm
   `SMASS: 1`**. `POST` không ghi; `GET` chỉ trả `SMASS` khi cờ đang bật nên
   round-trip GET→PUT lúc đang tắt bị thiếu trường → `Wrong Field`. Quên thì khối
   lượng dao động còn 2 080 t thay vì 17 035 t, f₁ 4,52 thay vì 2,14 Hz.

**Blockers mới**:
- B# — `q` (hệ số ứng xử động đất) chưa chốt: 1,5 hay 3,5·λ. Ảnh hưởng >2 lần tới
  toàn bộ ULS-4 ⇒ tới cốt thép trụ và cọc. Cần chốt trước khi kiểm toán mặt cắt.
- B# — chưa có bố trí cốt thép trong `sb29_data.py` ⇒ chưa kiểm toán GSD được.

---

## 2026-07-24 — Sweep động A1–A10 hoàn tất + cập nhật hồ sơ tiêu chí TGD

**Bối cảnh**: User đã chạy MIDAS Civil 2022 toàn bộ quét động HSLM-A1…A10 (bản
GROUPED theo đoàn tàu, ζ=1,0%). Do MIDAS hạn chế chiều dài đường dẫn, mô hình
chạy được di chuyển sang `D:\00_MCT_GOP_NHIEU_VAN_TOC`. Yêu cầu: bám tiêu chí
thiết kế (`8-4_ Tieu chi TK (TEDI)-PT dong.docx`), xử lý các mục liên quan đến
mô hình tính + xuất kết quả, rồi mới làm báo cáo một lượt.

**Đã làm** (chỉ phần mô hình + xuất kết quả, chưa làm báo cáo):
- Xác minh dữ liệu FINAL `00_TONG_HOP_KIEM_TRA_20260724_FINAL`: 320 case,
  76/76 sheet đọc OK, `complete_exports=True`, `out_ok=True`, 10/10 đoàn tàu,
  mỗi đoàn 1 OUT gộp. `1_du_an/BXD/slide/.../HSLM-A1_A10_FULL_SWEEP_20260724` đã đồng bộ
  đủ (5 file trùng md5 + governing_by_train/identity_crosscheck + KIEM_TRA_TONG_THE).
- Cập nhật ma trận tiêu chí `SO_THEO_DOI_TIEU_CHI_VA_CASE_MIDAS.xlsx`:
  - Ma_tran: CS-02/03/04/07 + DY-03/04/05 → **ĐÃ CÓ KẾT QUẢ** (kèm bằng chứng sweep);
    CS-10/DY-06 giữ MỘT PHẦN nhưng ghi rõ dữ liệu đã đủ để lập phụ lục.
  - Tong_quan (công thức COUNTIF tự cập nhật): Đã có 12→19, Một phần 10→7,
    MCT chờ chạy 4→0; kết luận quản lý #3 sửa để phản ánh envelope A1–A10 xong.
  - So_case_MIDAS: 320 dòng → **ĐÃ CHẠY - ĐÃ XUẤT**, cột OUT trỏ về `D:\00_MCT_GOP_NHIEU_VAN_TOC\<train>\...GROUPED\Untitled.OUT`.
  - Ket_qua_da_co: thêm block envelope A1–A10 (DZ/az/My/f1 chi phối), cập nhật ghi chú A1@330.
- Cập nhật `README_TONG_THE.md` (dossier) phản ánh sweep xong + nguồn D:\00_...
  và làm rõ vai trò `KET_QUA_KIEM_TRA_HO_SO` là kiểm tra toàn vẹn cấu trúc.

**Kết quả chi phối (envelope A1–A10, ζ=1,0%)**: HSLM-A7 —
|DZ|=4,268 mm@415, |az|=3,374 m/s²@420 (đạt ≤3,5 ballast, dự trữ ~3,6%),
|My|=12.690 kN·m@415; f1=4,790193 Hz (mọi đoàn).

**Còn lại theo tiêu chí** (đưa vào phụ lục/báo cáo hoặc chờ đầu vào):
DY-06 DAF động/tĩnh, CS-10 bảng mode đến cutoff, AT-01 L/600 + TN tiện nghi,
ST-09/DY-07 mỏi cáp-cốt đai, RS-01…09 RSI (không hội tụ), CS-05 đoàn tàu thực,
AT-02/04/05/06 cần model 3D hai ray, ST-03/04 SW/0–SW/2.

**Chưa làm**: báo cáo TGD (`05_BAO_CAO_TGD/*.docx`) — làm một lượt ở bước sau.

## 2026-07-25 — Báo cáo TGD lần 3 + Phụ lục tính toán + chốt RSI (Wizard)

**Bối cảnh**: session dài, làm việc trên hồ sơ TGD `1_du_an/BXD/TGD/`.

**Chốt RSI**: model dựng tay không hội tụ do (a) nối liên tục 32 mối (link SDx=1e7), (b) dùng
trị số ballast cho ballastless. Dựng lại bằng **MIDAS RSI Wizard** (giản đơn + Concrete Bed,
u0=0,5mm, kháng 40/60) → HỘI TỤ. Kết quả (bản V2, ΔT ray=0 để loại CWR tự do): **ứng suất ray
bổ sung +72,7/−62,7 MPa ≤ ±92 → ĐẠT**; δB 0,99≤5; δH 2,77≤8; δv 0,76≤2. Quy trình chốt:
Wizard sinh model → **Analyze lại** → mới xuất Rail Track Analysis Report. Còn RS-09 fastener
(uplift 12kN/nén 2,5mm) chờ catalog.

**Ma trận tiêu chí** (`00_QUAN_LY_HO_SO/SO_THEO_DOI_TIEU_CHI_VA_CASE_MIDAS.xlsx`): 31 đã có kết
quả / 5 một phần / 2 không áp dụng / 7 chờ đầu vào. AT-01/03/04, TN-01, CS-10, RS-02…07 lên ĐẠT.

**Báo cáo chính** `05_BAO_CAO_TGD/Bao_cao_lan_3.docx`: cập nhật lần 2, style bám bản chính thức
lần 1 (`bao_cao_lan_1_ban_chinh_thuc.pdf`). Cấu trúc §1–§8 + §3.3 an toàn giao thông (tóm tắt
Mục 3 doc 8-4) + §3.4 tiện nghi (Mục 4). Định dạng NĐ30 (heading 15pt xanh 1F4E79 / tiểu mục
14pt / thân bài 13pt / bảng 12pt header xanh chữ trắng; từ khóa kỹ thuật đỏ FF0000). §6 chi tiết
(RSI Wizard/Ballast-Fastener/SSI/Plugins/API). Header "Phòng QLCL&NCPT". **Đã bỏ mọi nội dung
riêng BXD 32,6m** khỏi báo cáo chính (tổng quát hóa).

**Phụ lục** `05_BAO_CAO_TGD/Phu_luc_tinh_toan_lan_3_chi_tiet.docx` (bản summary cũ
`Phu_luc_tinh_toan_lan_3.docx` chờ xóa khi user đóng): 9 mục, 5 bảng, **10 hình** (mô hình 3D,
cáp DƯL, HSLM-A, ζ, mode 4,79Hz, đồ thị V–az/V–DZ, time-history, **ứng suất ray dọc tuyến**).
Đã đối chiếu đủ doc 8-4 + bổ sung nhóm A (V>200 → động bắt buộc; Φ3=1,129; DAF; lực dọc ray
Nr≈557≤706kN; điều kiện UIC-60; sửa nhãn δB dọc). Đồ thị + ảnh ở `05_BAO_CAO_TGD/appendix_figs/`.
Công cụ: **OfficeCLI** (npm @officecli/officecli) + python-docx + pandoc + matplotlib.

**Next action**: (1) user đóng file summary cũ → xóa + đổi tên bản chi tiết thành
`Phu_luc_tinh_toan_lan_3.docx`. (2) DAF bằng số cần user xuất riêng moving-load LM71×Φ trên dầm.
(3) RS-09 fastener chờ catalog. (4) nhóm B (xoắn ray 3D, dao động ngang, VBI, mỏi) là hạng mục
mô hình/đầu vào riêng.

## 2026-07-26 — Chốt bản sửa phụ lục lần 3 theo markup của user

**Bối cảnh**: user sửa trực tiếp vào `05_BAO_CAO_TGD/Phu_luc_tinh_toan_lan_3_chi_tiet.docx`
bằng định dạng thủ công (gạch ngang + highlight vàng, KHÔNG dùng Track Changes) rồi yêu cầu
thi hành, kèm "căn chỉnh ô, bảng biểu phù hợp".

**Quyết định — quy ước đọc markup** (đã ghi memory `docx-markup-review-convention`):
- `w:strike` = nội dung không đưa vào → xoá trọn run.
- `w:highlight` vàng = chữ user vừa chèn (rsid khác rsid gốc) → giữ chữ, bỏ nền.
- Chữ đỏ FF0000 = nhấn mạnh kỹ thuật có chủ ý của tài liệu → giữ nguyên.
- Khi xoá làm câu sai ngữ pháp: **bỏ trọn cụm đã gạch**, không tự giữ liên từ để chữa câu
  (user đã yêu cầu bỏ luôn "nên theo" sau khi tôi giữ lại).

**Đã làm**:
- Accept 14 đoạn gạch bỏ + 2 chỗ highlight. Xoá **toàn bộ viện dẫn nội bộ** "Mục 1.3/1.4/3/4,
  Mục 2.4-2.5, tài liệu 8-4" → trích TCVN 13594 trực tiếp (mục 2 còn `(11.4.4.4 TCVN 13594-3)`).
- Bỏ giọng tự quảng bá ("nhằm minh chứng năng lực của" → "sử dụng phần mềm").
- Gọn cột "Đánh giá" trong bảng: bỏ "(dự trữ ~32,5%)", "(mức rất tốt)", "(cần model 3D)",
  "(giai đoạn NX/VBI)"; giới hạn Δu_rb → "không áp dụng" (4 mm là trị số của ballast).
- Căn chỉnh 5 bảng: `tblW` 9.355 twips + `tblLayout fixed` (= đúng vùng chữ A4, lề 1701/850),
  `tblHeader` lặp tiêu đề khi sang trang, `cantSplit`, `vAlign=center`, cellMar 40/85, cột chữ
  căn trái + cột số căn giữa, tinh chỉnh bề rộng cột để hết ngắt chữ xấu.
- **Đặt tên Bảng 1-5** (nghiêng 11pt, canh giữa, `keepNext`, phía trên bảng) — trước đây chỉ
  hình có caption. Bề rộng cột chi tiết ghi ở memory `docx-table-layout-bao-cao`.
- Backup `Phu_luc_tinh_toan_lan_3_chi_tiet_BACKUP_truoc_sua.docx`. File cuối: 8 trang, sạch
  (0 `w:strike`, 0 `w:highlight`, 0 chuỗi "tài liệu 8-4").

**Lý do dùng python-docx + XML trực tiếp** (không OfficeCLI): cần đọc/ghi chính xác
`w:strike`/`w:highlight`/`w:tblGrid`/`w:tblHeader`. Kiểm tra bằng Word COM
(`win32com` → `ExportAsFixedFormat` format 17) rồi render PNG bằng PyMuPDF để soi bảng.

**Next action**: (1) chờ user review; nếu duyệt → áp **cùng 3 quy tắc biên tập** cho
`Bao_cao_lan_3.docx`. (2) DAF (DY-06) vẫn chờ bảng My tĩnh LM71×Φ. (3) cập nhật
`SO_THEO_DOI_TIEU_CHI_VA_CASE_MIDAS.xlsx` cho khớp trạng thái RSI đã hội tụ + chạy lại SHA-256.

## 2026-07-24 (4) — RSI dựng lại bằng Wizard ĐÃ HỘI TỤ (đột phá)

Sau khi viết `HUONG_DAN_DUNG_LAI_RSI_WIZARD.md`, user dựng lại bằng MIDAS Rail Track Analysis
Wizard (`04_RSI/04_MCT_PHUC_HOI/RSI_Wizad_32.6m/`, simply-supported từng nhịp + Concrete Bed
ballastless). Model `..._Add3_ExpansionJoint_Str` **hội tụ sạch 6 vòng lặp** (norm 1,0→0,29→
0,036→0,0094→0,0025→0,00083 < tol 1E-3), KHÔNG còn chatter. ⟹ Xác nhận chẩn đoán: nguyên nhân
là **model dựng tay bị nối liên tục (32 link SDx=1e7) + sai loại nền (ballast thay vì ballastless)**;
Wizard sinh đúng giản đơn/ballastless → hội tụ. Còn lại: mới chạy 1/10 model; cần chạy nốt
Add1/Add2/Add3 + Mov1/2/3 (+ model ứng suất _Temp/_Train), xuất Rail Track Analysis Report,
rồi đọc kết quả → mở khóa RS-01…09 + AT-06.

**Kết quả RSI (report Untitled 16:19)**: sau khi đặt **ΔT ray=0** (loại ứng suất CWR ray tự do
~126 MPa lẫn trong bản đầu 204 MPa) và Analyze lại: **ứng suất ray bổ sung +72,7/−62,7 MPa ≤ 92/72
→ ĐẠT**; chuyển vị ngang dầm 0,99≤5 OK; xoay đầu dầm 2,77≤8 OK. Còn NG chuyển vị tương đối ray–dầm
6,44mm>4mm — nhưng 4mm là tiêu chí có ballast; model vẫn dùng kháng ballast (u0=2mm). Bước chót:
đặt Concrete Bed + trị số kháng ballastless (u0≈0,5mm) → chạy lại → dùng tiêu chí fastener ballastless.
Quy trình chốt: Wizard sinh model → **Analyze lại** → mới xuất report. Chi tiết: README_PHUC_HOI_RSI.md.

## 2026-07-24 (3) — Phục hồi RSI (chẩn đoán + MCT) + mở khóa AT-04

**AT-04** (bậc chuyển vị đứng đầu dầm): user chỉ ra model là **chuỗi 5 dầm** nên tại
mỗi trụ trong có 2 đầu dầm kề. Node đầu dầm vươn ra (vd `100031` x=32,65; `200001`
x=32,75; cách gối 0,55 m) **không khống chế đứng** → Dz của chúng chính là δv. ⇒ AT-04
tính được từ `Displacement.xls` đã có (CHƯA ĐỦ ĐẦU VÀO → **MỘT PHẦN**), không cần model mới.

**RSI**: user đã export MCT nguồn từ `.mcb` (`.../Bang_tinh_phan_tich_dong_va_RSI_bang_midas/RSI/32.6m_RSI.mct`,
18813 dòng, model UIC 774-3: rail Fe360 + 2.384 lò xo rail-track song tuyến Rlfc-1..32,
LIMDISP=2 mm; tải nhiệt/hãm-kéo/đứng; 2 stage Unloaded/Loaded).
- **Chẩn đoán phân kỳ**: Stage 1 hội tụ; Stage 2 "Loaded" phân kỳ (error norm
  0,34→0,80→1,39→2,18) vì đồng thời chuyển lò xo Unloaded→Loaded **và** áp toàn bộ
  tải tàu trong 1 bước (`bINCRESTEP=NO`) khi lò xo vượt ngưỡng dẻo 2 mm.
- **Đã dựng** (`04_RSI/04_MCT_PHUC_HOI/`): `RSI_01_STAGE_SPLIT.mct` (Loaded 10 bước tải,
  iITER=200) + `RSI_01b_STAGE_SPLIT_FINE.mct` (Loaded 20/Unloaded 10 bước, iITER=300) +
  `README_PHUC_HOI_RSI.md`. Chỉ đổi khối STAGE + iITER, phần còn lại giữ nguyên (18813 dòng).
- Sheet RSI (xlsx): RSI-00/01/02 → "MCT ĐÃ SẴN - CHỜ CHẠY". RS-01…09 (Ma_tran) giữ
  KHÔNG HỘI TỤ đến khi có OUT hội tụ.
- **Chờ user**: chạy `RSI_01` trong MIDAS; nếu hội tụ → export rail force/stress, chuyển vị
  tương đối ray–dầm, δB/δH đầu dầm, fastener (giới hạn ứng suất ray **±92 MPa ballastless**).

**Cập nhật kết quả chạy (user chạy 3 file)**: cả `RSI_01`, `RSI_01b`, `RSI_00` **đều KHÔNG
hội tụ**. Bằng chứng quyết định: (1) load-stepping bị RTI bỏ qua (Stage 2 luôn STEP 1, dãy
lặp y hệt gốc); (2) error norm khóa chu trình 2 giá trị (~1,95↔~1,46) = lò xo song tuyến
chatter; (3) RSI_00 (scale hàm để không yield) vẫn switch trạng thái, làm hỏng cả Stage 1
(0,032→bùng 2,4). ⟹ **Bất hội tụ nội tại ở solver Rail-Track Interaction của MIDAS; text-MCT
hết dư địa.** Phải xử lý trong GUI: Rail Track Analysis Control (nới tiêu chí, bước tải nội tại,
cập nhật tangent), tách chuỗi tải UIC 774-3 (nhiệt→đứng→hãm/kéo), rà neo dọc ray, hoặc dựng
lại bằng RTA wizard. Xem `04_RSI/04_MCT_PHUC_HOI/README_PHUC_HOI_RSI.md`.
**Khuyến nghị**: RSI thành hạng mục MIDAS song song; làm báo cáo TGD với RS-01…09 + AT-06
đánh dấu "đang xử lý" (đúng nguyên tắc chỉ hàng có OUT hợp lệ mới là kết quả).

**Cập nhật cuối RSI (research + phương pháp riêng UIC 774-3)**: research web (MIDAS blog UIC 774-3)
xác nhận điểm gãy song tuyến là vật lý mong đợi + có 2 phương pháp (staged vs separate). Đã thử
phương pháp separate: `RSI_SEP_A_THERMAL` **HỘI TỤ**; nhưng `RSI_SEP_B_TRAIN`, `RSI_SEP_B1_VERTICAL`,
`RSI_SEP_B2_BRAKING` đều chatter. **Cô lập được gốc rễ: mọi cấu hình dùng trạng thái lò xo LOADED
đều chatter (bất kể tải), Unloaded thì hội tụ** ⟹ vấn đề ở định nghĩa kháng Loaded của lò xo
rail-track (nhiều hàm Rlfc có LOADED=0), KHÔNG phải phương pháp/tải/staging. Đã thử tổng 6 biến thể
text-MCT — hết dư địa. **Phải xử lý trong MIDAS GUI**: rà hàm kháng Loaded, dùng Analysis → Rail
Track Analysis chuyên dụng. Nhánh nhiệt đã có kết quả hợp lệ. Chi tiết + mọi biến thể:
`04_RSI/04_MCT_PHUC_HOI/README_PHUC_HOI_RSI.md`.

**Chốt RSI (research YouTube/MIDAS/LUSAS + phát hiện của user)**:
- User phát hiện model **nối liên tục** thay vì chuỗi giản đơn → xác nhận có hệ thống: 32 mối nối
  khóa dọc 2 đầu dầm kề bằng link SDx=1e7 vào node ngang chung. Sai vật lý RSI + góp phần bất hội tụ.
- `RSI_FIX_STAGED` (LOADED 0→3×unloaded): Stage 2 **y hệt bản gốc** → tài liệu MIDAS xác nhận kháng
  Loaded chỉ áp nơi có tàu, ngoài ra dùng Unloaded ⟹ LOADED=0 là **red herring**, không phải nguyên nhân.
- Model dùng trị số ballast (u0=2mm, 20/60) nhưng BXD ballastless (u0≈0,5mm) → sai đầu vào.
- **Kết luận**: model RSI dựng tay không chuẩn; phải dựng lại bằng **MIDAS RSI Wizard** (mỗi nhịp
  simply-supported Fixed/Free, trị số ballastless, wizard tự dịch tàu). Text-MCT đã cạn dư địa
  (Stage 2 bất biến với mọi thay đổi text). RSI = hạng mục GUI riêng; báo cáo đánh dấu RS-01…09 + AT-06
  "đang xử lý". Nguồn: MIDAS RSI Wizard blog + Support Rail Track Analysis Model/Boundary; LUSAS UIC774 E1-3.

## 2026-07-24 (2) — Chốt ballastless + SW/0-SW/2 N/A; xử lý CS-08/ST-03/ST-04

**Bối cảnh**: User yêu cầu xử lý thêm model SW/0-SW/2 và biến thể mass, và giải
thích biến thể mass để làm gì/thuộc tiêu chí nào. Khi kiểm tra MCT + tài liệu 8-4:
- Kết cấu là **5 nhịp giản đơn** (`*CONSTRAINT`: mỗi nhịp 1 gối cố định + 1 gối di động).
- `04_DU_LIEU_DAU_VAO_BXD/project.yaml` khai báo **`track_type: ballastless`**.
- Doc 8-4 xác nhận: γbt=3,5 m/s² (có balát) và **γdf=5,0 m/s² (liên kết trực tiếp)**;
  biến thể mass cận trên/dưới là do **balát** (khô-sạch-mỏng ↔ bão hoà-bẩn-nâng ray).

**Giải thích đã cung cấp**:
- **Biến thể mass = CS-08** (EN 1991-2 6.4.6.3.1): cận dưới m → gia tốc max (DY-03);
  cận trên m → tốc độ cộng hưởng thấp nhất (CS-03/DY-01). Nguồn bất định là balát.
- **SW/0 = ST-03** (chỉ cầu liên tục), **SW/2 = ST-04** (tải nặng, khi có yêu cầu).

**User chốt**: ray **ballastless**; **không cần cả SW/0 và SW/2**.

**Đã làm** (không sinh MCT mới):
- **Sửa giới hạn gia tốc 3,5 → 5,0 m/s²** (γdf ballastless) tại: DY-03 (xlsx),
  Ket_qua_da_co (az envelope + A1@330), `KIEM_TRA_TONG_THE.md`, `README_TONG_THE.md`.
  |az|max=3,373825 → **dự trữ 1,626175 m/s² ≈ 32,5%** (đạt), thay cho ~3,6%.
- **CS-08 → ĐÃ CÓ KẾT QUẢ**: ballastless không có bất định khối lượng balát, mass
  danh nghĩa (self-weight + G2=106,75 kN/m qua *LOADTOMASS) đủ; biến thể balát N/A.
- **ST-03 (SW/0) → KHÔNG ÁP DỤNG** (giản đơn); **ST-04 (SW/2) → KHÔNG ÁP DỤNG** (HSR khách).
  Thêm dòng đếm "Không áp dụng" + COUNTIF vào `Tong_quan`.
- Tổng quan mới: **Đã có 20 / Một phần 6 / Chờ chạy 0 / Chưa đủ 8 / Không áp dụng 2 / Không hội tụ 9 = 45**.

**Lưu ý cho báo cáo**: mốc kết luận gia tốc là 5,0 m/s² (ballastless). Nếu sau này
đổi sang có balát, phải quay lại 3,5 m/s² và chạy biến thể mass balát cận trên/dưới.

## 2026-07-23 — Chia nhỏ MCT gộp cho MIDAS Civil 2022

**Bối cảnh**: File A1 gộp 10 vận tốc, 1.550 time functions và khoảng 5,2 MB
không mở được trong MIDAS Civil 2022 dù kiểm tra chéo tham chiếu MCT hợp lệ.
Tài liệu MCT chính thức cho phép nhiều TFUNCTION/THLDCASE nhưng không công bố
giới hạn số lượng; coi đây là giới hạn thực tế của phiên bản/khối dữ liệu.

**Đã làm**:
- Giữ bộ gộp lớn để truy vết và thêm cảnh báo không sử dụng.
- Tạo `generate_bxd_tgd_chunked_dynamic_cases.py` và sinh 81 MCT chia nhỏ.
- Khóa pilot A1 330+340: 2 TH cases, 310 functions, 310 DYN-NLOAD, 4 graphs.
- Các file khác tối đa 4 case, 620 functions và khoảng 2,12 MB.

**Verify**:
- Tất cả file PASS kiểm tra duy nhất block, tên function/case/graph và tham chiếu
  DYN-NLOAD; vẫn cần MIDAS xác nhận bằng cách import/run pilot.

## 2026-07-23 — HSLM-A1 320/325 và MCT gộp nhiều vận tốc

**Đã làm**:
- Đọc lại toàn bộ kết quả HSLM-A1 bằng skill batch; xác nhận 161/161 sheet
  được đọc, không có sheet lỗi.
- Xác nhận 320 km/h: 155 dynamic inputs, 8303 bước, `dt=0.001 s`,
  `|DZ|max=2.805 mm`, `|aZ|max=2.047736 m/s²`, `|My|max=8651.29 kN.m`.
- Xác nhận 325 km/h: 155 dynamic inputs, 8221 bước, `dt=0.001 s`,
  `|DZ|max=2.227 mm`, `|aZ|max=1.512030 m/s²`, `|My|max=6934.16 kN.m`.
- Thêm `report_tools/generate_bxd_tgd_grouped_dynamic_cases.py`; script ghép
  các MCT đơn theo từng đoàn tàu, tự loại case đã có đủ MCB/OUT/7 workbook.
- Sinh 10 MCT gộp cho 297 case chưa chạy; A1 chỉ gồm 330–420 km/h, A2–A10
  gồm toàn bộ dải theo manifest. Mỗi case giữ tên time function, TH load case
  và TH graph riêng.

**Verify**:
- Tất cả MCT gộp PASS kiểm tra một block động mỗi loại, tên duy nhất và mọi
  tham chiếu DYN-NLOAD được giải quyết.
- `ruff check report_tools/generate_bxd_tgd_grouped_dynamic_cases.py`: PASS.
- `pytest tests/unit/test_static_countercheck.py -q`: 3/3 PASS.
- `verify_bxd_tgd_dossier.py`: PASS_WITH_WARNINGS; hai cảnh báo SW/0 và SW/2
  thuộc phạm vi MCT tĩnh, không phát sinh từ MCT gộp.

## 2026-07-03 — BXD dynamic rerun report + project skills

**Bối cảnh**: Sau khi sửa dynamic end time để dùng chiều dài chuỗi dầm đang
phân tích, user chạy lại MIDAS cho `model_dynamic_countercheck_32_6_HSLM-A1_330`
và export kết quả vào thư mục result tương ứng. Cần đọc lại kết quả, dựng báo cáo
theo form `Tinh_toan_phan_tich_dong.docx`, và tạo skill/harness để tái sử dụng.

**Đã làm**:
- Đọc export mới trong
  `examples/bxd/generated/midas/model_dynamic_countercheck_32_6_HSLM-A1_330/`.
- Xác nhận OUT mới: `155` dynamic inputs, `8142` time steps, `dt=0.001 s`,
  valid DOF `895`, không thấy warning/error chính.
- Đồng bộ bản MCT trong result folder với canonical MCT cấp `generated/midas`;
  cả hai hiện có `ETIME=8.142545455 s`.
- Thêm harness `examples/bxd/generated/midas/build_dynamic_analysis_report.py`
  đọc OUT/Excel/BMP, cập nhật template Word, xuất phụ lục Excel và markdown.
- Tạo báo cáo:
  `bao_cao_tinh_toan_phan_tich_dong_model_dynamic_countercheck_32_6_HSLM-A1_330.docx`.
- Tạo 4 skill dùng lại ở `C:\Users\vupq.CITEC\.codex\skills`:
  `hsr-bridge-project-navigator`, `hsr-mct-dynamic-hardener`,
  `hsr-midas-output-reviewer`, `hsr-dynamic-report-builder`.

**Kết quả chính MIDAS mới**:
- Mode 1: `4.790193 Hz`.
- Modal mass: UZ mode 1 khoảng `15.32%`; UZ sum mode 1-5 khoảng `76.61%`.
- Node giữa nhịp `100016`: `DZ = 1.811 mm`, `|aZ| = 1.188777 m/s²`.
- Gia tốc DZ toàn cục: khoảng `1.195051 m/s²` tại node `100013`.
- Nội lực động: `|My|max = 5682.89 kN.m`, `|Vz|max = 547.05 kN`.

**Verify**:
- `python examples\bxd\generated\midas\build_dynamic_analysis_report.py` PASS.
- Wrapper skill `hsr-dynamic-report-builder/scripts/run_bxd_dynamic_report.py` PASS.
- `quick_validate.py` PASS cho 4 skill mới.

## 2026-06-24 — BXD dynamic countercheck: HSLM-A1 @ 330 km/h

**Bối cảnh**: Sau khi hoàn tất đối chứng tĩnh BXD 32,6 m, chuyển sang mục 5.7
phân tích động HSLM-A để so với báo cáo. Báo cáo khống chế dầm 32,6 m bởi
HSLM-A1 @ 330 km/h, `n0=5,066 Hz`, `amax=2,30 m/s²`, `δmax động=2,97 mm`.

**Đã làm**:
- Thêm `integrations/midas/mct/dynamic_countercheck.py` sinh MCT động riêng
  `model_dynamic_countercheck_32_6_HSLM-A1_330.mct`.
- Reuse dầm-only model và mesh split của `static_countercheck.py` để node giữa
  nhịp vẫn là `100016`.
- Sinh block `*TFUNCTION`, `*THLDCASE`, `*DYN-NLOAD`, `*TH-GRAPH` theo mẫu
  Midas 2022 đã có trong `model_base_review.mct`; damping lấy `0,015`.
- Cập nhật `static_countercheck_32_6.yaml` với cấu hình `dynamic_countercheck`
  cho HSLM-A1, vận tốc 330 km/h, dt 0,001 s.
- Cập nhật `rebuild_comparison_bxd_32_6.py` để thêm 3 dòng mục 5.7 ở trạng
  thái `Chờ export dynamic`; sinh lại comparison workbook/markdown và Word
  so sánh ngắn.
- Cập nhật README/SESSION_STATUS trong thư mục generated.

**Verify**:
- `python -m vbridge_dyn.integrations.midas.mct.dynamic_countercheck` PASS,
  sinh 29 time functions, graph node `100016`, duration `6,704 s`.
- `pytest tests\unit -q`: **61/61 PASS**.
- `ruff check src tests`, `mypy src`: PASS.

**Cần làm tiếp**:
- Import/chạy `model_dynamic_countercheck_32_6_HSLM-A1_330.mct` trong MIDAS.
- Export modal/eigen và TH-Graph `deck acc 32.6`, `deck dz 32.6` để điền kết
  quả mục 5.7 vào bảng so sánh.

## 2026-06-23 — BXD static countercheck: ưu tiên tải tích hợp MIDAS

**Quyết định**:
- Tự trọng G1 không khai báo lại bằng `BEAMLOAD` từ báo cáo; dùng `*SELFWEIGHT`
  để MIDAS tự tính từ hình học mặt cắt và trọng lượng riêng vật liệu.
- LM71 không rải tay bằng node/beam load theo đường ảnh hưởng nữa; khai báo theo
  block moving load của MIDAS (`*MVLDCODE=EUROCODE`, `*LINELANE`, `*VEHICLE`,
  `*MVLDCASE`) để phần mềm tự quét vị trí bất lợi.
- Tải từ báo cáo chỉ dùng cho phần chưa có/ chưa dùng built-in trong MIDAS:
  G2, xe vận chuyển dầm, gió và các hệ số tổ hợp.
- Nếu phải chia thêm node để đặt tải trục xe vận chuyển từ báo cáo thì phải sinh
  kèm `*TS-GROUP` cho các đoạn taper `Box_3_1` và `Box_1_3`; không được để các
  element mới làm mất khai báo biến thiên mặt cắt.

**Đã làm**:
- `static_countercheck_32_6.yaml`: thêm hệ số tổ hợp theo báo cáo và danh sách
  `load_combinations`.
- `static_countercheck.py`: bỏ `G1_REPORT`; thêm moving-load LM71 Eurocode; thêm
  `*LOADCOMB`; giữ split chỉ cho tải trục vận chuyển.
- `writer.py`: bật `bSELFWEIGHT=YES`; mở rộng `*TS-GROUP` để gom theo từng
  tapered section trong group hỗn hợp, ví dụ `1-3` và `3-1`.

**Verify**:
- Sinh lại `examples/bxd/generated/midas/model_static_countercheck_32_6.mct`.
- `pytest -q`: **60/60 PASS**.

## 2026-06-23 — Note limitation parser tendon DXF BXD

**Bối cảnh**: Parser `tendon.dxf` hiện được viết để chạy được bài toán BXD
32.6 m trước, chưa phải convention tổng quát cho mọi cầu/cáp.

**Ghi chú cần sửa sau**:
- Logic hiện tại giả định mỗi layer cáp có đủ mặt đứng + mặt bằng, CAD vẽ 1/2
  dầm và mirror ra full span, rồi gán profile cho toàn bộ group `Girder*`.
- Với bài toán tổng quát cần dùng điểm/block `ref` trên mặt cắt để xác định hệ
  tọa độ local riêng cho từng nhóm cáp, thay vì chỉ lấy tim mặt bằng và đỉnh
  mặt đứng làm gốc quy đổi.
- Danh sách phần tử gán cáp phải đọc từ DXF/CAD convention, không mặc định toàn
  bộ dầm. Cáp ngắn, cáp neo từng đoạn, hoặc cầu thi công phân đoạn có thể chỉ
  đi qua một phần tử/nhóm phần tử con.
- Cần mở rộng schema để lưu `element_ids`/`element_range`, `reference_point`,
  `section_group`, và quy tắc mirror theo từng tuyến cáp.

**Trạng thái hiện tại**:
- BXD `tendon.dxf` đọc được 13 layer × 5 girder groups = 65 tendon profiles.
- Đã đọc được `prototype_element_ids` và `section_reference` để audit, nhưng
  chưa dùng làm quy tắc gán/phép biến đổi tổng quát.

## 2026-06-02 — Giữ nguyên số điểm OPOLY/IPOLY từ DXF

**Bối cảnh**: Owner hỏi vì sao `IPOLY` của mặt cắt 1 và 3 khác số điểm dù DXF
cùng số đoạn. Nguyên nhân: MCT writer đang gọi `_simplify_polygon()` trước khi
ghi `OPOLY/IPOLY`, nên các điểm nằm trên cùng đường thẳng bị xóa.

**Đã sửa**:
- `sections.py`: bỏ simplify ở bước output polygon; chỉ còn dùng polygon đã
  simplify cho tính STIFF3/stress points.
- `OPOLY/IPOLY` giờ giữ nguyên số điểm sau khi DXF reader chia/trace loop.
- Thêm unit test đảm bảo điểm thẳng hàng trong outer boundary và hole không bị
  xóa khi ghi MCT.

**Verify**:
- Sinh lại `model_base.mct`.
- `Box-01`: `OPOLY=48`, `IPOLY=12`; `Box-03`: `OPOLY=48`, `IPOLY=12`.
- Tapered `Box-1-3` và `Box-3-1` cũng giữ 48/12 ở cả đầu YES/NO.
- `pytest tests\unit -q`: **56/56 PASS**.
- `ruff check src tests`, `ruff format --check src tests`, `mypy src`: PASS.

## 2026-06-02 — Đối chiếu `model_base_review.mct`

**Bối cảnh**: Owner chỉnh model trong Midas và lưu `examples/hcm_cg/generated/midas/model_base_review.mct`;
yêu cầu đối chiếu, cập nhật ngược về nguồn sinh.

**Đã cập nhật vào nguồn**:
- `bridge.xlsx`: từ review nhập thêm 40 node bearing `6605..6644`.
- `bridge.xlsx`: cập nhật section assignment của 80 element dầm chính theo review:
  `Box_03` ở vùng đầu/cuối, `Box_01` giữa nhịp, tapered `Box-3-1` tại element
  `103/203/303/403/503`, tapered `Box-1-3` tại element `114/214/314/414/514`.
- `bridge.xlsx`: thêm sections tapered `Box_1_3` (`Box_01 -> Box_03`) và
  `Box_3_1` (`Box_03 -> Box_01`).
- `bridge.xlsx`: thay rigid links theo review: 10 link dầm chính → bearing nodes,
  6 link đầu cọc → đáy bệ, 6 link đỉnh trụ → bearing nodes.
- `bridge.xlsx`: thêm 20 elastic links dạng bearing với `dof_mask` lấy từ review
  (`bearing_01`: `111000`, `bearing_02`: `110000`).
- `bridge.xlsx`: thêm boundary groups `bearing_01..bearing_04`.
- `project.yaml`: `analysis.n_modes = 70` để khớp `*EIGEN-CTRL`.

**Đã mở rộng code generator**:
- `ElasticLink` schema + Excel reader/template đọc `dof_mask`, `angle`, `sd_i`, `sd_j`.
- MCT writer xuất `*BNDR-GROUP`, `*ELASTICLINK`, `*TS-GROUP`, `*LOADTOMASS`,
  `*EIGEN-CTRL`.
- Rectangle đặc xuất `DBUSER ... SB` để khớp Midas export.
- Tapered section name dùng `section.name`, không dùng `section.id`.

**Đối chiếu sau generate**:
- Khớp review về count các block chính: 341 node, 254 element, 4 boundary groups,
  2 `*SECTION`, 6 `*TS-GROUP`, 20 `*ELASTICLINK`, 22 `*RIGIDLINK`,
  2 `*LOADTOMASS`, 1 `*EIGEN-CTRL`.
- `*NODE` và `*ELEMENT` khớp ID + value với review.

**Chưa cập nhật / cần owner xác nhận**:
- Review có raw dynamic case HSLM-A1 250 km/h: `*TFUNCTION` 6460 dòng,
  `*THLDCASE` 3 dòng, `*DYN-NLOAD` 85 dòng. Chưa đưa vào generator vì project
  hiện vẫn thiếu train catalog/schema để sinh lại có kiểm soát. Cần xác nhận có
  muốn copy raw block này như một case tạm thời hay chờ pipeline dynamic đúng.

**Verify**:
- `vbdyn generate examples\hcm_cg --target midas` PASS.
- `vbdyn validate examples\hcm_cg` PASS bridge/schema/support; FAIL duy nhất `Trains`.
- `pytest tests\unit -q`: **55/55 PASS**.
- `ruff check src tests`, `ruff format --check src tests`, `mypy src`: PASS.

## 2026-06-02 — Sửa hướng cọc, pilecap đặc, taper 01→02

**Bối cảnh**: Review sau khi dựng phần dưới: layout cọc bị nhầm phương dọc/ngang;
pilecap phải là hình chữ nhật đặc 7.5×10.5, chỉ lấy layer `pilecap`; thân trụ taper
phải từ mặt cắt nhỏ đến to (`Pier_01 -> Pier_02`) theo chiều dưới lên; chiều dài cọc
sửa thành 8 m.

**Đã làm**:
- `workbook_reader.py` + template Excel: thêm cột `dxf_layer` và `dxf_axis_order`
  (`xy` mặc định, `yx` để đảo trục DXF khi map sang local section Y-Z).
- `examples/hcm_cg/bridge.xlsx`: `Pilecap` đọc `dxf/Pilecap.dxf` với
  `dxf_layer=pilecap`, `dxf_axis_order=yx`; section sinh ra đặc, bbox local
  `Y=7.5 m`, `Z=10.5 m`, không còn `IPOLY` từ các circle cọc; writer xuất
  built-in `SB , BUILT, 7.5, 10.5` trong `*SECTION`.
- Layout cọc đổi thành 2 cột dọc cầu `x = pier_x ± 2.25 m` và 3 hàng ngang
  `y = -3.75, 0, +3.75 m`.
- Cọc dài 8 m từ đầu cọc `z=-2.5` đến chân cọc `z=-10.5`, chia 4 phần tử 2 m
  qua các node `...00 -> ...04`.
- `Pier_Taper` đổi hướng `taper_start_section_id=Pier_01`,
  `taper_end_section_id=Pier_02`; MCT `OPOLY=YES` là section nhỏ, `OPOLY=NO`
  là section lớn.
- Sinh lại `generated/midas/model_base.mct` thành công.

**Verify**:
- `vbdyn generate examples\hcm_cg --target midas` PASS.
- `vbdyn validate examples\hcm_cg` PASS bridge/schema/support; FAIL duy nhất
  `Trains` vì chưa import catalog HSLM/LM71/real train.
- `pytest tests\unit -q`: **54/54 PASS**.
- `ruff check src tests`, `ruff format --check src tests`, `mypy src`: PASS.

## 2026-06-02 — HCM-CG base model: bệ, cọc, thân trụ taper

**Bối cảnh**: Midas báo lỗi `Material Name` quá 16 ký tự và owner yêu cầu bổ sung
mô hình phần dưới: bệ `1000->1001 ... 6000->6001`, cọc theo `Pilecap.dxf`, đầu cọc
rigid link vào đáy bệ, thân trụ taper `1001->1005 ... 6001->6005`, boundary support
tại chân cọc.

**Đã làm**:
- `integrations/midas/mct/writer.py`: xuất tên vật liệu bằng `material.id` ngắn
  (`C50`, `C40`, `C30`, `CB240T`, `CB400V`, `PC270`) để thỏa giới hạn 16 ký tự của
  Midas Civil.
- Mở rộng schema/Excel/writer cho mặt cắt taper: sheet `Sections` có
  `taper_start_section_id`, `taper_end_section_id`; writer sinh `SECT=..., TAPERED`
  với cặp polygon `YES/NO`.
- Cập nhật `examples/hcm_cg/bridge.xlsx`: 301 node, 254 element, 6 material,
  9 section. Có 6 bệ, 24 phần tử thân trụ taper, 144 phần tử cọc, 36 support tại
  chân cọc, 6 rigid links từ node đáy bệ tới các node đầu cọc.
- Mặt cắt: `Pilecap` lấy từ `dxf/Pilecap.dxf`; `Pile_D1500` xuất DBUSER tròn đặc;
  `Pier_Taper` dùng `Pier_02` ở đáy và `Pier_01` ở đỉnh theo chiều element từ dưới
  lên.
- Sinh lại `examples/hcm_cg/generated/midas/model_base.mct` và manifest thành công.

**Giả định cần nhớ**:
- Chiều dài cọc lấy từ `1_du_an/hcm_cg/input_parameters.yaml`: 55 m; mỗi cọc chia
  4 phần tử, node từ trên xuống dưới.
- Tọa độ cọc lấy theo 6 tâm circle trong `Pilecap.dxf`.
- `Pilecap.dxf` đang được đọc như section polygon chữ nhật có 6 lỗ tròn; nếu file này
  thực ra là mặt bằng bệ chứ không phải mặt cắt, cần thay DXF mặt cắt bệ riêng.
- Chưa thêm liên kết gối/dầm chính với trụ; phần này cần dữ liệu bearing/link riêng.

**Verify**:
- `vbdyn generate examples\hcm_cg --target midas` PASS.
- `vbdyn validate examples\hcm_cg` PASS bridge/schema/support; FAIL duy nhất `Trains`
  vì chưa import catalog HSLM/LM71/real train.
- `pytest tests\unit -q`: **51/51 PASS**.
- `ruff check src tests`, `ruff format --check src tests`, `mypy src`: PASS.

## 2026-06-01 — Static load blocks cho MCT writer

**Bối cảnh**: v0.2 còn thiếu load blocks. File mẫu
`3_ho_so_tham_khao/template_mct/16 Eurocode Rail loads Final.mct` có đủ cú pháp
`*STLDCASE`, `*USE-STLD`, `*SELFWEIGHT`, `*BEAMLOAD`; chưa có sample cục bộ cho
`*EIGEN-CTRL` nên không đoán field layout modal.

**Đã làm**:
- `integrations/midas/mct/writer.py`: sinh `*STLDCASE` với load case `SW` và
  các case `DW <group>` cho `distributed_masses` hợp lệ.
- Sinh `*USE-STLD, SW` + `*SELFWEIGHT` (`0, 0, -1`) để model base có dead load
  self-weight theo vật liệu.
- `distributed_masses`: resolve `target_group` theo `StructureGroup.id`,
  `StructureGroup.name`, hoặc `Element.structure_group`; cộng dồn kg/m theo
  group; quy đổi sang force/length theo unit Midas hiện tại; xuất `*BEAMLOAD`
  `UNILOAD GZ` trên từng element. Group không có phần tử → warning, bỏ qua.
- Tests: thêm ca distributed mass → beamload. **49/49 PASS**, ruff format/check
  + mypy strict sạch.

**Follow-up còn lại**: `*EIGEN-CTRL` modal vẫn chờ file MCT mẫu Midas 2022 (B1);
`NodalMasses`/`ElementRelease`/`ElasticLinks` vẫn đang warning chưa export.

## 2026-06-01 — STIFF2 mesh vertices + LWPOLYLINE bulge

**Bối cảnh**: follow-up còn mở sau checkpoint ARC/CIRCLE + circle→DBUSER:
STIFF2 của `*SECT-PSCVALUE` cần lấy từ mesh vertices giống reference Converte;
DXF reader cần khóa support LWPOLYLINE có bulge cong.

**Đã làm**:
- `integrations/midas/mct/sections.py`: STIFF2 (`CyP/CyM/CzP/CzM/Cy/Cz`) lấy
  extents từ `section_model.mesh["vertices"]` sau khi trừ centroid, fallback về
  `outer_boundary` nếu mesh không có vertices. Đây là hành vi của
  `4_cong_cu/rm2midas/src/pipeline/step_020_json_to_mct.py`.
- `importers/dxf/section_reader.py`: xử lý trực tiếp `LWPOLYLINE` bằng
  `entity.get_points("xyb")`; cạnh có `bulge` được chuyển sang arc qua
  `ezdxf.math.bulge_to_arc` rồi chia theo `arc_angle_deg` (mặc định 10°).
- Tests: thêm 2 ca — STIFF2 ưu tiên mesh vertices; LWPOLYLINE bulge=1 tạo vòng
  tròn D=2 m và chia đúng số đoạn theo góc. **48/48 PASS**, ruff format/check +
  mypy strict sạch.

**Follow-up còn lại**: mở rộng writer `*STLDCASE`/`*SELFWEIGHT`/`*BEAMLOAD` (DW)
và `*EIGEN-CTRL`; dựng model 5 nhịp HCM-CG thật từ `1_du_an/hcm_cg/input_parameters.yaml`.

## 2026-06-01 — ARC chia theo góc (10°) + detect_circle→DBUSER

**Quyết định** (theo yêu cầu owner sau khi xác nhận MG_01 hiển thị đúng trong Midas):
chia ARC mặc định góc 10°; mặt cắt tròn xuất DBUSER. Đã commit checkpoint `38bb43a`
TRƯỚC khi làm 2 việc này.

**Đã làm**:
- `importers/dxf/section_reader.py`: `ARC`/`CIRCLE` chia theo **bước góc**
  (`arc_angle_deg`, mặc định **10°** — khớp Midas SPC) thay cho sagitta;
  `ELLIPSE`/`SPLINE` vẫn flatten theo sagitta. CIRCLE → vòng kín 36 đỉnh.
- `integrations/midas/mct/sections.py`: thêm `detect_circle()` + `CircleInfo` (port
  từ Converte `core/geometry`): hệ số biến thiên bán kính < 2% ⇒ tròn đặc (SR) /
  ống (P, 1 lỗ tròn đồng tâm).
- `integrations/midas/mct/writer.py`: tách section thành **2 khối** — `*SECTION`
  (DBUSER SR/P cho mặt cắt tròn, vd cọc D1500) + `*SECT-PSCVALUE` (GEN polygon còn lại).
- Tests: +3 (circle chia 10° = 36 đỉnh, override góc 30° = 12 đỉnh, circular section
  → DBUSER SR). **46/46 PASS**, ruff + mypy strict sạch.

**Verify**: CIRCLE D1.5 trong DXF → 36 đỉnh → `detect_circle` ra SR D≈1.5 → dòng
`*SECTION … DBUSER … SR`. MG_01 dầm hộp vẫn ra `*SECT-PSCVALUE` + OPOLY (KHÔNG nhận
nhầm tròn).

**Follow-up**: đổi STIFF2 sang mesh vertices; hỗ trợ LWPOLYLINE có bulge cong.

---

## 2026-06-01 — DXF section importer + vá writer fallback OPOLY

**Bối cảnh**: Midas không hiển thị mặt cắt vì writer phát `SHAPE=GEN` mà **thiếu
OPOLY** (section chỉ có A/Iy/Iz/J, không polygon → đi nhánh fallback). Owner xác
nhận nguồn mặt cắt = file DXF (`1_du_an/hcm_cg/dxf/MG_01.dxf`).

**Quyết định** (qua AskUserQuestion):
- Section tham chiếu DXF qua **cột `dxf_file`** trong sheet Sections.
- Trích hình bằng **auto-chain toàn modelspace** (prune nhánh hở, vòng lớn nhất = bao ngoài).

**Đã làm**:
- Module mới `importers/dxf/section_reader.py` (`read_section_polygon`): ezdxf → gom
  LINE/ARC/POLYLINE/INSERT thành đoạn → đổi đơn vị theo `$INSUNITS` → nối đồ thị →
  **prune đỉnh bậc ≤ 1** (tự loại dimension/leader/text) → trace vòng kín → vòng lớn
  nhất = outer, còn lại = holes; map DXF(x,y)→section(y,z). Thêm `ezdxf>=1.1` vào extra `[sections]`.
- `workbook_reader.py`: đọc cột `dxf_file` (resolve theo thư mục workbook qua `base_dir`);
  A/Iy/Iz/J cho phép trống khi có polygon (placeholder 1.0, writer tính lại).
- `bridge_template_writer.py`: thêm cột `dxf_file` + note hướng dẫn 2 cách nhập hình.
- **Vá writer fallback** (`writer.py`): section không polygon → tự sinh **OPOLY chữ
  nhật** (±cy, ±cz) + warning; GEN section giờ LUÔN có hình hiển thị.
- Tests: `test_dxf_section_reader.py` (4 ca: outer+hole, mm→m, chuỗi hở raise, vòng
  lớn nhất=outer) + assert `OPOLY=` ở init template. **43/43 PASS**, ruff + mypy strict sạch.

**Verify thật trên MG_01.dxf** (đối chiếu file Midas đã chạy `MG-001`):
- `$INSUNITS=6` (m); dimension text khớp 1:1 hình học (H=3000↔3.0, ttop=300↔0.3, 7604↔7.6039).
- Trích: bao ngoài 14 đỉnh + 2 lỗ 7 đỉnh; shapely valid; net area **20.93 m²**.
- `vbdyn generate examples/hcm_cg` → `*SECT-PSCVALUE` đầy đủ STIFF1/2/3 + OPOLY + 2
  IPOLY, prefix CT — **cấu trúc giống hệt file thật**. Đã copy MG_01.dxf + thêm cột
  `dxf_file`/`mesh_size` vào `examples/hcm_cg/bridge.xlsx`.

**Cần owner xác nhận**: MG_01 rộng **35 m** (±17.5) × cao 3 m, 2 lỗ ở cánh — lệch
12.6 m trong `input_parameters.yaml` trước đó (có thể là section vẽ thử hôm nay).

**Follow-up**: hỗ trợ ARC/bulge cho mặt cắt trụ cong (MG_01 toàn LINE nên chưa cần);
port `detect_circle`→DBUSER cho cọc tròn.

---

## 2026-06-01 — Sync v0.2 + research sub girder & verify section generation

**Bối cảnh**: code đã đi trước tracking docs (4 commit v0.2 chưa log). Phiên này
đồng bộ docs + research thêm sub girder cho tải tàu + đối chiếu pipeline mặt cắt với
code tham khảo `3_ho_so_tham_khao/020_Chuyển_json_sang_mct_và_gan_mat_cat_V4.py`.

**Đã log các commit v0.2 (trước đó chưa ghi)**:
- `538f544` feat(v0.2): MCT generator đầu tiên (writer + generator + CLI `generate --target midas`).
- `c3fc17a` fix(mct): bỏ group boundary chưa khai báo.
- `11247f0` feat(mct): sinh polygon section OPOLY/IPOLY.
- `ea06a75` feat(excel): import polygon section geometry.
- Writer hiện sinh: header + `*NODE` + `*ELEMENT` + `*GROUP` + `*MATERIAL`(+color) +
  `*SECT-PSCVALUE` (polygon hoặc fallback stiffness-only) + `*CONSTRAINT` + `*RIGIDLINK`.
  Manifest mới sinh 1 case modal (`case_modal_base`). Test **39/39 PASS**.

**Verify mặt cắt (đối chiếu V4 + bản production Converte `src/`)**:
- `integrations/midas/mct/sections.py` của vbridge **KHỚP thuật toán ĐÃ KIỂM CHỨNG**
  trong `Converte_RM_to_Midas/src/core/geometry.py` (STIFF3 = max Euclidean distance từ
  centroid trên boundary đã simplify; 100% match 38 file Midas SPC). **KHÔNG** phải bản
  `020...V4.py` cũ — V4 dùng mesh vertices + tolerance top/bottom region, đã bị thay thế.
  STIFF1, arrangement STIFF3, thứ tự OPOLY (CCW từ Q1) / IPOLY (CW) đều khớp production.
- 3 điểm lệch so với bản production cần xử lý:
  1. **STIFF2 (CyP/CyM/CzP/CzM)**: vbridge lấy từ `translated_outer` (boundary đã
     simplify); production lấy từ **mesh vertices** (`section.mesh["vertices"]`). Cùng kết
     quả với mặt cắt cạnh thẳng → nên đổi sang mesh vertices cho đúng 100% reference (an
     toàn cả mặt cắt cong). Rủi ro thấp.
  2. **Thiếu circle→DBUSER**: production `detect_circle` → xuất `DBUSER SR/P` cho mặt cắt
     tròn/ống; vbridge luôn xuất GEN polygon. Ảnh hưởng **cọc D1500 HCM-CG** → nên port.
  3. Ngưỡng lọc hole: vbridge `< 3` điểm, production `< 4`. Edge case nhỏ.
- Lưu ý: example `examples/hcm_cg` hiện chỉ có section dạng stiffness (không polygon) nên
  nhánh polygon mới được cover bằng `test_mct_generation.py` (rectangle), chưa chạy trên
  dầm hộp thật.

**Research sub girder (chi tiết → `1_du_an/hcm_cg/SUB_GIRDER_RESEARCH.md`)**:
- `*LINELANE` template: track **tĩnh** Eurocode = element-list + ECC ngang trên phần tử
  có sẵn (KHÔNG cần sub girder). Sub girder 601..785 chỉ cần khi dùng Train Load Generator
  (time-history **động**) — đúng strategy mặc định HCM-CG.
- Đã xác nhận TÊN block MCT động (MIDAS manual): `*EIGEN-CTRL`, `*TFUNCTION`, `*THLDCASE`,
  `*DYN-NLOAD` (+ `*MOVE-CTRL`/`*MVLDCASE` cho moving load tĩnh). Field layout vẫn cần file
  mẫu (B1).

**Liên kết research vào repo**: thêm trỏ tới `1_du_an/hcm_cg/` (MODEL_UNDERSTANDING,
SUB_GIRDER_RESEARCH, input_parameters.yaml) trong `CLAUDE.md` §8 + `PROJECT_STATUS.md`.

**Lý do**: tránh repo lệch khi chuyển máy/agent; chốt rằng pipeline mặt cắt đang theo
đúng bản đã validate; làm rõ điều kiện cần sub girder trước khi code v0.2 dynamic.

**Blockers**:
- B1 cập nhật: đã biết TÊN block time-history, vẫn cần file MCT mẫu Midas 2022 để lấy
  field layout + cách Train Load Generator sinh `*DYN-NLOAD`/`*TFUNCTION`.

---

## 2026-05-29 — Fix mypy, lock manifest schema, đổi tên test (P1-P3 follow-up)

**Quyết định** (theo review user):

- **P1 — Fix 9 mypy errors** (CI sẽ fail nếu không fix):
  - `train.py:36`: `catalog_meta: dict` → `dict[str, Any]` (thêm `from typing import Any`)
  - `workbook_reader.py:23`: thêm type `ws: Worksheet`
  - `workbook_reader.py:188`: signature `read_bridge_workbook() -> Bridge` → `tuple[Bridge, list[Track]]` (đúng với thực tế trả 2-tuple)
  - `workbook_reader.py:202`: thêm type `wb: Workbook` cho `_read_tracks`
  - `project_io.py:6` + `validate.py:8`: thêm `types-PyYAML>=6.0` vào dev deps
  - `validate.py:45`: `tracks_from_excel: list` → `list[Track]` (import Track)
  - `validate.py:48`: type của `raw` được khóa `dict[str, Any]`, tuple unpack từ read_bridge_workbook giờ đúng type
  - `pyproject.toml`: dọn `[[tool.mypy.overrides]]` chỉ giữ `openpyxl.*` (các deps khác đã có stubs hoặc không import)
  - Verify: `mypy src` → "Success: no issues found in 28 source files"

- **P2 — Lock `generation_manifest.json` schema** (acceptance v0.1):
  - `core/schemas/manifest.py`: `GenerationManifest` + `CaseEntry` + `StationRef`
  - Trường chính: target, target_version, run_id, generated_at, vbridge_dyn_version, project_name, project_hash, case_split_strategy, moving_load_strategy, cases (list), output_dir, expected_solver_outputs_dir
  - CaseEntry: case_name, case_kind (modal | time_history | static_envelope), mct_file, expected_csv_name, train_id, velocity_kmh, stations, signals, midas_load_case_name, time_history_case_name
  - StationRef: station_id, midas_node_ids, midas_element_ids, interpolation (direct | linear), eta
  - Helper properties: n_cases, trains_covered, velocities_kmh
  - 8 tests trong `test_manifest_schema.py`: required fields, train coverage, velocities, case kinds, interpolation modes, JSON roundtrip + file IO, grouped_by_train invariant, validation negative cases
  - Re-export trong `core/schemas/__init__.py`
  - Wording PROJECT_STATUS.md: "v0.1 skeleton hoàn tất" → "foundation skeleton complete; v0.1 acceptance đã đạt" để chính xác (vẫn in-progress về tuần 1/3 nhưng đã đạt acceptance)

- **P3 — Đổi tên test cho đúng coverage thật**:
  - `test_validate_empty_bridge_reports_failures` → `test_validate_template_only_reports_missing_trains` (rõ ràng: template có sample hợp lệ nên Bridge PASS, chỉ FAIL vì Trains rỗng — đó là expected behavior)
  - Thêm test mới `test_validate_missing_supports_fails_bridge_check`: xóa Supports khỏi bridge.xlsx bằng openpyxl → validate fail ngay ở bridge level (cover scenario user xóa data)

**Verify final**:
- ruff check: PASS
- ruff format --check: PASS
- mypy src: 28 files, no issues
- pytest tests/unit: 33/33 PASS (24 cũ + 8 manifest + 1 missing supports = 33)

---

## 2026-05-29 — v0.1 skeleton chạy được (init + validate + tests)

**Đã làm**:
- `pyproject.toml`: pip + uv compat, hatchling build, deps cứng (pydantic v2, typer, rich, pyyaml, pandas, openpyxl, numpy, scipy, pyarrow, matplotlib, reportlab, jinja2, loguru, h5py), optional `ui` (PySide6/pyqtgraph/pyvista), `sections` (sectionproperties/shapely/chardet), `dev` (pytest/hypothesis/ruff/mypy/pre-commit).
- `src/vbridge_dyn/` skeleton:
  - `core/schemas/`: units, geometry, properties, boundary, mass, groups, track, train, analysis, result_station, bridge, project (12 modules + __init__).
  - `io/`: project_io (YAML load/save), project_templates (sinh project.yaml mẫu).
  - `importers/excel/`: bridge_template_writer (11 sheets có sample + comment tiếng Việt) + workbook_reader (parse → Bridge schema).
  - `cli/main.py` + `cli/commands/{init,validate}.py`: Typer app với `--version`, `info`, `init`, `validate`. Validate tự load bridge.xlsx khi project.yaml bridge rỗng.
- Tests: 23/23 PASS
  - `test_schemas.py` (17 tests): Bridge ref consistency, Support binary, RigidLink dof_mask, ElementRelease, Track accel_limit, ResultStation target, Project defaults
  - `test_cli_init_validate.py` (4 tests): init creates folders, validate empty fails, info, --version
  - `test_excel_template_roundtrip.py` (2 tests): write template → read back → check schema
- Lint: ruff check + format clean (allow `×`, `≡`, `≥`, `°` Unicode khoa học; allow Typer B008 idiom + physics N815 cho alpha_T).
- CI workflow `.github/workflows/ci.yml`: lint+mypy + tests trên ubuntu+windows × py3.11/3.12 + schedule weekly cho V03-V05/V09 reference benchmarks.
- `.gitignore` + `LICENSE` (Apache-2.0).
- `examples/hcm_cg/` init thành công, validate ra hầu hết PASS (chỉ FAIL Trains vì user chưa import HSLM/LM71 từ Excel — B2 blocker, expected).

**Quyết định kỹ thuật**:
- Validate dispatch: nếu `project.yaml > bridge` rỗng và `bridge.xlsx` tồn tại → tự load Excel merge vào Bridge schema. User không cần copy data từ Excel sang YAML.
- Template `bridge.xlsx`: 11 sheets (Nodes/Elements/Materials/Sections/Supports/ElasticLinks/RigidLinks/NodalMasses/DistributedMasses/StructureGroups/Tracks) + `_README` sheet với hướng dẫn tiếng Việt. Đơn vị nội bộ SI; exporter sẽ tự đổi.
- Project.yaml: comment tiếng Việt dẫn dắt từng block (standards_profile, tcvn13594_versions, design, dynamic, velocity_range, analysis, targets, checks, report).

**Đã reverse-engineer MCT mẫu** (`3_ho_so_tham_khao/template_mct/16 Eurocode Rail loads Final.mct`, Midas 9.1.0, 2534 dòng, 36 sections):
- File mẫu dùng pattern **moving load Eurocode** (`*MVLDCODE=EUROCODE`, `*LINELANE`, `*VEHICLE`, `*MVLDCASE(EURO)`, `*MV-DYFG`, `*MOVE-CTRL`) — đây là **static moving load + DAF** (giải pháp cho LM71/SW/0/SW/2), KHÔNG phải dynamic time-history.
- Để làm **dynamic transient HSLM** (theo plan: `moving_load_strategy: time_history_function`) cần thêm `*EIGEN-CTRL`, `*TIME-HISTORY-FUNCTION`, `*TIME-HISTORY-LOAD`, `*TIME-HISTORY-CASE`, `*MODAL-DAMPING`. v0.2 sẽ research thêm sample MCT có time-history.
- Tham khảo `4_cong_cu/rm2midas` (private, PhamVu1505): pipeline 12 steps (010-095), `sectionproperties` lib để tính Area/Iy/Iz/J/Asy/Asz từ outer boundary, ECC→Rigid Link conversion, STIFF3 max Euclidean distance from centroid (đã validated 100% match Midas SPC trên 38 file).

**Blockers**:
- B1 (vẫn open): cần thêm MCT mẫu có **time-history block** + có HSLM time function — để v0.2 sinh được full dynamic case.
- B5 (mới): repo push lên GitHub bị auto mode chặn — user cần chạy `!gh repo create vbridge-dyn --private --source=... --remote=origin --push` thủ công, hoặc cấp permission.

---

## 2026-05-29 — Sửa 3 điểm còn lệch sau review P1-P3

**Quyết định** (theo review tiếp theo của user):

- **PLAN_REV9.md §Verification & Validation** đồng bộ với CLAUDE.md §7: tách
  thành 2 nhóm
  - **Hard benchmarks** (V01-V02 analytical + V06-V07 parity + V08 Phase 2 +
    V10 Phase 3) — tolerance cứng, CI gate
  - **Reference comparisons** (V03-V05 + V09) — soft, chỉ nâng lên cứng khi có
    file model gốc trong repo.
- **Rule test trên PR đồng bộ** ở 3 file:
  - CLAUDE.md §9 conventions: V01-V02 + V06-V07 mỗi PR; V03-V05/V09
    weekly/on-demand; V08/V10 theo phase.
  - AGENTS.md §6: cùng nội dung, format ngắn gọn.
  - PLAN_REV9.md §V&V: thêm subsection "CI chính sách" rõ ràng.
- **README.md §Vai trò bước 4**: "Eurocode/TCVN checks" → "checks theo
  `standards_profile` (mặc định TCVN 13594, Eurocode cross-check)" để phản ánh
  đúng quyết định TCVN là chính.

**Đã làm**:
- Edit `docs/PLAN_REV9.md`: bảng V&V tái cấu trúc thành 2 nhóm + CI policy.
- Edit `CLAUDE.md`: line "Test V01-V07 ... V08-V09 ..." sửa thành mô tả Hard
  vs Reference comparisons.
- Edit `AGENTS.md`: §6 "Test trước khi commit" sửa cùng nội dung.
- Edit `README.md`: "Eurocode/TCVN checks" → "checks theo standards_profile".

**Lý do**: 3 file (plan + claude.md + agents.md) phải nhất quán về benchmark
groups và CI rules, nếu không reviewer mới hoặc agent khác đọc sẽ thấy mâu
thuẫn — đó là root cause của review này.

---

## 2026-05-29 — Áp dụng review P1-P3 trước khi vào v0.1

**Quyết định** (theo 5 điểm review user nêu):

- **P1**: Plan rev9 đã được **copy vào repo** tại
  [`docs/PLAN_REV9.md`](./docs/PLAN_REV9.md). Mọi reference trong CLAUDE.md +
  PROJECT_STATUS.md trỏ về đường dẫn nội bộ thay vì
  `C:\Users\...\.claude\plans\...`. Repo trở thành self-contained, chuyển máy
  / agent khác vẫn có plan đầy đủ.
- **P2 (1)**: Thêm `AGENTS.md` ở repo root — entry point ngắn cho mọi agent
  (Codex, Cursor, dev mới). Nội dung: đọc 3 file (CLAUDE.md, PROJECT_STATUS.md,
  TASK_LOG.md) trước khi sửa code; 3 nguyên tắc MVP; quy tắc handoff.
- **P2 (2)**: Tách bảng Benchmarks trong CLAUDE.md §7 thành **2 nhóm rõ**:
  - **Hard benchmarks** (V01, V02, V06, V07, V08, V10) — có analytical/parity
    rõ → tolerance cứng, CI gate.
  - **Reference comparisons** (V03 KD-Railway, V04 HS2 eigen, V05 HS2 envelope,
    V09 HSR HCM-CG) — chỉ có PDF, **chưa có file model gốc** → soft acceptance
    (xu hướng + order-of-magnitude + report layout). Khi có file model thật
    mới đổi sang tolerance cứng.
  - Phù hợp với quyết định "soft" đã ghi ở rev7.
- **P3 (1)**: README.md sửa diễn đạt "Sinh `.mct` cho **từng case**" → "sinh
  `.mct` theo strategy đã chọn (mặc định `grouped_by_train`: 1 file/train,
  nhiều velocity cases)" + nhắc rõ `generation_manifest.json` bắt buộc.
- **P3 (2)**: PROJECT_STATUS.md v0.1 checklist thêm 2 task tách riêng:
  - `generation_manifest.json` schema + writer (pydantic)
  - `export_instructions.md` template generator
  Acceptance v0.1 mới thêm dòng: "manifest schema được khóa với sample output".
  Acceptance v0.2 cập nhật: phải có manifest đầy đủ cho case modal.

**Đã làm**:
- Tạo `vbridge-dyn/docs/` folder; copy plan `t-i-mu-n-ph-t-tri-n-polished-walrus.md` thành `docs/PLAN_REV9.md` (60 KB).
- Tạo `vbridge-dyn/AGENTS.md` (entry point).
- Edit `CLAUDE.md`: header tham chiếu AGENTS.md, mapping pointer đổi sang
  `docs/PLAN_REV9.md`, §7 Benchmarks tách 2 bảng, §8 đổi pointer plan.
- Edit `README.md`: diễn đạt MCT generation strategy, link AGENTS/PLAN_REV9.
- Edit `PROJECT_STATUS.md`: refs plan, v0.1 checklist thêm manifest/export
  guide, v0.1 acceptance thêm manifest schema, v0.2 acceptance bổ sung.

**Lý do**: theo review của user, repo phải self-contained, các agent ngoài
Claude cũng có entry point, benchmark V03-V05 không được đặt cứng khi chưa có
file model gốc, và manifest là xương sống MVP nên phải first-class trong
checklist.

---

## 2026-05-29 — Plan rev9 chốt + project tracking files

**Quyết định**:
- Tổ chức tracking với **4 file md ở root repo**:
  - `README.md` (cho người mới vào repo, tiếng Việt)
  - `CLAUDE.md` (auto-load cho Claude, single source of truth về kiến trúc)
  - `PROJECT_STATUS.md` (snapshot hiện tại, update khi đổi version/milestone)
  - `TASK_LOG.md` (history append-only, file này)
- Quyết định chọn phương án A "3 file gọn" + README riêng (qua AskUserQuestion).
- Lý do: tránh phân mảnh và mâu thuẫn nội dung như khi có 7 file (TASK_CURRENT
  + TASK_NEXT + SCOPE riêng).

**Đã làm**:
- Tạo `C:\Backup\D\2026\09_Tinh_toan_cau_duong_sat_toc_do_cao\4_cong_cu\vbridge-dyn\`
- Tạo `README.md`, `CLAUDE.md`, `PROJECT_STATUS.md`, `TASK_LOG.md`

---

## 2026-05-29 — Plan rev8: MVP chốt với Midas Civil 2022

**Quyết định**:
- `midas_version: "2022"` mặc định (KHÔNG 2024/NX).
- Reverse-engineer MCT bắt buộc từ Midas Civil 2022.
- **Civil NX/API → v1.2+ future**, KHÔNG nằm trong MVP.
- `runner.py` optional ngoài MVP, không trong acceptance.
- Thêm vào `generated/midas/`:
  - `generation_manifest.json` — map case → train/velocity/CSV expected/stations/nodes
  - `export_instructions.md` — hướng dẫn user export từ Midas thủ công
  - `result_export_template.xlsx` — template để chuẩn hóa CSV ingest
- `case_split: grouped_by_train` default → ~10-11 file MCT cho 500 cases
  (gộp velocities cùng train), file tên `case_th_hslm_a1.mct` không
  `case_th_hslm_a1_v140.mct`.
- Pipeline `[8]` đổi "Eurocode checks" → "checks (dispatch theo
  standards_profile)".
- Pipeline `[9]` PDF "13 mục" (không 11).
- UI status sửa "Generated 11 .mct files / 510 cases (grouped_by_train)".

**Lý do**: anh xác nhận có license Midas Civil 2022, không có Civil NX. Yêu cầu
MVP chỉ sinh model + user chạy tay + ingest CSV.

---

## 2026-05-29 — Plan rev7: Consistency

**Quyết định**:
- TCVN 13594-4 mặc định **2022** (override "2023" nếu cần). Tra VSQI: TCVN
  13594-4:2022 còn hiệu lực.
- `dynamic_required.py` comment trung tính: "kiểm tra theo TCVN 13594 profile";
  clause map qua `version_registry.py` (3:2022 Hình 31 hoặc 4 §5.1 tùy bản).
- Đổi `postprocessor/checks_eurocode.py` → `postprocessor/checks.py` (dispatch
  theo `standards_profile`).
- `moving_load_strategy: time_history_function` default cho Midas Civil 2022,
  `rail_track_analysis` experimental (cần verify cú pháp/ý nghĩa).
- UI wireframe: "Damping [EN 1991-2]" → "Damping [standards_profile]" (label
  động).
- Catalog file names trung lập: `hslm_catalog.xlsx`, `static_train_loads.xlsx`,
  `real_trains.xlsx` (bỏ prefix `eurocode_` hoặc `tcvn_`).
- Acceptance v0.2-v0.3 mềm hơn: với HSR-CG/HS2/KD-Railway → kiểm tra **xu
  hướng + critical speed approximate + report layout + postprocess logic**
  thay vì ±3%/±5% cứng (vì chưa có file model gốc).
- Report PDF nhất quán **13 mục** (đã sửa từ "11 mục" còn sót).

---

## 2026-05-29 — Plan rev6: Vietnam standards flat structure

**Quyết định**:
- Đổi `standards/vn/tcvn_13594/part_X/` → `standards/vietnam/tcvn13594/` flat.
- Files theo capability: `dynamic_required.py`, `train_loads.py`,
  `hslm_rules.py`, `speed_range.py`, `damping.py`, `acceleration.py`,
  `resonance.py`, `load_actions.py`, `load_distribution.py`, `combinations.py`,
  `version_registry.py`.
- Thêm vào `project.yaml`:
  - `standards_profile: vietnam_tcvn13594`
  - `tcvn13594_versions` block (đọc năm xuất bản theo project)
  - `design` block (design_speed_kmh, max_analysis_speed_factor, track_type)
  - `dynamic` block (check_required_method, damping_method, resonance_check,
    time_step_method)
- Benchmark V09 — HSR-CG typical span với giá trị cụ thể từ bản tính PDF:
  - Solver: MIDAS Civil 2025, HSLM-A, ξ=1%, dt=0.001s
  - Vtk=350 km/h, Vmax=420 km/h
  - **f_bending ≈ 5.9312 Hz**, **f_torsion ≈ 16.35 Hz**, **Vcr ≈ 384.34 km/h**
  - Tolerance: soft (vì chưa có file model MIDAS gốc).
- Report PDF thêm mục: Vcr theo k=1..4, f_bending/f_torsion highlight, bảng
  Vmin/Vtk/Vmax, phản ứng tại Vtk + Vmax, biểu đồ xu hướng gia tốc theo vận
  tốc, kiểm tra điều kiện cần phân tích động.
- KHÔNG hard-code năm TCVN trong source code.

---

## 2026-05-29 — Plan rev5: TCVN làm tiêu chuẩn chính

**Quyết định**:
- Đọc bản tính HSR HCM-CG (575 trang) → liệt kê bộ TCVN 13594:2022-2023:
  - TCVN 13594-3:2022 (Tải trọng) — cốt lõi
  - TCVN 13594-4 (Phân tích) — cốt lõi
  - + TCVN 13594-5/6/7/8/9/10 + TCVN 2737/5574/9386/10304
- Tiêu chuẩn **chính = TCVN 13594**, Eurocode = tham chiếu kỹ thuật.
- Tải trọng đoàn tàu mở rộng: LM71 + SW/0 + SW/2 + HSLM-A1..A10 + HSLM-B +
  Tàu rỗng + Đoàn tàu thực + custom.
- Tải trọng phụ: kéo/hãm (QLAK, QLBK), ly tâm, lắc ngang, khí động học.
- Tổ hợp tải trọng theo Bảng A.1 TCVN 13594-3 (ψ0/ψ1/ψ2) + ULS + SLS +
  Accidental.
- Damping theo Bảng 18 TCVN 13594-3 (≡ EN 1991-2 6.4.6.3 Table 6.6).
- Acceleration limit 3.5/5.0 m/s² theo TCVN 13594-4 (≡ EN 1990 A2.4.4.2).

---

## 2026-05-29 — Plan rev4: 3 nguyên tắc MVP first-class

**Quyết định**:
- Đưa 3 nguyên tắc MVP lên đầu plan như ràng buộc cứng:
  1. MVP = 5 module nền cho Midas (MCT gen + Excel import + reader +
     postprocess + report).
  2. RM Bridge: skeleton + schema-ready, Phase 2.
  3. KHÔNG tự viết solver. Midas/RM là engine.
- Bất kỳ tính năng nào vi phạm 3 nguyên tắc → out of scope.

---

## 2026-05-29 — Plan rev3: Pre+Post processor cho Midas/RM Bridge

**Quyết định** (qua AskUserQuestion):
- Vai trò cốt lõi = **Pre + Post processor cho Midas Civil + RM Bridge**, không
  có solver nội bộ.
- Solver target = **Cả Midas Civil + RM Bridge** (Rolling Stock module).
- Result IO = User export CSV/Excel từ Midas/RM → app đọc.
- Input format = Excel/CSV.
- Project workspace = folder-based.
- Storage = **Parquet + SQLite combo** (TH → Parquet, envelope/meta →
  SQLite).
- UI = Desktop PySide6 + CLI Typer.
- Ngôn ngữ = tiếng Việt.
- Catalog HSLM/real trains mặc định **EMPTY**; user import Excel (tránh bản
  quyền EN).
- Architecture: tách `core/` (trung lập) + `standards/` (tiêu chuẩn có
  version) + `integrations/` (Midas/RM coupling) + `services/orchestration` +
  `ui/cli interface`.
- Data model bổ sung: ElementRelease, ElasticLink, RigidLink, NodalMass,
  ElementDistributedMass, StructureGroup, BoundaryGroup, LoadGroup,
  CoordinateSystem, ResultStation, UnitSystem.
- Capability-based MCT blocks naming (geometry/properties/boundary/...) thay
  vì MCT-keyword-based.

---

## 2026-05-29 — Plan rev1-rev2: Khám phá phương án

**Đã làm**:
- Đọc `docs/[Final]Dynamic Analysis for High Speed Two (HS2).pdf` (40 trang
  MIDAS UK Tutorial). Tóm tắt:
  - Eurocode flowchart NA.12 (BS EN 1991-2)
  - Eigenvalue + modal superposition
  - ERRI D214 time-step formula: `dt = min(1/(8fmax), Lmin/(200v),
    Lmin/(4nv), 0.001s)`
  - Damping EN 1991-2 6.4.6.3 Table 6.6
  - HSLM-A (A1..A10) + HSLM-B + 12 real trains
  - Load distribution 3 rail pads (EN 1991-2 6.3.6.3)
  - Acceleration limit 3.5/5.0 m/s²
- Xem 8 snapshot KD-Railway → hiểu UX panels (Structural Properties, Load
  HSLM, Options, Calculation toolbar).
- Web search: KD-Railway (UTT Vietnam, Cast3M backend, C#/.NET WinForms),
  CALDINTAV, OpenSeesPy.

**Phương án ban đầu** (đã được thay thế bởi rev3+): solver nội bộ OpenSeesPy
+ MCT export. → Sau khi user feedback "thống nhất Midas/RM làm engine" →
chuyển sang Pre+Post processor architecture.

---

## Quy ước viết log entry

```markdown
## YYYY-MM-DD — Tiêu đề ngắn

**Quyết định** (nếu có):
- Bullet list

**Đã làm**:
- Bullet list

**Lý do** (nếu non-obvious):
- ...

**Blockers mới phát sinh** (nếu có):
- B# - mô tả
```
