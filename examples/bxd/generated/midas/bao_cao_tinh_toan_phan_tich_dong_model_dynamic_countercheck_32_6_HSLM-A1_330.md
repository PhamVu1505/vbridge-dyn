# Báo cáo phân tích động model_dynamic_countercheck_32_6_HSLM-A1_330

Cập nhật: 2026-07-03

## Nguồn

- MCT: `model_dynamic_countercheck_32_6_HSLM-A1_330.mct`
- OUT: `D:\2026\09_Dynamic_analysis_for_high_speed_railway_bridges\vbridge-dyn\examples\bxd\generated\midas\model_dynamic_countercheck_32_6_HSLM-A1_330\model_dynamic_countercheck_32_6_HSLM-A1_330.OUT`
- Result folder: `D:\2026\09_Dynamic_analysis_for_high_speed_railway_bridges\vbridge-dyn\examples\bxd\generated\midas\model_dynamic_countercheck_32_6_HSLM-A1_330`

## Kiểm tra chạy

- Dynamic inputs: 155; MCT nodal loads: 155.
- Time steps: 8142; dt = 0.001 s; ETIME = 8.142545 s.
- Valid DOF: 895.
- Warning/error chính: không thấy.

## Kết quả chính

| Đại lượng | Báo cáo | MIDAS mới | Chênh |
| --- | ---: | ---: | ---: |
| Tần số mode 1 | 5.066 Hz | 4.790 Hz | -5.4% |
| Gia tốc giữa nhịp | 2.300 m/s2 | 1.189 m/s2 | -48.3% |
| Chuyển vị giữa nhịp | 2.970 mm | 1.811 mm | -39.0% |

- Gia tốc DZ toàn cục: 1.195 m/s2 tại node 100013, t=1.646s.
- Chuyển vị DZ toàn cục: 1.811 mm tại node 100016, t=1.551s.
- UZ modal mass mode 1 = 15.32%; UZ sum mode 1-5 = 76.61%; RY sum mode 1-5 = 73.62%.
- My abs max = 5682.89 kN.m tại elem 100015; Vz abs max = 547.05 kN tại elem 100029.

## Đầu ra

- Word: `D:\2026\09_Dynamic_analysis_for_high_speed_railway_bridges\vbridge-dyn\examples\bxd\generated\midas\bao_cao_tinh_toan_phan_tich_dong_model_dynamic_countercheck_32_6_HSLM-A1_330.docx`
- Phụ lục Excel: `D:\2026\09_Dynamic_analysis_for_high_speed_railway_bridges\vbridge-dyn\examples\bxd\generated\midas\bao_cao_tinh_toan_phan_tich_dong_model_dynamic_countercheck_32_6_HSLM-A1_330_phu_luc.xlsx`
