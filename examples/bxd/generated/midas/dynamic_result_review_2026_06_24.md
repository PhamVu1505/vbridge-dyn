# Dynamic result review - BXD 32.6 m

Cap nhat: 2026-06-24, sau hai lan chay MIDAS moi:

- `model_dynamic_countercheck_32_6_HSLM-A1_330`
- `model_dynamic_countercheck_32_6_HSLM-A1_330_no_cable`

## Nguon ket qua da doc

OUT nam o thu muc `examples/bxd/generated/midas`:

- `model_dynamic_countercheck_32_6_HSLM-A1_330.OUT`
- `model_dynamic_countercheck_32_6_HSLM-A1_330_no_cable.OUT`

Excel export nam trong hai thu muc ket qua:

- `model_dynamic_countercheck_32_6_HSLM-A1_330/`
- `model_dynamic_countercheck_32_6_HSLM-A1_330_no_cable/`

## Kiem tra OUT

Ca hai bai chay deu khong thay warning/error chinh theo cac tu khoa `ERROR`, `WARNING`,
`FATAL`, `ABNORMAL`, `TERMINAT`, `FAILED`, `NOT CONVERG`, `SINGULAR`, `INSTABILITY`.

Thiet lap phan tich giong nhau:

- Valid DOF: 895.
- Transient method: modal analysis.
- Mass type: lumped mass.
- Damping method: modal damping.
- Time step: 6703 buoc, `dt = 0.001 s`.
- `ALL FREQUENCIES HAVE BEEN CHECKED`: yes.

## Ket qua so sanh nhanh

Muc tieu bao cao muc 5.7:

- `n0 = 5.066 Hz`.
- `amax = 2.30 m/s2`.
- `delta_dynamic = 2.97 mm`.
- Case khong che: HSLM-A1 @ 330 km/h.

| Mo hinh | n0 mode 1 (Hz) | Chenh n0 voi bao cao | DZ max tai node 100016 | Acc DZ max tai node 100016 |
| --- | ---: | ---: | ---: | ---: |
| Co cap + G2 mass | 4.790193 | -5.45% | 1.759 mm | 1.14845 m/s2 |
| No-cable + G2 mass | 4.717181 | -6.89% | 1.622 mm | 0.994675 m/s2 |

Noi luc dong luc doc tu `Beam Force.xls`:

| Mo hinh | My abs max | Vz abs max |
| --- | ---: | ---: |
| Co cap + G2 mass | 5531.27 | 531.96 |
| No-cable + G2 mass | 4973.87 | 496.54 |

So voi no-cable, mo hinh co cap:

- Tang tan so khoang 1.55%.
- Tang gia toc DZ tai 330 km/h khoang 15.5%.
- Tang chuyen vi DZ tai 330 km/h khoang 8.4%.
- Tang My abs max khoang 11.2%, Vz abs max khoang 7.1%.

## Nhan xet ky thuat

1. G2 mass da co tac dung ro. Truoc khi them G2 mass, export cu co `n0 = 5.89363 Hz`.
   Sau khi them G2 mass, mo hinh co cap con `n0 = 4.790193 Hz`. Nhu vay loi chinh
   truoc do la thieu khoi luong tinh tai phan 2, khong phai do cap lam tang do cung qua lon.

2. Cap/prestress co lam tang do cung, nhung muc tang nho. Bo cap lam `n0` giam tu
   `4.790193 Hz` xuong `4.717181 Hz`, chi khoang 1.55%. Vi vay cap khong phai nguyen
   nhan chinh gay lech lon so voi bao cao.

3. Sau khi them G2 mass, mo hinh dang hoi mem/nang so voi bao cao. `n0` hien tai thap
   hon bao cao 5.45%. Neu khoi luong da dung, do cung hieu dung can tang xap xi
   `(5.066 / 4.790193)^2 - 1 = 11.8%` de khop tan so. Neu khoi luong hien tai cao
   hon khoi luong bao cao, phan chenh tan so se giam bot nhung chua het.

