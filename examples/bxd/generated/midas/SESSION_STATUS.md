# Trang thai phien BXD 32.6 m

Cap nhat: 2026-06-24.

## Da thuc hien

- Da them combo `SLS_TRANSPORT_P = SelfWeight + Prestress + TRANSPORT_DYN` vao `examples/bxd/static_countercheck_32_6.yaml`.
- Da cap nhat script rebuild so sanh de doc them:
  - `Beam Stress.xls`
  - `Beam Stress_construction.xls`
  - `Displacements(Global)_construction.xls`
- Da bo cac muc huong dan Bridge Girder Diagram va dien giai dai khoi file Word so sanh.
- Da them so sanh muc 5.1 ung suat, muc 5.2 do vong/do vong/goc xoay tai dau dam, va muc 5.8 moi.
- Da them khai bao moi EN trong MCT:
  - `Load Model 71 Fatigue` voi alpha=1.0.
  - `LM71_FAT_2T_PHI` co he so dong Phi.
  - `FATIGUE_LM71_EN = LM71_FAT_2T_PHI * lambda`, voi `lambda=1.04`.
- Da doc export moi tu `32.6m_check_2.mcb` va cap nhat so sanh:
  - `SLS_TRANSPORT_P` da co ung suat thi cong SLS.
  - `FATIGUE_LM71_EN` da co mo men moi va bien do ung suat be tong.
  - `Tendon Stress Limit Check.xls` chua dung de dien moi cap vi day la bang kiem gioi han ung suat tendon, khong phai stress range moi.
- Da sua logic so sanh ung suat muc 5.1 theo bang bao cao:
  - `top = Cb1/Cb2`, `bot = Cb3/Cb4`.
  - Cang keo: `sigma_bot,min`.
  - Khai thac: `sigma_bot,max` tai node giua nhip `x00016`, dung `SLS_CHAR_LM71(max)`, khong dung `SLS_CHAR_LM71(all/min)`.
  - Thi cong: `sigma_bot,max` tai node giua nhip `x00016`.
  - Dai han: `sigma_top,min`.
- Da ra lai cac hang co lien quan max/min:
  - Noi luc mo men duong dung `(max)`.
  - Do vong LM71 dung `LM71_2T(min)` va lay `abs(DZ_min)`.
  - Goc xoay dau dam va luc cat doi chieu dang dung tri tuyet doi envelope hai dau/hai chieu.
  - Ung suat moi be tong dung bien do `FATIGUE_LM71_EN(max) - FATIGUE_LM71_EN(min)`.
- Da tao bao cao tinh toan MIDAS doc lap:
  - `bao_cao_tinh_toan_midas_bxd_32_6.docx`.
  - `bao_cao_tinh_toan_midas_bxd_32_6_phu_luc.xlsx`.
  - `tendon_layout_bxd_32_6.png`.
  - Script tai tao: `build_bxd_32_6_calculation_report.py`.
  - Bao cao gom node, element, lien ket/support, mat cat, vat lieu, tai trong, cap DUL, stage, to hop, tong hop ket qua va phu luc.
- Da tao README huong dan tai tao report.
- Da tham khao mau RM bridge report tai `report refer RM bridge/report.pdf` va lap phuong an trinh bay lai bao cao MIDAS:
  - `phuong_an_trinh_bay_bao_cao_rm_style.md`.
  - Huong chinh: bo cuc `Mo hinh tinh -> Tai trong/stage/to hop -> Ket qua`, dua `Lien ket va support` len ngay sau node/element, tuong tu muc `Spring Declaration` trong mau RM.
- Da cap nhat `build_bxd_32_6_calculation_report.py` va tao lai bao cao Word theo bo cuc RM-style:
  - Trang bia, muc luc noi dung, header/footer.
  - Chuong 1 `Mo hinh tinh`, gom support ngay sau node/element.
  - Chuong 2 `Ket qua tinh toan`, tach noi luc/phan luc, ung suat, do vong-vong-goc xoay, moi va checklist.
  - Phu luc Excel them sheet `support_interpretation` va `support_activation`.
- Da them model dong doi chung muc 5.7:
  - `dynamic_countercheck.py` sinh `model_dynamic_countercheck_32_6_HSLM-A1_330.mct`.
  - Da sinh them bien the khong cap: `model_dynamic_countercheck_32_6_HSLM-A1_330_no_cable.mct`.
  - Case khong che theo bao cao: HSLM-A1 @ 330 km/h, damping 1,5%, node giua nhip `100016`.
  - MCT co `*TFUNCTION`, `*THLDCASE`, `*DYN-NLOAD`, `*TH-GRAPH` cho `deck acc 32.6` va `deck dz 32.6`.
  - MCT dong da them khoi luong G2: self-weight convert tu `*STRUCTYPE`, `G2_REPORT = 106,75 kN/m` convert qua `*LOADTOMASS`.
  - Ban `no_cable` tat `prestress.enabled`, khong co `*TDN-PROPERTY`, `*TDN-PROFILE`, `*TDN-PRESTRESS` va khong co loadcase `Prestress, PS`; van giu G2 mass va HSLM time-history.
