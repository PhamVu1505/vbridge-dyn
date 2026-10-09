# BXD 32.6 m MIDAS Countercheck

Thu muc nay chua cac file MIDAS export va report so sanh tu dong cho dam 32,6 m.

## File MIDAS can export dung ten

Dat cac file sau trong thu muc nay:

- `Beam Force.xls`
- `Reaction(Global).xls`
- `Displacements(Global).xls`
- `Displacements(Global)_construction.xls`
- `Beam Stress.xls`
- `Beam Stress_construction.xls`
- `Eigenvalue Mode.xls`
- `Displacement_dynamic.xls`
- `Absolute Accel._dynamic.xls`
- `Relative Accel._dynamic.xls`
- `Velocity_dynamic.xls`

Sau khi them combo `SLS_TRANSPORT_P` va `FATIGUE_LM71_EN`, can chay lai MIDAS tu file MCT moi va export lai `Beam Stress.xls`/`Beam Force.xls` de co ket qua ung suat thi cong SLS va moi EN.

## Tao lai MCT

Tu thu muc repo:

```powershell
cd D:\2026\09_Dynamic_analysis_for_high_speed_railway_bridges\vbridge-dyn
.\.venv\Scripts\python.exe -m vbridge_dyn.integrations.midas.mct.static_countercheck
```

File MCT duoc tao tai:

```text
examples\bxd\generated\midas\model_static_countercheck_32_6.mct
```

## Tao model dong muc 5.7

Model dong dau tien bam dung dong khong che trong bao cao cho dam 32,6 m:
HSLM-A1 tai 330 km/h, damping 1,5%, xuat TH-Graph o node giua nhip.
Model dong da khai bao khoi luong theo dung gia thiet bao cao: self-weight duoc
convert tu Structure Type, con `G2_REPORT = 106,75 kN/m` duoc them vao
`*LOADTOMASS`.

```powershell
cd D:\2026\09_Dynamic_analysis_for_high_speed_railway_bridges\vbridge-dyn
.\.venv\Scripts\python.exe -m vbridge_dyn.integrations.midas.mct.dynamic_countercheck
```

File MCT duoc tao tai:

```text
examples\bxd\generated\midas\model_dynamic_countercheck_32_6_HSLM-A1_330.mct
examples\bxd\generated\midas\model_dynamic_countercheck_32_6_HSLM-A1_330_no_cable.mct
```

Hai bien the can chay de tach nguyen nhan tan so:

- `model_dynamic_countercheck_32_6_HSLM-A1_330.mct`: co tendon/prestress.
- `model_dynamic_countercheck_32_6_HSLM-A1_330_no_cable.mct`: tat prestress/tendon, van giu self-weight va `G2_REPORT` trong mass.

Sau khi import/chay trong MIDAS, export:

- Modal/eigen frequency mode uon dau de so `n0 = 5,066 Hz`.
- Time-history graph `deck acc 32.6` de so `amax = 2,30 m/s2`.
- Time-history graph `deck dz 32.6` de so `delta_max dong = 2,97 mm`.
- Voi bien the no-cable, export bang modal/eigen rieng de doi chieu tan so voi ban co cap.

Export moi nhat da duoc doc vao bang so sanh:

- `Eigenvalue Mode.xls`: mode 1 = 5,89363 Hz.
- `Absolute Accel._dynamic.xls`: node 100016, DZ = 1,162995 m/s2.
- `Displacement_dynamic.xls`: node 100016, abs DZ = 1,405 mm.

Luu y: cac export tren la truoc khi them `G2_REPORT` vao `*LOADTOMASS`.
Sau khi sinh lai MCT dong, can chay lai MIDAS va export lai `.OUT/.xls` de cap
nhat tan so/gia toc/vong dong.

## Chay MIDAS va export

1. Import/chay `model_static_countercheck_32_6.mct` trong MIDAS.
2. Export cac bang force/reaction/displacement/stress dung ten file o tren.
3. Voi construction stage, export theo `Load=Summation` cho cac stage:
   - `CS1_Prestress_3d`
   - `CS2_G2_36d`
   - `CS3_LongTerm_100y`
4. Voi ung suat thi cong, export `Beam Stress.xls` co load combination `SLS_TRANSPORT_P`.
5. Voi moi, export `Beam Force.xls` va `Beam Stress.xls` co load combination/case:
   - `FATIGUE_LM71_EN(max)`
   - `FATIGUE_LM71_EN(min)`
   - `FATIGUE_LM71_EN(all)`
   Neu MIDAS chi cho export moving load case rieng, export them `LM71_FAT_2T_PHI`; script se uu tien combo `FATIGUE_LM71_EN`.

## Tao lai workbook va Word report

