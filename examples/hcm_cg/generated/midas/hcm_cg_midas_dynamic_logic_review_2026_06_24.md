# HCM-CG MIDAS dynamic logic review

Cap nhat: 2026-06-24.

Muc tieu: kiem tra lai logic khai bao trong
`examples/hcm_cg/generated/midas`, dac biet viec 5 nhip, time force functions va
quan he voi generator hien tai cua repo.

## File da kiem tra

| File | Nhan xet |
| --- | --- |
| `model_base.mct` | Output chinh tu CLI/generator hien tai. Co geometry 5 nhip, nhung khong co `*TFUNCTION`, `*THLDCASE`, `*DYN-NLOAD`. |
| `model_base_review.mct` | File review/reference co them raw dynamic case HSLM-A1 @ 250 km/h. Co 5 nhip va 85 dynamic nodal loads. |
| `Untitled.mct` | MCT cu/manual co 5 nhip, nhung khong co dynamic time-history block. |
| `generation_manifest.json` | Chi khai bao `case_modal_base`; ghi chu dynamic train-load blocks se sinh sau khi xac nhan HSLM catalog va load path. |
| `model_base_V1.OUT`, `Untitled.OUT` | Da chay modal + time history, 85 dynamic inputs, 3000 time steps; khong thay warning/error chinh. |

## Geometry va 5 nhip

Ca `model_base.mct`, `model_base_review.mct` va `Untitled.mct` deu co 5 nhom dam chinh:

- `Girder1`: elements `101..116`.
- `Girder2`: elements `201..216`.
- `Girder3`: elements `301..316`.
- `Girder4`: elements `401..416`.
- `Girder5`: elements `501..516`.
- `Main Girder`: gom ca 5 nhom tren.

Ket qua parse:

| File | Nodes | Elements | X range | Dynamic load |
| --- | ---: | ---: | ---: | --- |
| `model_base.mct` | 341 | 254 | -2.25..165.75 m | none |
| `model_base_review.mct` | 341 | 254 | -2.25..165.75 m | 85 nodal loads |
| `Untitled.mct` | 301 | 254 | -2.25..165.75 m | none |

Nhan xet: output base hien tai khong chi co 1 nhip; geometry co 5 nhip. Dieu dang
thieu trong output chinh la dynamic train-load block.

## Dynamic block trong `model_base_review.mct`

`model_base_review.mct` co:

- `*TFUNCTION`: line 1693.
- `FUNC=HSLM-A1_250km/h_f001`: line 1697.
- `FUNC=HSLM-A1_250km/h_f085`: line 8081.
- `*THLDCASE`: line 8158.
- `NAME=HSLM-A1`: line 8172.
- `*DYN-NLOAD`: line 8176.
- `*TH-GRAPH`: line 8264.
- `*EIGEN-CTRL`: line 8296.

Thong so time-history:

- Case: `HSLM-A1`.
- Speed encoded in function names: `250 km/h`.
- Duration in `*THLDCASE`: `30 s`.
- Time increment: `0.01 s`.
- Modal damping: `0.01`.
- OUT: `NUMBER OF DYNAMIC INPUTS = 85`, `NUMBER OF TIME STEPS = 3000`.
- TH graph chi xuat `deck acc` tai node `308`, tuc mid/near-mid cua nhip 3, khong xuat tat ca nhip.

## Load path 5 nhip trong dynamic block

`*DYN-NLOAD` co 85 dong = 5 nhip x 17 node/nhip:

| Span | Loaded nodes | X range | Function range | ARTIME range |
| --- | --- | ---: | --- | ---: |
| 1 | `101..117` | 0.05..32.65 m | `f001..f017` | 0..0.46152 s |
| 2 | `201..217` | 32.75..65.35 m | `f018..f034` | 0.46944..0.93240 s |
| 3 | `301..317` | 65.45..98.05 m | `f035..f051` | 0.94032..1.40328 s |
| 4 | `401..417` | 98.15..130.75 m | `f052..f068` | 1.41120..1.87416 s |
| 5 | `501..517` | 130.85..163.45 m | `f069..f085` | 1.88208..2.34504 s |

Nhan xet: dynamic block cua review dang xet ca chuoi 5 nhip, khong phai chi nhip 1.
Do cac dong `*DYN-NLOAD` bi sap xep khong theo thu tu node, nhin bang mat rat de tuong
la thieu nhip.

## HSLM-A1 pattern trong review

Tu `FUNC=HSLM-A1_250km/h_f001`, co the recover duoc 50 peak tai trong truc. Cac vi tri
peak dau tien theo met, voi `v = 250/3.6 m/s`:

```text
0.0, 3.0, 14.0, 17.0, 20.525, 22.525,
35.7625, 37.7625, 53.7625, 55.7625, ...
```

Khoang cach lap lai chinh:

```text
3, 11, 3, 3.525, 2, 13.2375, 2, 16, 2, 16, ...
```

Nhan xet: review HCM-CG dang encode mot HSLM-A1 day du hon, 50 peak/truc. No khac voi
logic BXD countercheck hien tai, noi dang dung pattern rut gon:

```text
coach_count = 18
2 axles/coach tai i*D va i*D+d
D = 18 m
d = 2 m
P = 170 kN
```

Pattern BXD rut gon cho 36 truc, khong tuong duong voi raw HCM-CG review 50 peak.

## Logic time function: HCM review vs BXD

### HCM review

Chien luoc trong `model_base_review.mct` la:

1. Tao 1 time function cho moi loaded node tren chuoi 5 nhip: `f001..f085`.
2. Moi function chua dang bien thien cuc bo cua tai truc qua node do, bao gom shape
   function tuyen tinh qua hai element lan can.
3. Dung `ARTIME` trong `*DYN-NLOAD` de dich function den vi tri tuyet doi tren chuoi nhip.

Kiem tra timing:

- Lay `ARTIME + first_peak_time` cua moi function.
- So voi `(x_node - x_start) / v`, voi `x_start = 0.05 m`, `v = 250/3.6 m/s`.
- Sai khac deu khoang `0.00072 s`, chinh la offset do lay moc x bat dau. Nhu vay khong
  thay loi double-shift; ARTIME va function dang phoi hop dung theo moc chuoi nhip.

### BXD countercheck hien tai

Logic trong `src/vbridge_dyn/integrations/midas/mct/dynamic_countercheck.py`:

- Config default `span_index = 1`.
- Goi `_load_path_nodes(top_bridge, span_index)`.
- Chi lay node cua `Girder1` de sinh `*TFUNCTION` va `*DYN-NLOAD`.
- `ARTIME = 0` cho tat ca dynamic nodal loads.
- Moi function da chua truc tiep thoi gian theo toa do local cua nhop do.

Nhan xet: day la logic hop voi countercheck 1 nhip BXD, nhung khong hop neu muon mo
phong chuoi 5 nhip HCM-CG nhu `model_base_review.mct`.

## Quan he voi generator hien tai cua repo

Repo hien tai chua dung train-load generator tong quat de sinh dynamic MCT HCM-CG.

Bang chung:

- `examples/hcm_cg/project.yaml` dang `trains: []`.
- `generation_manifest.json` chi co `case_modal_base`.
- `generation_manifest.json` notes: dynamic train-load blocks se sinh sau khi HSLM catalog
  va Sub Girder/load-path duoc xac nhan.
- `TASK_LOG.md` ghi raw dynamic case HSLM-A1 250 km/h co `*TFUNCTION` 6460 dong,
  `*THLDCASE` 3 dong, `*DYN-NLOAD` 85 dong, nhung chua dua vao generator vi thieu
  train catalog/schema de sinh lai co kiem soat.
- `src/vbridge_dyn/core/schemas/train.py` co `TrainModel`/`Axle`, nhung catalog khong ship
  san va HCM-CG chua import train.

Nhan xet: `model_base_review.mct` la reference/manual raw dynamic block, khong phai output
chinh thuc cua generator hien tai.

## Ket luan

1. HCM-CG base geometry hien tai co 5 nhip trong `model_base.mct`; khong phai chi 1 nhip.
2. Dynamic block 5 nhip chi co trong `model_base_review.mct`, khong co trong output generator
   `model_base.mct`.
3. Dynamic block review dung 85 load nodes tren 5 nhip va HSLM-A1 50 peak, khac dang ke
   voi logic BXD dang dung 29/30 nodes mot nhip va HSLM-A1 rut gon 36 truc.
4. BXD `dynamic_countercheck.py` hien tai co `span_index=1`, nen neu dem ap dung cho
   HCM-CG se chi sinh tai dong cho nhip 1.
5. Can lay `model_base_review.mct` lam fixture/reference de xay dung generator HCM-CG
   dung chuoi 5 nhip, thay vi copy logic BXD mot nhip.

## Huong trien khai tiep

1. Tach raw dynamic block HCM-CG trong `model_base_review.mct` thanh fixture test:
   - count `*TFUNCTION = 85`.
   - count `*DYN-NLOAD = 85`.
   - speed `250 km/h`.
   - node path `101..117`, `201..217`, ..., `501..517`.

2. Them train catalog HSLM-A1 day du vao schema/import:
   - Khong dung pattern BXD 36 truc cho HCM-CG.
   - Can xac nhan chinh thuc bang TCVN/EN hoac lay tu raw review neu dung lam source.

3. Viet load-path builder cho multi-span:
   - Chon `Main Girder` hoac list `Girder1..Girder5`.
   - Sap node theo toa do X tren chuoi lien tuc.
   - Giu ca endpoint nodes neu can khop review: 17 node/nhip.

4. Chon mot trong hai chien luoc time function:
   - Chien luoc HCM review: local function + `ARTIME` theo `x_abs/v`.
   - Chien luoc BXD: absolute-time function + `ARTIME = 0`.

   Nen uu tien chien luoc HCM review neu muc tieu la reproduce `model_base_review.mct`.

5. Sau khi sinh lai, so sanh tu dong voi reference:
   - so node load, function count, ARTIME, first peak timing;
   - OUT phai co `NUMBER OF DYNAMIC INPUTS = 85`, `NUMBER OF TIME STEPS = 3000`;
   - khong co warning/error chinh.
