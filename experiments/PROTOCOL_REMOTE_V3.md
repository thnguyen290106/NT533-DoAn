# NT533 · Giới hạn công việc đồng thời tại Catalog

- `protocol_version=nt533-q05-remote-v3`, `topology=remote-zerotier`. [Quy tắc đo của phiên bản v2](PROTOCOL_REMOTE_V2.md) tiếp tục áp dụng cho warm-up, SLO, validity, dữ liệu WAN và ma trận thí nghiệm.
- Lượt v2 ở 80 req/s có 1.019/4.800 request đo thành công. Ba replica Catalog gần chạm quota CPU. NGINX ghi timeout khi chờ Catalog và có lúc không còn upstream khả dụng. Success RPS lệch 12,28% trong hai cửa sổ cuối. Giữ hồ sơ v2 và verdict G3 của lượt đó.
- Mỗi replica Catalog cho phép tối đa hai request `cpu-fixed` tính SHA-256 đồng thời. Khi đủ hai request, endpoint lab trả HTTP 503 với mã `BENCH_OVERLOADED`. Request đã được nhận vẫn tính lại đúng N vòng và checksum theo Q04. Quota Catalog được giữ ở 0,75 vCPU mỗi replica. Các route nghiệp vụ giữ contract hiện hành.
- HTTP 503 được ghi trong raw và tính vào error rate đầu cuối. Giữ ngưỡng lỗi dưới 1%, p95 đầu cuối dưới 500 ms cho direct và dưới 1.000 ms cho Quote, throughput và dropped iterations theo Q05. Một lượt vượt SLO vẫn phải báo FAIL.
- Hai cửa sổ 30 giây cuối warm-up giữ ngưỡng lệch success RPS 5% và p95 NGINX 10%. Nếu vượt một trong hai ngưỡng sau 300 giây thì chặn G3. Chạy lại pilot trên runtime v3, thu cả p95/p99 LOADGEN và NGINX, RTT, jitter, packet loss và tài nguyên LOADGEN. Dùng một cấu hình đã khóa cho RR, LC, IPH và CH-ID.
