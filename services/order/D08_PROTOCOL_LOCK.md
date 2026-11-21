# D08-TDN · Khóa G3

- Runtime đã đo a96cfe9dec1d250456b21e1813672b584ac3e71b. Runner đã khóa SHA-256 bd905ec4c1fdc2f38db685ecba977e7f93c80855a052b8d37a4e9fc9fa7f244c. Cấu hình Compose của G3 có SHA-256 4bc56feb3cc64ed2ac7770fa00e9910f931cc9a7d837b540a6761fa9b596f958. Quota Catalog 0.75 vCPU mỗi replica được áp dụng đồng đều, hiệu chuẩn CPU dùng cùng quota. Kết nối tin cậy theo biên nhận D08-DHN và kiểm lại trước pilot.
- Đường phát tải dùng ZeroTier qua WAN, giữa hai LAN vật lý. Phiên bản nt533-q05-remote-v3 có topology remote-zerotier.
- PR #33 tái sử dụng buffer SHA-256 32 byte trong từng request. Sáu mức đối chiếu trên JDK 21 giữ nguyên checksum. Hiệu chuẩn sau triển khai chọn N=512000, median app 35.652 ms trên 100 request, checksum 4574569b6a4629b360feb2dd5704ce37acb2d6f2d0a69fed43278ebd52a9df2d.
- PR #35 giới hạn hai phép tính SHA-256 đồng thời tại mỗi Catalog. HTTP 503 được tính vào error rate. Chấp nhận số đo pilot trên runtime a96cfe9dec1d250456b21e1813672b584ac3e71b.
- B3 Quote dùng profile riêng và dùng IP thực của LOADGEN.
- Ngưỡng direct p95 dưới 500 ms, Quote dưới 1.000 ms và tỷ lệ lỗi dưới 1% theo Q05. Hai cửa sổ warm-up được kiểm tra trước khi chấp nhận từng pilot. Các lượt chạy chính thức dùng lịch đã khóa.

| Profile | Pass liền trước | R_ref | M | H |
|---|---:|---:|---:|---:|
| cpu-fixed | 40 | 80 | 48 | 80 |
| mixed-delay | 160 | 320 | 192 | 320 |
| quote | 160 | 320 | 192 | 320 |
