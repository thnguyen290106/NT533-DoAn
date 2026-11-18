# Kiểm kê hạ tầng D8 trước pilot

- Kiểm tra trực tiếp hai Ubuntu qua SSH đã ghim khóa tại 2026-11-18T14:18:15.599Z. HOST đang chạy bản D7 `f3c1ae21a14a62d491ed16a7ce7dff0da8bebb71`; SHA-256 cấu hình NGINX trong container là `f7c9b5d7c0e77e5d586195064cd71e22c25be311bd92d8b223ba6e62007d2b62`.
- Docker xác nhận 9 backend có healthcheck đạt, mỗi JVM 0,5 CPU và 512 MiB. Cùng NGINX, Prometheus và Grafana, tổng quota là 5888 MiB. Thêm I4 thì cần 6400 MiB trước Ubuntu và Docker. Không phát hiện OOM tại thời điểm kiểm kê.
- Kiểm cả 1.000 prefix /24 mô phỏng và 5.000 hàng từ trace thường. Hai điều kiện A3 dùng địa chỉ NAT chung; 5.000 hàng kiểm tra dùng `10.250.0.10`. Đây là kết quả xác minh input, chưa phải traffic chính thức.
- Cấu hình chạy thật dùng HTTP/1.1, 2 NGINX workers, 4.096 connection mỗi worker, keepalive 32, connect 200 ms, send/read 3 s, buffer và retry tắt. Cổng management của app không publish; Prometheus/Grafana chỉ bind loopback.
- Biên trên của sai lệch clock trong lượt kiểm tra là 48.45 ms. Kết nối HTTP LAN tới cổng 8080 chạy được; listener pilot 8081 chưa mở trong bản mặc định. Trước pilot phải xác minh lại listener bảo vệ cho đúng peer LOADGEN.
- HOST hiện có 5878 MiB RAM. Áp dụng yêu cầu preflight đã ghi ở D1 trước khi chạy pilot đủ cụm. Chưa khóa N/R_ref, chưa có kết quả chiến dịch D9–D11.
