# Dynamic Handoff - BXD 32.6 m

Cap nhat: 2026-06-24.

## Muc tieu tiep theo

Kiem tra nguyen nhan lech ket qua dong luc muc 5.7 so voi bao cao:

- Bao cao: `n0 = 5,066 Hz`, `amax = 2,30 m/s2`, `delta_dynamic = 2,97 mm`.
- Export cu truoc khi them G2 mass: `n0 = 5,89363 Hz`, `amax = 1,162995 m/s2`, `delta = 1,405 mm`.

Nhan dinh hien tai: can chay lai MIDAS sau khi them G2 vao mass truoc khi sweep toc do/case HSLM.

## Ket qua chay moi da kiem tra

Da doc hai bo ket qua moi:

- `model_dynamic_countercheck_32_6_HSLM-A1_330`
- `model_dynamic_countercheck_32_6_HSLM-A1_330_no_cable`

OUT nam o thu muc `examples/bxd/generated/midas`; Excel export nam trong tung thu muc ket qua.
Ca hai bai chay khong thay warning/error chinh, deu dung modal transient, lumped mass,
modal damping, 895 valid DOF, 6703 buoc, `dt = 0.001 s`.

Ket qua chinh:

| Mo hinh | n0 mode 1 | DZ abs max node 100016 | Acc DZ abs max node 100016 |
| --- | ---: | ---: | ---: |
| Co cap + G2 mass | 4.790193 Hz | 1.759 mm | 1.14845 m/s2 |
| No-cable + G2 mass | 4.717181 Hz | 1.622 mm | 0.994675 m/s2 |

Ket luan ngan:

- G2 mass da lam tan so giam tu export cu `5.89363 Hz` xuong `4.790193 Hz`; nguyen nhan
  lech truoc do chu yeu la thieu khoi luong tinh tai phan 2.
- Bo cap chi lam tan so giam them khoang 1.55%, nen cap/prestress khong phai nguyen nhan
  chinh cua lech lon.
- Mo hinh co G2 mass dang thap tan so hon bao cao `5.066 Hz` khoang 5.45%; tai 330 km/h
  co the da qua dinh cong huong cua model moi. Toc do cong huong A1 uoc tinh hien tai
  khoang `310.4 km/h`, trong khi bao cao ung voi khoang `328.3 km/h`.

Chi tiet da luu tai:

- `dynamic_result_review_2026_06_24.md`

Da sinh them MCT sweep co cap + G2 mass:

- `model_dynamic_countercheck_32_6_HSLM-A1_290.mct`
- `model_dynamic_countercheck_32_6_HSLM-A1_300.mct`
- `model_dynamic_countercheck_32_6_HSLM-A1_305.mct`
- `model_dynamic_countercheck_32_6_HSLM-A1_310.mct`
- `model_dynamic_countercheck_32_6_HSLM-A1_315.mct`
- `model_dynamic_countercheck_32_6_HSLM-A1_320.mct`
- `model_dynamic_countercheck_32_6_HSLM-A1_325.mct`
- `model_dynamic_countercheck_32_6_HSLM-A1_330.mct`
- `model_dynamic_countercheck_32_6_HSLM-A1_335.mct`
- `model_dynamic_countercheck_32_6_HSLM-A1_340.mct`

Rasoat them:

- `Eigenvalue Mode.xls` hien da co modal participation mass/factor/direction factor; can
  trich cumulative UZ cho cum mode 1-5, khong chi mode 1.
- Line mass bao cao: `(214.1 + 106.75) / 9.806 = 32.720 t/m`, gan voi `32.705 t/m`.
- Line mass tu MCT section + G2 khoang `33.10-33.36 t/m`, cao hon bao cao 1-2%, khong
  du giai thich toan bo chenhlech tan so.
- HSLM-A1 pattern trong MCT: 18 coaches, 2 axles/coach, `D = 18 m`, `d = 2 m`, `P = 170 kN`,
  `v = kmh/3.6`, nodal load `Z` scale `-1`.

## MCT can chay

1. `model_dynamic_countercheck_32_6_HSLM-A1_330.mct`
   - Co tendon/prestress.
   - Self-weight convert mass bang `*STRUCTYPE`.
   - `G2_REPORT = 106,75 kN/m` convert mass bang `*LOADTOMASS`.

2. `model_dynamic_countercheck_32_6_HSLM-A1_330_no_cable.mct`
   - Tat prestress/tendon de kiem tra anh huong khai bao cap.
   - Khong co `*TDN-PROPERTY`, `*TDN-PROFILE`, `*TDN-PRESTRESS`.
   - Van co self-weight mass va `G2_REPORT` mass.

## Export can lay tu MIDAS

Cho moi MCT:

- `.OUT` de kiem tra warning/error va tan so trong eigen output.
- `Eigenvalue Mode.xls`.
- `Displacement_dynamic.xls`.
- `Absolute Accel._dynamic.xls`.
- Neu can doi chieu: `Relative Accel._dynamic.xls`, `Velocity_dynamic.xls`.

Neu file export ghi de cung ten, luu rieng ban no-cable voi hau to ro rang hoac doi ten truoc khi rebuild bang so sanh.

## Cach danh gia

1. So tan so mode 1 cua ban co cap sau khi them G2 mass voi `5,066 Hz`.
2. So tan so mode 1 cua ban no-cable voi ban co cap:
   - Neu gan nhu khong doi: tendon/prestress khong lam tang do cung dong trong MCT hien tai.
   - Neu giam dang ke: tiep tuc soi cach MIDAS ke stiffness/tendon trong modal.
3. Truoc khi sweep day du HSLM A1-A10, can sweep nhanh A1 quanh `290-340 km/h` de
   bat dinh cong huong moi sau khi them G2 mass.
4. Xuat/kiem tra modal mass participation vi mo hinh hien co 5 nhip doc lap, cac mode
   dau gan trung tan so va co the chia participation giua cac mode.
5. Rasoat khoi luong tren met dai voi muc bao cao `32.705 t/m`, sau do moi ket luan
   can hieu chinh do cung section/stage hay load HSLM.

## File da sua

- `src/vbridge_dyn/integrations/midas/mct/dynamic_countercheck.py`
- `tests/unit/test_static_countercheck.py`
- `examples/bxd/generated/midas/README.md`
- `examples/bxd/generated/midas/SESSION_STATUS.md`

## Lenh tai tao

```powershell
cd D:\2026\09_Dynamic_analysis_for_high_speed_railway_bridges\vbridge-dyn
.\.venv\Scripts\python.exe -m vbridge_dyn.integrations.midas.mct.dynamic_countercheck
.\.venv\Scripts\python.exe -m pytest tests\unit\test_static_countercheck.py -q
```