4. Case A1 @ 330 km/h khong con nam dung dinh cong huong cua mo hinh hien tai. Voi
   khoang lap A1 `D = 18 m`, toc do cong huong xap xi:
   - Bao cao: `5.066 * 18 * 3.6 = 328.3 km/h`.
   - Co cap hien tai: `4.790193 * 18 * 3.6 = 310.4 km/h`.
   - No-cable hien tai: `4.717181 * 18 * 3.6 = 305.7 km/h`.

   Do do, tai 330 km/h ket qua hien tai co the da qua dinh cong huong cua model moi.
   Can sweep quanh 300-335 km/h truoc khi ket luan response thap do load/damping.

5. Ket qua tai 330 km/h van thap hon bao cao dang ke:
   - Co cap: `amax = 1.14845 m/s2`, thap hon bao cao khoang 50.1%.
   - Co cap: `delta = 1.759 mm`, thap hon bao cao khoang 40.8%.

   Nguyen nhan tiep theo can soi la vi tri dinh cong huong, khoi luong hieu dung, do cung
   section/stage, modal mass participation va cach khai bao doan tau HSLM.

## Viec can lam tiep

1. Sweep nhanh HSLM-A1 quanh dinh du kien cua mo hinh hien tai:
   `290, 300, 305, 310, 315, 320, 325, 330, 335, 340 km/h`.

2. Xuat them modal mass participation hoac bang participation factor tu MIDAS. Mo hinh
   hien co 5 nhip/doc lap nen 5 mode dau gan trung nhau; mass participation co the bi
   chia ra giua cac mode trung tan so.

3. Rasoat khoi luong tren met dai:
   - Self-weight da convert mass qua `*STRUCTYPE`.
   - `G2_REPORT = 106.75 kN/m` da convert mass qua `*LOADTOMASS`.
   - Can doi chieu tong khoi luong hieu dung voi khoi luong bao cao `32.705 t/m`.

4. Rasoat do cung hieu dung section/stage sau khi co khoi luong dung. Neu giu khoi
   luong hien tai, can tang do cung hieu dung khoang 11.8% moi khop `n0 = 5.066 Hz`.

5. Kiem tra don vi va pattern tai HSLM-A1:
   - Axle load 170 kN.
   - Coach spacing `D = 18 m`, axle spacing `d = 2 m`.
   - Toc do 330 km/h doi dung sang m/s.
   - Cach noi suy luc vao node/element theo thoi gian.

6. Sau khi dinh A1 da duoc xac dinh va tan so/mass duoc khop, moi sweep day du HSLM
   A1-A10 theo dai toc do thiet ke.

## Modal mass participation can xuat/doc

Trong `Eigenvalue Mode.xls` hien tai da co du cac block can cho nhan xet mass tham gia:

- `MODAL PARTICIPATION MASSES PRINTOUT`: mass participation theo % va cumulative %.
- Bang mass tuyet doi ngay sau block tren: `MASS` va `SUM`.
- `MODAL PARTICIPATION FACTOR PRINTOUT (kN,m)`.
- `MODAL DIRECTION FACTOR PRINTOUT`.

Vi vay neu export `Eigenvalue Mode.xls` da gom cac block nay thi khong can xuat them
file rieng. Neu MIDAS chi export moi bang tan so/chu ky, can vao bang ket qua Eigenvalue
va tick them modal participation mass, modal participation factor, modal direction factor,
all modes va all components `UX, UY, UZ, RX, RY, RZ`.

So lieu da doc tu file hien tai:

| Mo hinh | Mode 1-5 freq | UZ mass moi mode | UZ sum sau 5 mode | RY sum sau 5 mode |
| --- | ---: | ---: | ---: | ---: |
| Co cap + G2 mass | 4.790193-4.790195 Hz | 15.32% | 76.61% | 73.62% |
| No-cable + G2 mass | 4.717181-4.717183 Hz | 15.34% | 76.71% | 73.71% |

Nhan xet: 5 mode dau gan trung tan so do model co 5 nhip doc lap. Khi doi chieu voi bao
cao khong nen chi lay mass participation cua mode 1; can cong cum mode 1-5 cho dao dong
dung co ban.

