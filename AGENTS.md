# Agents & Contributors — Read Before Working

> Bất kỳ AI agent (Claude, Codex, Cursor, …) hoặc dev nào làm việc trên repo này
> **bắt buộc đọc 3 file sau theo thứ tự** trước khi sửa code:
>
> 1. [`CLAUDE.md`](./CLAUDE.md) — kiến trúc, 3 nguyên tắc MVP, stack, conventions
> 2. [`PROJECT_STATUS.md`](./PROJECT_STATUS.md) — version hiện tại, active focus, blockers
> 3. [`TASK_LOG.md`](./TASK_LOG.md) — lịch sử quyết định (append-only)

Kế hoạch chi tiết đầy đủ: [`docs/PLAN_REV9.md`](./docs/PLAN_REV9.md) (bản nội bộ
trong repo, không phụ thuộc thư mục `.claude/` ngoài).

---

## Quy tắc làm việc

1. **Không vi phạm 3 nguyên tắc MVP** (xem `CLAUDE.md` §1):
   - MVP = 5 module nền cho Midas (gen + import + read + postprocess + report)
   - RM Bridge ở MVP = skeleton + schema-ready
   - KHÔNG tự viết solver; Midas Civil 2022 + RM Bridge là engine

2. **Khi quyết định kiến trúc thay đổi**: cập nhật cả `CLAUDE.md` (mục liên
   quan) và append entry mới vào `TASK_LOG.md` trong **cùng commit**.

3. **Khi đóng/mở task lớn, đổi version, hoặc gặp blocker**: cập nhật
   `PROJECT_STATUS.md`.

4. **Ngôn ngữ**:
   - Text user-facing (UI, comment trong code, error message, PDF report): **tiếng Việt**
   - Tên biến/class/function/identifier: **tiếng Anh**

5. **Tiêu chuẩn**:
   - Mặc định `standards_profile: vietnam_tcvn13594`
   - Eurocode là cross-check, không phải primary
   - KHÔNG hard-code năm xuất bản TCVN — đọc từ `project.yaml > tcvn13594_versions`

6. **Test trước khi commit** (chi tiết trong `CLAUDE.md` §7):
   - **Hard benchmarks** V01-V02 (analytical) + V06-V07 (TCVN/EN parity) chạy mỗi PR (<5 min)
   - **Reference comparisons** V03-V05, V09 weekly/on-demand (cần Midas hoặc reference data)
   - V08 (RM Bridge parity) chỉ chạy khi tới Phase 2; V10 (VBI) khi tới Phase 3

---

## Khi chuyển giao (handoff)

Nếu chuyển dự án cho người/AI khác:

1. Cập nhật `PROJECT_STATUS.md` với hiện trạng đầy đủ (version, active focus, blockers).
2. Append vào `TASK_LOG.md` đoạn `## Handoff <yyyy-mm-dd>` liệt kê:
   - Todo còn lại
   - Blockers đã biết
   - Files đã sửa gần đây
   - Quyết định kiến trúc mới (nếu có) — cũng update `CLAUDE.md`
3. Commit message: `handoff: <ngày> — <summary 1 dòng>`.

---

## Liên hệ

- Owner: Vũ (quangvu0515@gmail.com)
