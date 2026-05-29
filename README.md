# VBridge-Dyn

> Phần mềm tự động hóa phân tích động lực học cầu đường sắt tốc độ cao theo
> **TCVN 13594:2022-2023** (Eurocode làm tham chiếu kỹ thuật).

VBridge-Dyn sinh model + tổ hợp tải trọng đoàn tàu cho **Midas Civil 2022**, sau
khi user chạy phân tích trong Midas và export CSV, phần mềm tự động ingest, tính
envelope/time-history, và xuất **báo cáo PDF vector tiếng Việt** theo yêu cầu
TCVN 13594-4.

Lấy cảm hứng UX từ KD-Railway (UTT Vietnam) và tham khảo bản tính dự án thật
**HSR Hồ Chí Minh - Cần Giờ** (Main Girder + Sub Girder, 5 nhịp điển hình).

---

## Đối tượng người dùng

- Kỹ sư cầu Việt Nam thiết kế cầu đường sắt khổ 1435 mm, vận tốc đến 350 km/h.
- Có sẵn license **Midas Civil 2022**, quen workflow MCT.
- Cần tự động hóa pipeline: sinh nhiều load case → chạy Midas → tổng hợp kết
  quả → báo cáo theo TCVN.

---

## Vai trò (ranh giới quan trọng)

VBridge-Dyn **KHÔNG** là solver. Phân tích bằng **Midas Civil 2022** chạy thủ
công. Phần mềm chỉ:

1. **Sinh** `.mct` theo strategy đã chọn (mặc định `grouped_by_train`: **1 file
   cho mỗi đoàn tàu, chứa nhiều velocity cases** dưới dạng `*TIME-HISTORY-CASE`).
   Cộng thêm `generation_manifest.json` (bắt buộc — map case → CSV expected
   filename + train + velocity + result stations), `export_instructions.md`,
   `result_export_template.xlsx`.
2. **Hướng dẫn** user export CSV thủ công từ Midas qua `export_instructions.md`.
3. **Ingest** CSV → SQLite (envelope/meta) + Parquet (time-history).
4. **Postprocess** envelope + checks theo `standards_profile` (mặc định
   TCVN 13594, Eurocode làm cross-check).
5. **Xuất** PDF báo cáo 13 mục tiếng Việt.

---

## Quick start (sẽ implement v0.1+)

```powershell
# Cài đặt (Python 3.11+, uv)
uv tool install vbridge-dyn

# Khởi tạo project mới
vbdyn init my_bridge_project

# Sửa my_bridge_project/bridge.xlsx (template tự sinh)
# Sửa my_bridge_project/project.yaml: chọn trains, velocity range, standards_profile

vbdyn validate my_bridge_project
vbdyn generate --target midas my_bridge_project
# → generated/midas/*.mct + generation_manifest.json + export_instructions.md

# (Thủ công) Mở từng .mct trong Midas Civil 2022, Run, Export CSV theo hướng dẫn

vbdyn ingest --target midas my_bridge_project
vbdyn envelope my_bridge_project
vbdyn report --pdf reports/report.pdf my_bridge_project
```

Desktop UI:

```powershell
vbdyn  # mở PySide6 window
```

---

## Yêu cầu hệ thống

| Mục | Yêu cầu |
|---|---|
| OS | Windows 10/11 (64-bit) |
| Python (dev) | 3.11+ với `uv` |
| Midas Civil | **2022** (mặc định) — version khác cần override `column_mapping.yaml` |
| RAM | 8 GB đủ cho cầu 3-5 nhịp; 16 GB đề xuất |
| Disk | ~2 GB cho 500 cases với time-history Parquet nén gzip |

---

## Tiêu chuẩn áp dụng

**Việt Nam — chính**: TCVN 13594-1..10:2022-2023, TCVN 2737:2023, TCVN
5574:2022, TCVN 9386:2012, TCVN 10304:2015.

**Châu Âu — tham chiếu**: EN 1990:2002+A1:2005, EN 1991-2:2003, EN 1992-2, EN
1994-2, ERRI D214:1999.

---

## Tài liệu tiếp theo

- [`AGENTS.md`](./AGENTS.md) — quy tắc cho mọi agent/dev khi vào repo (đọc đầu tiên).
- [`CLAUDE.md`](./CLAUDE.md) — context kiến trúc + 3 nguyên tắc MVP + stack +
  conventions. **Đọc bắt buộc** trước khi đóng góp code.
- [`PROJECT_STATUS.md`](./PROJECT_STATUS.md) — snapshot hiện tại (version,
  milestone, blockers, checklist active).
- [`TASK_LOG.md`](./TASK_LOG.md) — lịch sử quyết định + task hoàn thành
  (append-only).
- [`docs/PLAN_REV9.md`](./docs/PLAN_REV9.md) — plan đầy đủ đã duyệt (bản
  trong repo, self-contained).

---

## License

Apache-2.0 (đề xuất).
