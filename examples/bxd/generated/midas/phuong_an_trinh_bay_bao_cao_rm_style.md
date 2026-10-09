# Phuong an trinh bay lai bao cao tinh toan MIDAS theo mau RM

Nguon tham khao chinh: `report refer RM bridge/report.pdf`, 103 trang. Mau RM co cau truc ro: thong tin mo hinh truoc, tai trong va to hop sau, ket qua tach theo trang thai kiem toan.

## 1. Nhan xet ve mau RM

- Moi trang co header gom don vi lap, ten du an, ten cau, ten bao cao va so trang. Nen ap dung tuong tu cho bao cao MIDAS de de kiem tra phien ban va truy vet.
- Chuong 1 la `Structural Model`, gom day du node, element, spring/support, mat cat, tai trong, stage.
- Muc `Spring Declaration` dat rat som, ngay sau element parameters. Dieu nay hop ly vi dieu kien lien ket la mot phan cua mo hinh ket cau, khong nen de sau phan tai trong.
- Tai trong duoc tach thanh `Load case definitions`, sau do moi den bang load combination/envelope. Cach nay giup doi chieu tung nguon tai truoc khi kiem tra to hop.
- Stage thi cong co bang rieng, the hien thoi diem bat dau, duration, activation, creep/shrinkage, prestress/grout/stress output.
- Chuong 2 la `Results`, tach theo trang thai: construction stage, after construction, service, strength, extreme, shear/ultimate diagram.

## 2. Bo cuc de xuat cho bao cao MIDAS BXD 32,6 m

### Trang bia va muc luc

- Ten du an, hang muc, mo hinh tinh, phien ban file MCT/MCB, ngay tao bao cao.
- Nguon du lieu: file MCT, file xls xuat tu MIDAS, file bao cao BXD goc, file DXF tendon.
- Muc luc theo 2 chuong lon: `1. Mo hinh tinh` va `2. Ket qua tinh toan`.

### 1. Mo hinh tinh

1.1. Tong quan mo hinh

- Mo ta 5 dam 32,6 m, bo qua tru mong, mo hinh dam va goi ke dam.
- Don vi tinh, he truc toa do, quy uoc dau noi luc/ung suat.
- So luong node, element, vat lieu, mat cat, group, stage, load case, combination.

1.2. Node - toa do

- Bang tom tat theo tung dam: node dau, node cuoi, chieu dai, cao do.
- Bang chi tiet node dua vao phu luc Excel/Word. Trong Word chi nen chen cac dong mau va ghi ro phu luc day du.

1.3. Element - tham so phan tu

- Bang tom tat element theo tung dam: so phan tu, chieu dai nho nhat/lon nhat, mat cat su dung.
- Bang chi tiet: element id, node i, node j, chieu dai, vat lieu, mat cat, group.

1.4. Lien ket va support

- Tach thanh muc rieng theo cach RM dat `Spring Declaration`.
- Bang `Boundary group`: group `Support`, loai khai bao `CONSTRAINT`, stage kich hoat `ABNDR=Support, ORIGINAL`.
- Bang `Support node`: node goi, dam, vi tri x, ma rang buoc, Dx, Dy, Dz, Rx, Ry, Rz.
- Bang dien giai:
  - Node local 2 cua moi dam: `111100`, khoa Dx, Dy, Dz, Rx; mo Ry, Rz.
  - Node local 30 cua moi dam: `011100`, khoa Dy, Dz, Rx; mo Dx, Ry, Rz.
- Bo sung hinh so do goi tren mat bang/line model neu sinh duoc tu node.
- Ket qua phan luc goi se dat o chuong 2 de doi chieu voi khai bao support nay.

1.5. Vat lieu va dac trung theo thoi gian

- Bang vat lieu be tong, cap du ung luc.
- Bang creep/shrinkage, cuong do theo tuoi, tuoi be tong tai tung stage.
- Ghi ro cach MIDAS tu tinh co ngot/tu bien theo stage.

1.6. Mat cat dam va taper group

- Bang mat cat box, dac trung hinh hoc: A, Iy, Iz, torsion constant, vi tri thotop/thobot neu co.
- Bang taper group cho cac doan chuyen tiep `box-1-3`, `box-3-1`.
- Neu can doi chieu ung suat theo cb1, cb2, cb3, cb4, can them bang quy uoc thotop/thobot: cb1/cb2 la thot tren, cb3/cb4 la thot duoi.

1.7. Cap du ung luc

- Bang thong so tendon: vat lieu, duong kinh tao cap, so tao, dien tich, he so ma sat, wobble, anchorage set, luc cang.
- Bang profile tendon: tendon id, group, element gan cap, toa do diem profile, vi tri dau/cuoi.
- Chen so do bo tri cap da tao tu DXF.
- Ghi chu hien tai logic doc tendon dung rieng cho bai toan BXD; element gan cap lay tu DXF va diem refer dung de xac dinh nhom cap.