```powershell
cd D:\2026\09_Dynamic_analysis_for_high_speed_railway_bridges\vbridge-dyn
.\.venv\Scripts\python.exe .\examples\bxd\generated\midas\rebuild_comparison_bxd_32_6.py
.\.venv\Scripts\python.exe .\examples\bxd\generated\midas\build_bxd_32_6_word_report.py
.\.venv\Scripts\python.exe .\examples\bxd\generated\midas\build_bxd_32_6_calculation_report.py
```

Output chinh:

- `comparison_bxd_32_6.xlsx`
- `comparison_bxd_32_6.md`
- `comparison_checklist_bxd_32_6.md`
- `so_sanh_midas_bao_cao_bxd_32_6_moc_3d_36d_100y.docx`
- `bao_cao_tinh_toan_midas_bxd_32_6.docx`
- `bao_cao_tinh_toan_midas_bxd_32_6_phu_luc.xlsx`
- `tendon_layout_bxd_32_6.png`

## Bao cao tinh toan MIDAS

`build_bxd_32_6_calculation_report.py` tao mot bao cao tinh toan doc lap theo bo cuc tham khao RM bridge report:

- Trang bia, muc luc noi dung va nguon du lieu.
- Chuong 1 `Mo hinh tinh`: node, element, support, vat lieu, mat cat, cap DUL, tai trong, stage, to hop.
- Chuong 2 `Ket qua tinh toan`: noi luc/phan luc, ung suat, do vong/do vong/goc xoay, moi va checklist.
- Chuong 3 `Phu luc ket qua`: danh sach cac sheet du lieu day du trong Excel phu luc.

Bao cao gom cac noi dung chinh:

- Thong tin node va element.
- Lien ket/support, gom node goi, constraint Dx/Dy/Dz/Rx/Ry/Rz, dien giai `111100`/`011100`, group `Support` va stage kich hoat `ABNDR=Support, ORIGINAL`.
- Dac trung hinh hoc mat cat, vat lieu va vat lieu theo thoi gian.
- Tai trong, moving load, xe LM71/LM71 fatigue, tai van chuyen, gio.
- So do bo tri cap DUL va hinh minh hoa profile cap G1.
- Stage thi cong, to hop tai trong.
- Tong hop ket qua va phu luc bang du lieu day du.

## Luu y doc ket qua

- G1 trong report goi la `trong luong ban than`.
- Ung suat MIDAS trong `Beam Stress*.xls` co don vi `kN/m2`; script doi sang `MPa`.
- Quy uoc tho muc 5.1 theo bao cao:
  - `top` = tho tren dam = `Cb1/Cb2`.
  - `bot` = tho duoi dam = `Cb3/Cb4`.
  - `Cang keo`: so `sigma_bot,min`.
  - `Khai thac`: so `sigma_bot,max`, lay `SLS_CHAR_LM71(max)` tai node giua nhip `x00016`; khong dung `SLS_CHAR_LM71(all/min)`.
  - `Thi cong`: so `sigma_bot,max`, lay tai node giua nhip `x00016` de tranh node dau dam co ung suat 0 lam sai max.
  - `Dai han`: so `sigma_top,min`.
- Muc 5.2 cua bao cao duoc so theo dung thoi diem:
  - Do vong LM71: `Displacements(Global).xls`, load `LM71_2T(min)`, lay `abs(DZ_min)`.
  - Do vong sau lap tinh tai GD2: `Displacements(Global)_construction.xls`, `Summation`, `CS2_G2_36d`, last step.
  - Do vong 100 nam: `Displacements(Global)_construction.xls`, `Summation`, `CS3_LongTerm_100y`, last step.
  - Goc xoay tai dau dam: lay tri tuyet doi envelope `RY` tai node dau dam `x00001/x00031`.
- Gio ngang da co ghi chu rieng va tam bo qua trong report so sanh hien tai.
- Moi EN trong MCT dung `Load Model 71 Fatigue` voi alpha=1.0, co he so dong Phi, va combo `FATIGUE_LM71_EN` nhan he so tuong duong hu hong `lambda=1.04`.
- Bang so sanh khong dung tam `LM71_2T` alpha=0.90 cho moi; neu da export `FATIGUE_LM71_EN`, script se cap nhat mo men moi va bien do ung suat be tong.
- Ung suat moi be tong lay bien do `FATIGUE_LM71_EN(max) - FATIGUE_LM71_EN(min)`, khong lay mot chieu max/min rieng le.
- `Tendon Stress Limit Check.xls` la bang kiem gioi han ung suat tendon sau neo/khai thac, khong phai bien do ung suat moi cap.
- Ung suat cap va cot dai moi can them cong thuc/design output rieng neu muon ket luan cuoi.
