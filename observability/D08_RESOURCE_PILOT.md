# D08-TTN · Tài nguyên pilot theo Q05

| Profile | Pass liền trước | R_ref | M | H |
|---|---:|---:|---:|---:|
| cpu-fixed | 40 | 80 | 48 | 80 |
| mixed-delay | 160 | 320 | 192 | 320 |
| quote | 160 | 320 | 192 | 320 |

- Khởi động 300 s, đo 60 s và cooldown tối thiểu 60 s ở mọi bậc. Các lượt được dùng đều đồng hồ trong giới hạn 100 ms, client hợp lệ và dropped bằng 0.
- Min RAM còn khả dụng trên LOADGEN lần lượt 2906, 1798, 1860 MiB. Mỗi Catalog dùng 0.75 vCPU ở mọi profile. Inventory và Order dùng 0,5 vCPU mỗi replica. Runtime a96cfe9dec1d250456b21e1813672b584ac3e71b.
- Peak CPU LOADGEN theo mẫu 5 s là 20.82% qua 19 lượt. Cả HOST và LOADGEN có swap tắt, bộ đếm OOM và swap không tăng trong pilot. HOST còn 7783 MiB RAM khả dụng tại thời điểm kiểm sau pilot.
- Đối chứng riêng ở 20 req/s: 0.5 vCPU đạt p95 warm-up 51/44 ms · 0.75 vCPU đạt p95 warm-up 51/50 ms · 0.75 vCPU đạt p95 warm-up 55/53 ms. Lượt đối chứng được lưu riêng và không dùng để tính R_ref.
- Hai lượt SLO fail ở R_ref của mỗi profile được giữ cùng SHA-256 trong biên nhận G3. Lượt fail vẫn giữ raw và phân biệt với lượt không hợp lệ.

| Run ID | Rate | LOADGEN p95 / p99 ms | NGINX p95 / p99 ms | RTT p95 ms | Jitter ms | Gói mất/gửi | SLO |
|---|---:|---:|---:|---:|---:|---:|---|
| PILOT-cpu-fixed-RR-r10-20261120T170350284448Z-a1 | 10 | 64.00 / 71.00 | 42.00 / 43.00 | 14.50 | 1.67 | 0/355 | PASS |
| PILOT-cpu-fixed-RR-r20-20261120T171056273137Z-a1 | 20 | 64.00 / 72.00 | 42.00 / 43.00 | 16.40 | 5.05 | 0/355 | PASS |
| PILOT-cpu-fixed-RR-r40-20261120T171805725112Z-a1 | 40 | 64.00 / 129.00 | 41.00 / 115.00 | 16.50 | 7.85 | 0/356 | PASS |
| PILOT-cpu-fixed-RR-r80-20261121T001850548807Z-a1 | 80 | 168.00 / 184.00 | 155.00 / 169.00 | 13.80 | 3.40 | 1/357 | FAIL |
| PILOT-cpu-fixed-RR-r80-20261121T002625086320Z-a2 | 80 | 155.00 / 174.00 | 142.00 / 161.00 | 12.90 | 5.26 | 0/357 | FAIL |
| PILOT-mixed-delay-RR-r10-20261121T003414122076Z-a1 | 10 | 216.00 / 227.00 | 203.00 / 203.00 | 14.10 | 4.05 | 0/355 | PASS |
| PILOT-mixed-delay-RR-r20-20261121T004146296550Z-a1 | 20 | 215.00 / 226.00 | 202.00 / 203.00 | 13.10 | 3.61 | 0/355 | PASS |
| PILOT-mixed-delay-RR-r40-20261121T004920880851Z-a1 | 40 | 214.00 / 224.00 | 202.00 / 202.00 | 12.90 | 1.55 | 0/356 | PASS |
| PILOT-mixed-delay-RR-r80-20261121T005655601257Z-a1 | 80 | 214.00 / 224.00 | 202.00 / 202.00 | 12.70 | 1.63 | 1/357 | PASS |
| PILOT-mixed-delay-RR-r160-20261121T010432811249Z-a1 | 160 | 215.00 / 225.00 | 202.00 / 202.00 | 13.20 | 7.94 | 0/360 | PASS |
| PILOT-mixed-delay-RR-r320-20261121T011209621125Z-a1 | 320 | 220.00 / 4098.00 | 202.00 / 202.00 | 15.40 | 5.27 | 1/368 | FAIL |
| PILOT-mixed-delay-RR-r320-20261121T011948690498Z-a2 | 320 | 218.00 / 4074.00 | 202.00 / 202.00 | 15.30 | 7.25 | 1/368 | FAIL |
| PILOT-quote-RR-r10-20261121T012801830269Z-a1 | 10 | 34.00 / 38.00 | 10.00 / 11.00 | 13.80 | 1.37 | 0/355 | PASS |
| PILOT-quote-RR-r20-20261121T013533884270Z-a1 | 20 | 31.00 / 43.00 | 8.00 / 22.00 | 13.50 | 5.28 | 1/354 | PASS |
| PILOT-quote-RR-r40-20261121T014309373440Z-a1 | 40 | 29.00 / 32.00 | 7.00 / 8.00 | 12.20 | 1.18 | 0/356 | PASS |
| PILOT-quote-RR-r80-20261121T015044968526Z-a1 | 80 | 30.00 / 33.00 | 7.00 / 7.00 | 13.50 | 2.95 | 0/357 | PASS |
| PILOT-quote-RR-r160-20261121T015822652221Z-a1 | 160 | 29.00 / 33.00 | 7.00 / 9.00 | 13.80 | 4.40 | 1/358 | PASS |
| PILOT-quote-RR-r320-20261121T020559856814Z-a1 | 320 | 3599.00 / 4585.00 | 284.00 / 1807.00 | 18.60 | 10.67 | 1/368 | FAIL |
| PILOT-quote-RR-r320-20261121T022359877281Z-a2 | 320 | 40.00 / 2488.00 | 8.00 / 15.00 | 14.50 | 2.83 | 2/366 | FAIL |
