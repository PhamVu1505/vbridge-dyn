# BXD 32.6 m - so sanh MIDAS / bao cao

- MIDAS exports: `D:\2026\09_Dynamic_analysis_for_high_speed_railway_bridges\vbridge-dyn\examples\bxd\generated\midas`
- Bao cao goc: `projects\de tai BXD\Bao_cao_tinh_toan_thiet_ke_dam_HSR_nhom_tren_30m.docx`
- Workbook chi tiet: `D:\2026\09_Dynamic_analysis_for_high_speed_railway_bridges\vbridge-dyn\examples\bxd\generated\midas\comparison_bxd_32_6.xlsx`

| Nhóm | Đại lượng | Trạng thái | Đơn vị | Báo cáo | MIDAS | Sai khác % | Ghi chú |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Nội lực 4.2 | G1 trọng lượng bản thân giữa nhịp | Đã so | kNm | 26,554.000 | 25,780.860 | -2.912 | MIDAS tự tính theo hình học/taper; báo cáo dùng q_G1 tại mặt cắt giữa nhịp. |
| Nội lực 4.2 | G2 tĩnh tải giai đoạn 2 giữa nhịp | Đã so | kNm | 13,240.000 | 13,240.160 | 0.001 | OK |
| Nội lực 4.2 | Mô men âm lớn nhất do dự ứng lực | Đã so | kNm | -64,546.000 | -62,213.550 | -3.614 | Sai khác cơ bản do cách kể dự ứng lực/mất mát giữa báo cáo và tendon MIDAS. |
| Nội lực 4.2 | LM71 hai làn | Đã so | kNm | 24,108.000 | 24,121.260 | 0.055 | OK |
| Nội lực 4.2 | LM71 hai làn x phi | Đã so | kNm | 27,220.000 | 27,232.900 | 0.047 | OK |
| Nội lực 4.2 | Xe vận chuyển | Đã so | kNm | 37,889.000 | 37,958.380 | 0.183 | OK |
| Nội lực 4.2 | Xe vận chuyển x hệ số động | Đã so | kNm | 41,678.000 | 41,754.220 | 0.183 | OK |
| Tổ hợp 4.2 | Khai thác không kể DUL: G1+G2+LM71*phi | Đã so | kNm | 67,014.000 | 66,253.920 | -1.134 | Tổng từ các thành phần; không phải load case export trực tiếp. |
| Tổ hợp 4.2 | ULS khai thác LM71 | Đã so | kNm | 93,191.000 | 92,166.090 | -1.100 | Sai khác theo trọng lượng bản thân MIDAS. |
| Tổ hợp 4.2 | ULS vận chuyển | Đã so | kNm | 98,364.000 | 97,435.490 | -0.944 | OK; tổ hợp đã bỏ G2_REPORT. |
| Lực cắt 4.2 | Phản lực gối do trọng lượng bản thân | Đã so | kN | 3,372.075 | 3,594.434 | 6.594 | Khác do MIDAS lấy trọng lượng theo hình học/taper. |
| Lực cắt 4.2 | Lực cắt ULS khai thác có DUL | Cần rà DUL | kN | 7,536.000 | 8,433.850 | 11.914 | Sai khác cơ bản do ảnh hưởng dự ứng lực: tendon xiên trong MIDAS sinh lực cắt đứng và mất mát DUL khác báo cáo. |
| Ứng suất 5.1 | Ứng suất căng kéo 3 ngày | Đã so | MPa | -15.650 | -16.000 | 2.236 | Theo bảng 5.1: Căng kéo kiểm sigma_bot,min, bot = Cb3/Cb4. |
| Ứng suất 5.1 | Ứng suất khai thác SLS | Đã so | MPa | -4.410 | -3.770 | -14.512 | Theo bảng 5.1: Khai thác kiểm sigma_bot,max; phải dùng envelope max của tổ hợp moving load, không dùng all/min. |
| Ứng suất 5.1 | Ứng suất thi công - vận chuyển SLS | Đã so | MPa | -4.160 | -3.510 | -15.625 | Theo bảng 5.1: Thi công kiểm sigma_bot,max để không kéo thớ dưới; lấy đúng bot = Cb3/Cb4 tại giữa nhịp. |
| Ứng suất 5.1 | Ứng suất dài hạn 100 năm | Đã so | MPa | -2.870 | -2.810 | -2.091 | Theo bảng 5.1: Dài hạn kiểm sigma_top,min, top = Cb1/Cb2. |
| Độ võng/vồng 5.2 | Độ võng do LM71 | Đã so | mm | 8.400 | 8.056 | -4.095 | Độ võng xuống lấy trị tuyệt đối của DZ_min; không dùng DZ_max vì đó là chiều ngược. |
| Độ võng/vồng 5.2 | Độ vồng sau lắp tĩnh tải GĐ2 | Đã so | mm | 18.920 | 24.114 | 27.452 | So cùng mốc sau lắp tĩnh tải GĐ2 trong mục 5.2. |
| Độ võng/vồng 5.2 | Độ vồng dài hạn 100 năm | Đã so | mm | 17.360 | 33.059 | 90.432 | So cùng mốc dài hạn 100 năm trong mục 5.2. |
| Độ võng/vồng 5.2 | Chênh lệch độ vồng | Đã so | mm | 1.560 | -8.945 | -673.397 | Dấu âm nghĩa là MIDAS tăng vồng theo thời gian; cần rà time-dependent/DUL. |
| Góc xoay 5.2 | Góc xoay tại đầu dầm do LM71 | Đã so | mrad | 0.267 | 0.720 | 169.663 | Báo cáo ghi góc xoay tại đầu dầm; MIDAS lấy đúng node đầu dầm. |
| Góc xoay 5.2 | Góc xoay tại đầu dầm do vận chuyển | Đã so | mrad | 0.408 | 1.296 | 217.647 | Báo cáo ghi góc xoay tại đầu dầm; MIDAS lấy đúng node đầu dầm. |
| Mỏi 5.8 | Mỏi - mô men kiểm toán | Đã so | kNm | 25,072.000 | 31,469.130 | 25.515 | Theo EN: lấy biên độ nội lực do LM71 alpha=1.0, có Phi, nhân lambda=1.04; không dùng LM71 alpha=0.90 của mục hoạt tải thường. |
| Mỏi 5.8 | Mỏi - ứng suất bê tông | Đã so | MPa | 5.200 | 6.439 | 23.827 | Theo EN: lấy biên độ ứng suất = max-min do LM71 alpha=1.0, có Phi, nhân lambda=1.04. |
| Mỏi 5.8 | Mỏi - ứng suất cáp dự ứng lực | Cần bổ sung | MPa | 21.100 |  |  | Cần công thức/thiết kế cáp hoặc xuất kết quả tendon stress range để so trực tiếp. |
| Mỏi 5.8 | Mỏi - ứng suất cốt đai | Cần bổ sung | MPa | 21.200 |  |  | Cần công thức kiểm toán cốt đai theo báo cáo hoặc module design riêng. |
| Động lực 5.7 | Tần số dao động riêng n0 | Đã so | Hz | 5.066 | 5.894 | 16.337 | Mode uốn đứng đầu của nhóm dầm song song; export hiện tại cao hơn báo cáo. |
| Động lực 5.7 | Gia tốc động lớn nhất HSLM-A | Đã so | m/s² | 2.300 | 1.163 | -49.435 | Báo cáo khống chế bởi A1 @ 330 km/h; export hiện tại thấp hơn đáng kể, cần sweep thêm tốc độ/case HSLM nếu muốn tìm giá trị khống chế. |
| Động lực 5.7 | Độ võng động lớn nhất HSLM-A | Đã so | mm | 2.970 | 1.405 | -52.694 | Báo cáo khống chế bởi A1 @ 330 km/h; export hiện tại thấp hơn đáng kể, cần kiểm lại damping/khối lượng và sweep tốc độ nếu cần khớp báo cáo. |