## Rasoat khoi luong huu hieu

Gia tri `32.705 kg/m` trong trao doi duoc hieu la `32.705 t/m` hoac `32705 kg/m`.
Neu dung tai trong bao cao:

- `G1 = 214.1 kN/m`.
- `G2 = 106.75 kN/m`.
- `(G1 + G2) / 9.806 = 32.720 t/m`, gan nhu trung voi `32.705 t/m`.

Trong MCT hien tai, self-weight khong nhap truc tiep bang `214.1 kN/m`, ma lay tu section
hinh hoc nhan voi `DEN = 25 kN/m3` va convert mass qua `*STRUCTYPE`.

Tinh nhanh tu section trong MCT:

| Pham vi | Area binh quan | G1 tu section | G1 + G2 quy doi |
| --- | ---: | ---: | ---: |
| Full girder 32.6 m | 8.8163 m2 | 220.41 kN/m | 33.36 t/m |
| Support span/load span 31.5 m | 8.7135 m2 | 217.84 kN/m | 33.10 t/m |
| Bao cao | - | 214.10 kN/m | 32.72 t/m |

Nhu vay cach tinh self-weight trong MIDAS dang cao hon bao cao khoang 1-2% neu tinh theo
line mass tong. Sai khac nay co the lam tan so giam khoang 0.5-1.0%, nhung khong du giai
thich viec `n0` thap hon bao cao 5.45%. Phan con lai van can rasoat stiffness/section/stage.

## Rasoat stiffness section/stage

MCT dong hien tai:

- Vat lieu C50: `E = 37,278,000 kN/m2`, `DEN = 25 kN/m3`.
- Section PSC: `Box-01`, `Box-03`, tapered `Box-1-3`, `Box-3-1`.
- Iyy binh quan tren full girder: `9.1873 m4`, `E*Iyy = 342,482,934 kN.m2`.
- Iyy binh quan tren support span: `9.0968 m4`, `E*Iyy = 339,109,741 kN.m2`.
- Dynamic MCT co TDM definitions va prestress load, nhung khong co construction stage
  sequence rieng cho eigen; eigen dang chay tren full model tai trang thai khai bao hien tai.

Neu khoi luong giu nhu hien tai, de tu `4.790193 Hz` len `5.066 Hz` can stiffness hieu
dung tang khoang 11.8%. Neu sua line mass ve dung bao cao truoc, stiffness con can tang
xap xi 9-11%. Can doi chieu lai `E`, `Iyy`, tapered length/area, support stiffness va
viec co/khong tinh tendon transformed stiffness trong modal.

## Rasoat HSLM-A1 pattern

Pattern trong script hien tai:

- `coach_count = 18`.
- Moi coach co 2 truc: `x = i * D` va `x = i * D + d`.
- `D = 18 m`, `d = 2 m`.
- `P = 170 kN/truc`.
- Toc do doi bang `v_mps = kmh / 3.6`.
- Luc duoc chia ve hai node lan can bang shape function tuyen tinh.
- `*DYN-NLOAD` dat phuong `Z`, scale `-1`, nen function duong tao luc di xuong.
- Khong nhan them dynamic factor Phi, phu hop voi time-history moving load.

Can kiem bang tay mot moc: tai thoi diem mot truc nam dung node giua, tong luc tren node
do nen co gia tri cuc bo `170 kN` neu khong co truc khac cung anh huong; khi truc nam
giua hai node, hai node lan can chia tong `170 kN`.

## MCT sweep da sinh

Da sinh cac file co cap + G2 mass sau:

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

Sau khi chay MIDAS, luu export moi vao thu muc rieng theo ten case/toc do. Can export toi thieu:

- `.OUT`.
- `Eigenvalue Mode.xls`.
- `Displacement.xls`.
- `Absolute Accel..xls`.
- Neu can doi chieu: `Relative Accel..xls`, `Velocity.xls`, `Beam Force.xls`.