1.8. Tai trong va load case

- Tach theo tung nguon tai:
  - Trong luong ban than: MIDAS tu tinh tu hinh hoc va vat lieu.
  - Tinh tai phu/lan can/duong ray/thiet bi neu co.
  - Du ung luc.
  - Van chuyen/thi cong.
  - Gio ngang, ghi chu can tiep tuc lam ro cong thuc trong bao cao BXD.
  - Hoat tai LM71: uu tien moving load/vehicle load tich hop cua MIDAS.
  - Moi: bien do noi luc do LM71 nhan he so lambda = 1,04.
- Moi load case can co bang: ten MIDAS, loai tai, nguon du lieu, he so, don vi, muc bao cao BXD lien quan.

1.9. Construction stage

- Bang stage: ten stage, duration, tuoi be tong, active element, active support, active load, tendon stress/grout, creep/shrinkage.
- Dac biet phai the hien cac moc 3 ngay, 36 ngay, 100 nam de doi chieu do vong, do vong nguoc va ung suat.

1.10. To hop tai trong va quy tac lay max/min

- Bang combination: ten to hop MIDAS, thanh phan, he so, trang thai kiem toan, muc bao cao BXD.
- Them bang quy tac lay ket qua:
  - Do vong dung gia tri bat loi theo DZ va quy uoc dau.
  - Ung suat khai thac theo bang bao cao: bot/top phai map dung cb3/cb4 va cb1/cb2.
  - Luc cat, moment, phan luc goi can ghi ro lay max/min hay envelope nao.

### 2. Ket qua tinh toan

2.1. Ket qua stage thi cong

- Do vong/do vong nguoc tai 3 ngay, 36 ngay, 100 nam.
- Ung suat giai doan cang keo, thi cong/van chuyen neu co.

2.2. Noi luc sau thi cong

- Moment, luc cat, phan luc goi cho cac load case chinh.
- Neu so sanh voi bao cao BXD, can ghi ro vi tri tiet dien va dau noi luc.

2.3. SLS - trang thai gioi han su dung

- Ung suat khai thac theo to hop dac trung `M = MPe + MSLS`.
- Do vong hoat tai LM71, goc xoay tai dau dam.
- Bang so sanh gom cot: gia tri bao cao, gia tri MIDAS, sai khac, nguon trong bao cao, ghi chu.

2.4. ULS / Strength

- Noi luc thiet ke, kha nang chiu moment/luc cat neu co du du lieu.
- Ghi ro phan nao da tinh trong MIDAS, phan nao can tinh hau xu ly.

2.5. Fatigue

- Bien do noi luc do LM71, nhan lambda = 1,04 theo EN 1991-2 Phu luc D.
- So sanh voi yeu cau bao cao neu bao cao co muc moi; neu bao cao chua co, ghi la ket qua bo sung theo EN.

2.6. Extreme / Dynamic

- De muc rieng cho cac bai toan dong va HSLM se trien khai sau.

2.7. Tong hop doi chieu

- Bang checklist tat ca chi tieu can doi chieu voi bao cao BXD cho dam 32,6 m.
- Trang thai: da so sanh, can xuat them ket qua, can lam ro dinh nghia, chua trien khai.

## 3. Phu luc

- Phu luc A: node chi tiet.
- Phu luc B: element chi tiet.
- Phu luc C: support/boundary chi tiet.
- Phu luc D: vat lieu, mat cat, tendon.
- Phu luc E: tai trong, stage, combination.
- Phu luc F: ket qua xuat tu MIDAS.
- Phu luc G: bang so sanh voi bao cao BXD va quy tac max/min.

## 4. Dieu chinh so voi bao cao hien tai

- Doi bo cuc tu dang tong hop nhanh sang dang `Model definition -> Load definition -> Stage/combination -> Results`, giong mau RM.
- Dua `Lien ket va support` len som, ngay sau element.
- Tach phan tai trong thanh tung load case thay vi mot bang chung.
- Them bang quy tac max/min vi day la nguyen nhan de nham khi so sanh ung suat, do vong, luc cat va phan luc.
- Giu bao cao Word gon, nhung day cac bang dai sang phu luc Excel; trong Word chi chen bang tom tat, bang kiem tra va duong dan phu luc.
- Bo sung header/footer, so trang, thong tin file nguon, ngay tao bao cao.

## 5. Buoc thuc hien tiep theo

1. Cap nhat `build_bxd_32_6_calculation_report.py` de sinh bao cao theo bo cuc moi.
2. Chen them bang support day du va bang dien giai ma rang buoc.
3. Them hinh so do line model/support neu can tao tu node.
4. Sap xep lai ket qua theo cac muc kiem toan cua bao cao BXD.
5. Tao lai Word va Excel phu luc, sau do doi chieu voi checklist hien tai.