- Da doc export dong luc cu va cap nhat muc 5.7:
  - `model_dynamic_countercheck_32_6_HSLM-A1_330.OUT` chay xong, khong thay loi/canh bao chinh.
  - `Eigenvalue Mode.xls`: mode 1 = 5,89363 Hz.
  - `Absolute Accel._dynamic.xls`: node 100016, DZ = 1,162995 m/s2.
  - `Displacement_dynamic.xls`: node 100016, abs DZ = 1,405 mm.
  - `rebuild_comparison_bxd_32_6.py` da them parser modal/dynamic va dien 3 dong muc 5.7 vao `comparison_bxd_32_6.xlsx`.
  - Luu y: export dong luc tren la truoc khi them G2 vao mass; can chay MIDAS lai tu MCT moi de cap nhat ket qua.
- Da kiem tra export dong luc moi sau khi them G2 mass:
  - `model_dynamic_countercheck_32_6_HSLM-A1_330.OUT`: khong thay warning/error chinh, 895 valid DOF, 6703 buoc, `dt = 0.001 s`.
  - `model_dynamic_countercheck_32_6_HSLM-A1_330_no_cable.OUT`: khong thay warning/error chinh, thiet lap phan tich tuong tu.
  - Co cap + G2 mass: `n0 = 4.790193 Hz`, `DZ = 1.759 mm`, `Acc DZ = 1.14845 m/s2` tai node `100016`.
  - No-cable + G2 mass: `n0 = 4.717181 Hz`, `DZ = 1.622 mm`, `Acc DZ = 0.994675 m/s2` tai node `100016`.
  - Bo cap chi lam tan so giam khoang 1.55%, nen cap/prestress khong phai nguyen nhan chinh cua lech lon.
  - Da luu nhan xet chi tiet vao `dynamic_result_review_2026_06_24.md`.
- Da rasoat them modal participation trong `Eigenvalue Mode.xls`:
  - File hien tai da co `MODAL PARTICIPATION MASSES PRINTOUT`, bang mass tuyet doi, `MODAL PARTICIPATION FACTOR PRINTOUT`, `MODAL DIRECTION FACTOR PRINTOUT`.
  - Co cap: mode 1-5 gan `4.790193-4.790195 Hz`, moi mode UZ khoang 15.32%, UZ sum sau 5 mode = 76.61%.
  - No-cable: mode 1-5 gan `4.717181-4.717183 Hz`, moi mode UZ khoang 15.34%, UZ sum sau 5 mode = 76.71%.
- Da rasoat line mass:
  - Bao cao: `(214.1 + 106.75) / 9.806 = 32.720 t/m`, gan muc `32.705 t/m`.
  - MCT tu section + G2: khoang `33.10-33.36 t/m`, cao hon bao cao 1-2%.
  - Sai khac mass nay khong du giai thich `n0` thap hon bao cao 5.45%; can tiep tuc soi stiffness.
- Da rasoat stiffness/HSLM:
  - `E = 37,278,000 kN/m2`, Iyy binh quan full girder `9.1873 m4`, support span `9.0968 m4`.
  - Dynamic MCT chua co construction stage sequence rieng cho eigen.
  - HSLM-A1 dung `18 coaches`, `D=18 m`, `d=2 m`, `P=170 kN`, `v=kmh/3.6`, load Z scale `-1`.
- Da sinh MCT sweep co cap + G2 mass cho cac toc do:
  - `290, 300, 305, 310, 315, 320, 325, 330, 335, 340 km/h`.

## Can lam tiep

- Neu can ket luan day du muc moi, bo sung cong thuc hoac output design cho ung suat cap du ung luc va cot dai.
- Tiep tuc ra cong thuc/design output cho ung suat cap du ung luc va cot dai moi.
- Ra tiep nguyen nhan sai khac lon o do vong/vong/goc xoay do DUL/time-dependent neu can.
- Chay MIDAS cac MCT sweep HSLM-A1 da sinh, moi toc do luu export vao thu muc rieng theo ten case/toc do.
- Xuat them modal mass participation/participation factor tu MIDAS, vi mo hinh 5 nhip doc lap co 5 mode dau gan trung tan so.
- Rasoat khoi luong hieu dung voi muc bao cao `32.705 t/m`: self-weight mass + `G2_REPORT = 106.75 kN/m` qua `*LOADTOMASS`.
- Rasoat do cung hieu dung section/stage; neu khoi luong hien tai dung, can tang do cung hieu dung xap xi 11.8% de khop `n0 = 5.066 Hz`.
- Kiem tra don vi/pattern tai HSLM-A1 truoc khi sweep day du A1-A10.
- Sau khi tan so, mass participation va dinh A1 da hop ly, moi sweep day du cac toc do/case HSLM va cap nhat bang so sanh muc 5.7.
- Dong/mo file Word neu script bao loi permission khi ghi de.

## File dau ra can xem

- `model_static_countercheck_32_6.mct`
- `comparison_bxd_32_6.xlsx`
- `comparison_checklist_bxd_32_6.md`
- `so_sanh_midas_bao_cao_bxd_32_6_moc_3d_36d_100y.docx`
- `bao_cao_tinh_toan_midas_bxd_32_6.docx`
- `bao_cao_tinh_toan_midas_bxd_32_6_phu_luc.xlsx`
- `phuong_an_trinh_bay_bao_cao_rm_style.md`
- `model_dynamic_countercheck_32_6_HSLM-A1_330.mct`
- `model_dynamic_countercheck_32_6_HSLM-A1_330_no_cable.mct`
- `AGENT_HANDOFF_DYNAMIC.md`
- `dynamic_result_review_2026_06_24.md`
