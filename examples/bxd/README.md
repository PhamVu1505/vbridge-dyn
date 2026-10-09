# HSR BXD

## Tham số (theo `D:\2026\09_Dynamic_analysis_for_high_speed_railway_bridges\projects\de tai BXD`)

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

## Trạng thái hiện tại

`bridge.xlsx` đã có dữ liệu model BXD để sinh **base/modal MCT**: nodes,
elements, materials, sections, supports, elastic links, rigid links, groups,
tracks và dead load phân bố.

Trước khi chạy, cần bảo đảm các file mặt cắt trong sheet `Sections` tồn tại
trong thư mục `dxf/`. Hiện project cần file:

```text
dxf/MG_01.dxf
```

Nếu chỉ muốn test pipeline bằng mặt cắt mẫu có sẵn trong repo, có thể copy từ
project `hcm_cg`:

```powershell
Copy-Item ".\examples\hcm_cg\dxf\MG_01.dxf" ".\examples\bxd\dxf\MG_01.dxf"
```

## Cách chạy sinh MCT

Chạy từ thư mục root của repo:

```powershell
cd "D:\2026\09_Dynamic_analysis_for_high_speed_railway_bridges\vbridge-dyn"

.\.venv\Scripts\vbdyn.exe validate .\examples\bxd
.\.venv\Scripts\vbdyn.exe generate .\examples\bxd --target midas
```

Kết quả sinh ra:

```text
examples\bxd\generated\midas\model_base.mct
examples\bxd\generated\midas\generation_manifest.json
```

Ghi chú: `validate` có thể báo `Trains FAIL` vì `project.yaml` hiện để
`trains: []`. Điều này chưa chặn bước sinh `model_base.mct`; nó chỉ cho biết
chưa có dữ liệu đoàn tàu để sinh dynamic/time-history HSLM.

## Verify

Acceptance V09 (xem CLAUDE.md §7.2 — soft): f_bending cùng order (~6 Hz),
f_torsion cùng order (~16 Hz), V_cr ±20 km/h, report layout đủ 13 mục.
