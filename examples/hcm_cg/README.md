# HSR Hồ Chí Minh - Cần Giờ — Nhịp điển hình

Project mẫu reproduce **benchmark V09** từ bản tính HSR HCM-CG.

## Tham số (theo `refer/202512-23_HSR-CG Ban Tinh Tong The H7H15m.pdf`)

| Thông số | Giá trị |
|---|---|
| Số nhịp | 5 (Main Girder + Sub Girder cho dynamic investigation) |
| Vận tốc thiết kế V_tk | 350 km/h |
| Vận tốc phân tích max | 420 km/h (1.2 × V_tk) |
| Loại đường ray | ballastless (HSR) |
| Đoàn tàu chính | HSLM-A |
| Damping ξ | 1% (input bản tính); auto theo Bảng 18 TCVN 13594-3 nếu để default |
| Time step dt | 0.001 s (theo ERRI D214) |
| **f_bending kỳ vọng** | ≈ 5.9312 Hz |
| **f_torsion kỳ vọng** | ≈ 16.35 Hz |
| **V_cr kỳ vọng** | ≈ 384.34 km/h |

## Trạng thái v0.1

`bridge.xlsx` hiện chứa **template với sample minimal** (1 nhịp giản đơn). Khi
có file MCT mẫu Midas Civil 2022 (B1 trong PROJECT_STATUS), sẽ reverse-engineer
và import dữ liệu 5 nhịp Main+Sub girder đầy đủ vào bridge.xlsx.

## Verify

```powershell
vbdyn init examples\hcm_cg --name "HSR HCM-CG" --design-speed 350 --track-type ballastless --force
vbdyn validate examples\hcm_cg
```

Acceptance V09 (xem CLAUDE.md §7.2 — soft): f_bending cùng order (~6 Hz),
f_torsion cùng order (~16 Hz), V_cr ±20 km/h, report layout đủ 13 mục.
