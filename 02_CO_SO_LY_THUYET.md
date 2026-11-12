> **Vận hành v2 — chưa chạy D01:** ADMIN chọn D1–D14; năm worker thực hiện ngày được chọn, không tự chuyển ngày. Mọi task ban đầu chưa thực hiện. Code/test chạy trong workspace riêng trên Ubuntu HOST/LOADGEN; server tự Git/PR/merge theo CI và review AI, không chờ duyệt PR thông thường. Không áp ngưỡng CPU/RAM/disk để chặn bắt đầu; lỗi OOM/hết disk hoặc test thất bại vẫn phải báo thật. Các mục Windows/WSL, quyền duyệt và ngưỡng mở lab của mô hình cũ bên dưới được thay bởi hồ sơ này và AGENTS.md; số liệu, raw, RQ/API/protocol không được giả hoặc đổi để làm đẹp kết quả.

# CƠ SỞ LÝ THUYẾT — NT533, BẢN TRIỂN KHAI 2 TUẦN

**Môn học:** Hệ tính toán phân bố (NT533), UIT.  
**Phạm vi:** Spring Boot, Docker, NGINX; Round Robin, Least Connections, IP Hash; đo lường và đánh giá thực nghiệm; mở rộng Consistent Hash theo client-ID (CH-ID).  
**Cập nhật:** 10/11/2026 — chốt NT533-v1 tại mục 0A, đồng bộ kế hoạch 14 ngày và PCCV 5 thành viên. **Đi kèm:** [Kế hoạch và phân công](01_KE_HOACH_DO_AN.md).

> Tài liệu dùng để học, thiết kế thí nghiệm và phát triển chương cơ sở lý thuyết. Ví dụ số là minh họa toán học, không phải kết quả của nhóm. Cấu hình mẫu chưa được chạy trong môi trường đồ án; cần kiểm tra với phiên bản đã khóa.

## 0A. Hồ sơ quyết định NT533-v1 — chốt ngày 10/11/2026

Phần này có cùng nội dung trong cả hai tài liệu và là đặc tả để triển khai. Các task “chốt/thiết kế/duyệt” trong PCCV được thực hiện bằng cách áp dụng, kiểm tra và lưu evidence cho các quyết định dưới đây, không mở lại việc lựa chọn từ đầu. **Đã chốt thiết kế không có nghĩa đã viết code, chạy thử, được giảng viên duyệt hoặc hoàn thành task trong Excel.** Nếu phần diễn giải cũ khác đặc tả này, sửa phần diễn giải theo đặc tả trước khi triển khai; không tự chọn một trong hai.

### Q01. RQ, giả thuyết và scope đã chốt

| RQ | Câu hỏi đã chốt | Phép đo/đối chứng |
|---|---|---|
| RQ1 | RR/LC/IPH khác nhau thế nào với backend đồng nhất và thời gian xử lý biến thiên? | B1 CPU-fixed, B2 Mixed-delay, cùng M/H; success RPS, p95/p99, lỗi, count và CPU |
| RQ2 | Một backend chậm hoặc dừng ảnh hưởng chất lượng và phục hồi thế nào? | A1/A2 so B2/M khỏe, cùng trace/block; timeline stop/start/ready |
| RQ3 | CH-ID có giảm tập trung do NAT và giữ affinity theo ID không, kể cả hot-client? | A3 uniform/hot-ID; RR/LC/IPH/CH-ID cùng một IP và trace |
| RQ4 | Bật consistent có giảm remapping khi membership 3→4→3 không? | A4 GH-ID so CH-ID cùng key, membership, endpoint identity |
| RQ5 | 1→3 replica và gọi xuyên dịch vụ thay đổi kết quả ở cùng tải thế nào? | B0 so B1; B3 quote; B4 chỉ diagnostic đường đi |

H1: RR đủ tốt với request đồng nhất. H2: LC có thể giảm tail khi connection bận phản ánh công việc tồn đọng. H3: ID tách client cùng NAT nhưng không chia được một hot key. H4: CH-ID có thể giảm remapping so GH-ID. Đây là giả thuyết cần kiểm chứng; không buộc dữ liệu phải ủng hộ.

**Trong scope:** Catalog, Inventory, Order; mỗi service ba replica; RR/LC/IPH core; CH-ID ở Inventory cho A3, GH-ID/CH-ID cho A4; A1 slow và A2 stop/start. **Ngoài scope:** AWS, Kubernetes/HPA, UI, database ghi, đặt hàng/thanh toán thật, auth production, cache/session store thật, retry ablation, circuit breaker và scheduler adaptive. Không thêm spike/soak vào ma trận chính.

**Ma trận cố định:** B0=6, B1=18, B2=18, B3=9, B4=3, A1=9, A2=9, A3=24 → **96 run chính + 8 xác nhận = 104 run hiệu năng**; A4 = 2 biến thể × 5 bộ khóa × 3 membership × 2 sweep = **60 sweep / 60.000 request**. Giữ nguyên 70 task, owner, effort và ngày trong Excel; không tự đánh dấu hoàn thành. Hai contrast xác nhận: LC–RR tại B2/H; CH-ID–IPH tại A3/uniform, thêm block 4–5 cho đúng hai phía để đạt n=5.

### Q02. API v1 và fixture đã chốt

HTTP/1.1, JSON UTF-8; không thêm `/v1` vào URL hiện có. Request quote bắt buộc `Content-Type: application/json`; kiểu khác → 415 `UNSUPPORTED_MEDIA_TYPE`. Mọi response nghiệp vụ/lab do ứng dụng tạo có `requestId` và `instanceId` ở top-level, kèm `X-Request-ID` và `X-Instance-ID` trùng body; không bọc thêm `data`. Health/Actuator giữ schema của nền tảng. Response nghiệp vụ không chứa timestamp để dễ so sánh fixture. Route không có → 404 `ROUTE_NOT_FOUND`; method không hỗ trợ → 405 `METHOD_NOT_ALLOWED` và header `Allow`.

| Endpoint | Input | Body 200 ngoài requestId/instanceId |
|---|---|---|
| `GET /api/catalog/products` | Không query, không phân trang | `{"products":[{"id":"P001","name":"Ban phim","price":100000,"currency":"VND"},{"id":"P002","name":"Chuot","price":250000,"currency":"VND"},{"id":"P003","name":"Cap USB","price":50000,"currency":"VND"}]}`; thứ tự ID tăng dần |
| `GET /api/catalog/products/{id}` | ID đúng regex `^P[0-9]{3}$` | `{"id":"P001","name":"Ban phim","price":100000,"currency":"VND"}` với ID P001 |
| `GET /api/inventory/{productId}` | Cùng quy tắc ID | `{"productId":"P001","availableStock":100}` với ID P001 |
| `POST /api/orders/quote` | Chính xác `{"productId":"P001","quantity":2}` | `{"productId":"P001","quantity":2,"unitPrice":100000,"totalPrice":200000,"currency":"VND","availableStock":100}` |

Fixture duy nhất: P001/100000 VND/tồn 100; P002/250000 VND/tồn 3; P003/50000 VND/tồn 0. Catalog giữ tên/giá, Inventory giữ tồn; commit fixture cùng source, mọi replica cùng checksum. Giá và tổng dùng số nguyên 64-bit theo đồng, không float; `totalPrice = unitPrice × quantity`. Không giảm tồn, không sinh orderId, không ghi đơn. Quote kiểm tra input → Catalog → Inventory tuần tự; dừng ngay khi một bước lỗi, không gọi tiếp và không retry ở bất kỳ tầng nào.

`quantity` là JSON integer 1–10, không nhận chuỗi, boolean hoặc 2.5; thiếu/null, trường thừa, query không được khai báo, JSON lỗi → 400 `INVALID_INPUT`. ID sai format → 400; ID đúng format nhưng không có fixture (P999) → 404 `PRODUCT_NOT_FOUND`. Tồn < quantity → 409 `INSUFFICIENT_STOCK`, kể cả P003. Catalog 404 được Order trả 404; Inventory 404 khi Catalog có sản phẩm là lỗi không nhất quán fixture → 502 `DOWNSTREAM_BAD_RESPONSE`.

Lỗi ứng dụng có đúng dạng `{"error":{"code":"INVALID_INPUT","message":"Invalid request"},"requestId":"<id>","instanceId":"O1"}`; instance thực tế tùy service. Message ngắn, không lộ stack trace/host. Connection refused hoặc downstream 5xx → 503 `DOWNSTREAM_UNAVAILABLE`; hết deadline → 504 `DOWNSTREAM_TIMEOUT`; body/schema sai hoặc status khác dự kiến → 502 `DOWNSTREAM_BAD_RESPONSE`; lỗi nội bộ chưa xử lý → 500 `INTERNAL_ERROR`. Nếu timeout tại NGINX trước khi app trả lời, giữ status/body proxy, đánh lỗi transport/proxy trong analyzer; không ép body đó thành JSON đúng nghiệp vụ.

RequestId public: NGINX tạo `$request_id`, ghi đè header ngoài. Ingress lab chỉ nhận `X-Request-ID` dạng 32 hex thường từ load generator đã cho phép, thiếu/sai → 400; chuyển nguyên ID này xuống app. B3 gọi `/api/orders/quote` trên listener lab 8081 (proxy giữ nguyên URI tới Order), vì vậy requestId trong trace được giữ; public listener vẫn tạo ID mới. Order dùng cùng requestId cho cả hai call; mỗi call thêm `X-Call-ID` bằng requestId + `-catalog` hoặc `-inventory`. NGINX nội bộ giữ requestId và callId từ Order, không tạo lại. Không dùng requestId làm Prometheus label. X-Instance-ID trả về quote là O1/O2/O3, không ghi đè bằng instance downstream.

Test contract bắt buộc: list đủ ba sản phẩm; P001×2 → 200/200000; P002×3 → 200/750000; P002×4 và P003×1 → 409; P999 → 404; ID sai/quantity 0,11,2.5,"2",null/trường thừa → 400; sai content-type → 415; giả lập từng lỗi downstream → đúng 502/503/504. Kiểm tra cả body, metadata và số lần gọi, không chỉ status.

### Q03. Stack, topology, tài nguyên và config đã chốt

Chọn Spring MVC đồng bộ, Java 21, Maven Wrapper 3.9.9, Spring Boot 3.5.7; dùng BOM của Boot, không tự trộn phiên bản Spring. Image lab chọn NGINX OSS 1.28.3, k6 1.0.0, Prometheus 3.2.1, Grafana 11.6.0; analyzer Python 3.12 với stdlib, chart dùng matplotlib 3.10.1. Đây là baseline tái lập trong mạng cô lập, **không phải tuyên bố các bản này mới nhất/an toàn để đưa production**. Trước lần build phải rà advisory, nếu cần nâng patch thì cập nhật cả hai tài liệu và chạy smoke trước pilot; không đổi giữa các run chính thức. Java patch, OS/Docker/Compose thực tế và image digest chỉ được ghi từ lệnh trên HOST, không tự điền giá trị giả. `versions.lock` và manifest giữ version + digest; không dùng `latest`.

Nguồn phiên bản: [Boot 3.5.7](https://spring.io/blog/2025/10/23/spring-boot-3-5-7-available-now/), [Maven 3.9.9](https://maven.apache.org/docs/3.9.9/release-notes.html), [NGINX 1.28](https://nginx.org/en/CHANGES-1.28), [k6 1.0.0](https://github.com/grafana/k6/releases/tag/v1.0.0), [Prometheus 3.2.1](https://github.com/prometheus/prometheus/releases/tag/v3.2.1), [Grafana 11.6.0](https://github.com/grafana/grafana/releases/tag/v11.6.0), [matplotlib 3.10.1](https://pypi.org/project/matplotlib/3.10.1/). Phiên bản là lựa chọn thiết kế; chưa build/test tương thích trong lần sửa tài liệu này.

Topology cố định cho chiến dịch: một HOST chạy Docker Compose và một LOADGEN riêng cùng LAN; nếu không có máy riêng thì dùng LOADGEN chung host như phương án dự phòng đã chọn, ghi `topology=single-host` và giám sát client; không trộn hai topology trong một chiến dịch. HOST/LOADGEN là vai trò, Nhật điền địa chỉ từ kiểm kê, không giả định máy hiện tại đủ tài nguyên. Điều kiện mở lab v2: năm Codex ready, SSH xác thực thành công và công cụ cần thiết dùng được; không chặn theo CPU/RAM/disk. Giữ cấu hình replica/protocol; ghi lỗi thực thi thật nếu không chạy được.

Tên container `catalog-1..3`, `inventory-1..3`, `order-1..3`; instance `C1..3`, `I1..3`, `O1..3`; A4 thêm `inventory-4`/I4. Port app 8080, management 8082 chỉ nội bộ. Compose có mạng backend/monitoring; chỉ NGINX publish API 8080 và lab 8081 trên địa chỉ LAN được firewall giới hạn LOADGEN. Grafana 3000/Prometheus 9090 chỉ bind loopback; Actuator và backend không publish. B4 chạy qua quyền truy cập private tới C1, không mở C1 ra Internet. Order gọi listener NGINX nội bộ 8083; B3 không truyền IP giả xuống downstream.

Mỗi JVM: 0,5 CPU, 512 MiB, `-Xms256m -Xmx256m`, G1, 32 platform worker threads, accept-count 100, virtual threads off. NGINX: 1 CPU/256 MiB, 2 worker, worker_connections 4096; mọi upstream zone 64k, equal weight=1, keepalive 32, `max_fails=1 fail_timeout=5s`. Monitoring tổng 1 CPU/1 GiB; I4 cùng quota JVM. Đo không swap/OOM, không CPU contention bất thường; nếu footprint không đạt thì dừng preflight và sửa đồng đều trước pilot, không đổi quota riêng một thuật toán.

HTTP/1.1, cache off, `proxy_buffering off`, `proxy_next_upstream off`, connect 200 ms, send/read 3 s, client k6 timeout 5 s, keepalive bật đồng đều. Order: mỗi downstream connect ≤200 ms nằm trong call deadline tổng 1 s; toàn quote deadline 2,5 s, không chỉ dựa vào socket read timeout. Healthcheck readiness 5 s/lần, timeout 2 s, start-period 60 s, 3 retries; runner yêu cầu 3 lần ready liên tiếp trước warm-up, abort sau 120 s. Probe Compose không phải health-check chủ động của NGINX OSS; NGINX vẫn dùng passive failure handling.

### Q04. Workload, trace và seed đã chốt

| Profile/endpoint lab | Hành vi chính xác | Input/output cần kiểm |
|---|---|---|
| `cpu-fixed`: `/bench/catalog` → Catalog `/internal/bench` | SHA-256 lặp N lần, digest vòng trước làm input vòng sau, input đầu UTF-8 `NT533-v1`; tính lại mỗi request, không cache/sleep | Query `profile=cpu-fixed`; body `profile,iterations,checksum,requestId,instanceId`; checksum khớp N |
| `mixed-delay`: `/bench/inventory` → Inventory `/internal/bench` | Query `delayClass=fast` ngủ 20 ms, `slow` ngủ 200 ms; trace chọn 80/20 | Query `profile=mixed-delay&delayClass=fast` hoặc `slow`; body `profile,delayClass,appliedDelayMs,requestId,instanceId` |
| `mapping`: cùng route Inventory | Không delay/CPU loop, không gọi downstream | Query `profile=mapping`; body `profile,requestId,instanceId` |
| `quote`: `/api/orders/quote` | P001, quantity=2; không thêm synthetic delay vào API nghiệp vụ | 200, totalPrice=200000, stock=100; profile quote ở trace, không phải query API |

Không nhận số delay/vòng lặp do client tự truyền. Profile ngoài allowlist hoặc query sai → 400; `/internal/bench` không được route qua API public, Spring profile lab tắt thì route không tồn tại. N áp dụng chung mọi Catalog, xác định bằng pilot theo Q05; Mixed-delay 20/200 ms là giá trị đã chọn, không chỉnh để tạo chiến thắng LC. A1: I3 thêm **300 ms** vào mọi request lab trước thời gian fast/slow, nên appliedDelayMs=320/500; I1/I2 giữ 20/200. B2/A2/A3 không có extra delay. Cleanup trả I3 về 0 ms extra.

Trace CSV UTF-8/LF: `request_index,request_id,client_id,effective_ip,profile,delay_class,product_id,quantity`. Index liên tục từ 0, dùng `scenario.iterationInTest`, không lấy VU ID; requestId = 32 hex đầu SHA-256 của `trace_id:request_index`. Seed block 1–5: **53301,53302,53303,53304,53305**; seed schedule=53300, bootstrap=53399, A4 keyset=**53401..53405**. Luồng độc lập: dùng Python `random.Random(seed)` cho client, `random.Random(seed+100000)` cho delay; schedule dùng seed riêng. Xuất toàn bộ trace trước khi chạy, đóng checksum; block lặp cùng trace trên mọi thuật toán.

A3 và B1/B2/A1/A2 dùng cùng bộ 1.000 client-ID/block: ID thứ j (0..999) là `c-` + 16 hex đầu SHA-256 của `seed:client:j`; trùng ID → abort generator. Uniform chọn `randrange(1000)`; hot-ID chọn ID 0 với xác suất 0,8, còn lại chọn đều 1..999, báo tỷ lệ thực tế từ trace. Delay chọn fast nếu RNG delay <0,8, không gắn fast/slow vào hot-ID. A4 dùng cùng cách sinh với seed 53401..53405, sắp ID tăng dần rồi sweep; keysets phải khác nhau.

IP giả lập cho client j: `10.(64 + j//256).(j%256).10`, tạo 1.000 prefix /24 khác nhau; A3 tất cả dùng `10.250.0.10`. NGINX lab dùng `real_ip_header X-Lab-Source-IP`, `real_ip_recursive off`, `set_real_ip_from` đúng peer LOADGEN thực tế /32 sau kiểm kê; firewall chặn nguồn khác, log cả `$realip_remote_addr` và `$remote_addr`. Không tin toàn mạng 0.0.0.0/0, không expose ingress này. A3/A4 bắt buộc ID regex `^c-[0-9a-f]{16}$` ở tất cả biến thể. B3 dùng IP thực từng hop; IPH downstream hash IP Order, không giả định hash IP người dùng. Trust Real-IP phải kiểm tra theo [module NGINX](https://nginx.org/en/docs/http/ngx_http_realip_module.html).

A4 rate **10 request/s**, concurrency tối đa 1, timeout 5 s; nếu không giữ được rate do lỗi/chậm thì snapshot invalid. Mỗi membership có 2 sweep đủ 1.000 ID, mapping giống nhau 100%; lỗi/schema sai/thiếu key → invalid và chạy lại cả snapshot với ID mới. Sau reload: backend ready, worker generation cũ thoát (tối đa 30 s), đóng connection client cũ/mở mới, smoke xác minh generation mới trước sweep; không đạt → abort. Traffic-weighted remap dùng weight từ trace hot-ID cùng seed keyset; lưu riêng weight CSV/checksum; không suy weight từ response thành công. So cả 3→4, 4→3 và 3 đầu→3 cuối; không ép tỷ lệ đổi bằng 25%.

### Q05. Pilot, SLO, lịch run và ngưỡng quyết định đã chốt

Các giá trị **được đo**, không phải quyết định tùy ý: N CPU, R_ref cho CPU/Mixed/Quote, số VU cần cấp, version/digest và host facts. Không điền số giả. Chốt quy tắc sau để người triển khai không phải tự chọn lại:

1. N CPU: bắt đầu 1.000 vòng, gấp đôi đến tối đa 1.024.000; warm-up 120 s và đo 100 request tuần tự trực tiếp C1, chọn N đầu tiên có median xử lý app ≥20 ms và ≤100 ms. Không tìm được → dừng hiệu chuẩn, ghi log, không đo chính thức. N giống nhau giữa replica/thuật toán.
2. RR/3 replica, từng profile riêng: rate 10,20,40,... tối đa 2.560 request/s; mỗi bước warm-up 120 s/đo 60 s, cooldown tối thiểu 60 s. `R_ref` là bước đầu vi phạm ít nhất một SLO trong 2 lượt cùng rate có client hợp lệ; bước trước phải đạt SLO. Nếu ngay 10 đã trượt, thêm bước 1,2,5; không có bước đạt, hoặc đến 2.560 chưa trượt → dừng pilot, ghi không tìm được điểm tham chiếu trong miền đã chốt, không tự tăng trần.
3. H=R_ref; M=max(1,floor(0,6×R_ref)). B0/B4 dùng rate CPU của B1; A1/A2/A3 dùng M Mixed của B2; B3 dùng M Quote riêng. Không chọn rate riêng theo thuật toán. Cấp trước `ceil(rate×5×1,2)` VU, maxVUs bằng preAllocatedVUs; smoke/pilot phải chứng minh LOADGEN đủ RAM/CPU. Không đủ → đổi máy phát tải trước chiến dịch, không hạ offered load chỉ cho một thuật toán.
4. **SLO cố định:** direct p95 wall-clock thành công <500 ms, quote <1.000 ms, error <1%. Validity: actual sent ≥99% target, dropped=0, đủ raw/trace/config/membership và cùng input, HTTP 200 không sai fixture/schema. Overload/timeouts/HTTP lỗi do backend là kết quả performance, không invalid; sai body 200 do bug implementation là lỗi contract phải sửa và chạy lại toàn bộ cell bị ảnh hưởng, giữ raw cũ. Không hạ SLO theo pilot.
5. Run thường warm-up 120 s, đo 180 s, drain tối đa 5 s, cooldown ≥60 s. A2 đo 300 s; stop I3 tại t=90 s bằng stop timeout 0, start cùng container t=150 s; log thời điểm lệnh/exit và ready thực, không reload config trong run. Nếu warm-up chưa ổn (hai cửa sổ 30 s cuối có success RPS lệch >5% hoặc p95 lệch >10%), tăng warm-up đồng đều lên 300 s và chạy lại pilot; vẫn không ổn → dừng G3. Cập nhật ngân sách nếu tăng, không cắt đoạn dữ liệu bằng mắt.
6. Giữ pairing theo block: B2/M → A1 → A2 cùng algorithm/seed, reset giữa run; các thuật toán trong block đảo thứ tự bằng seed schedule. Các case khác đảo thứ tự thuật toán trong từng cell/block; ghi toàn bộ `schedule.csv` trước khi xem kết quả. D9 chạy B0–B4 (54); D10 A1/A3 và 8 xác nhận (41); D11 A2 (9) và A4 (60 sweep); không chạy chồng host. Máy dự trù 18–20 giờ, 642 phút hiệu năng chưa cộng drain; riêng mapping 60.000/10=100 phút chưa tính setup. Nếu phải tăng warm-up, công bố ngân sách mới trước chạy.
7. Khác biệt thực tiễn: ≥10% giảm p95 hoặc tăng success RPS, **error candidate không lớn hơn baseline**, không đánh đổi đạt SLO thành trượt SLO. n=3: từng run, median/min–max, chỉ kết luận thăm dò. n=5: paired bootstrap 10.000 resample nguyên block, seed 53399, thống kê mean chênh lệch cặp và CI 95% percentile; CI chứa 0 → chưa đủ bằng chứng chiều cải thiện. Không dùng p-value/kiểm định hàng loạt và không gọi “tương đương” vì CI rộng.
8. Recovery A2: mức trước fault = success RPS trong [30,90) s; xét cửa sổ 10 s không chồng, neo tại t=90 s. Đầu của 3 cửa sổ liên tiếp có error <1%, p95 <500 ms, success RPS ≥95% mức trước fault là mốc phục hồi; mỗi cửa sổ ≥100 successful samples, không đủ → N/A. Báo khoảng từ stop thực và ready thực; nếu mốc phục hồi trước ready, ghi đã phục hồi khi I3 còn down và khoảng từ ready là N/A. Không đạt trước t=300 → chưa phục hồi trong thời gian quan sát.

### Q06. Metric, dữ liệu và kiểm thử đã chốt

Latency chính = wall-clock từ ngay trước `http.get/post` đến khi nhận xong hoặc timeout, đơn vị ms; giữ riêng k6 http_req_duration để diagnostic. p50/p95/p99 analyzer dùng nearest-rank `sorted[ceil(p×n)-1]`, n=0 → N/A. Báo latency successful riêng all-completed; timeout là lỗi, không âm thầm bỏ mẫu. p99 với <1.000 successful samples gắn cờ ít mẫu; không dùng để xếp hạng. Success=HTTP/body đúng contract. Throughput theo completion-window; latency/error theo request bắt đầu trong measurement-window và kết thúc đến drain; lưu rõ hai population, pending cuối drain làm run invalid do thiếu dữ liệu.

Scrape trực tiếp từng instance **5 s**, retention **15 ngày**. Custom counter `nt533_requests_total{service,instance,route,status,profile}`, timer `nt533_request_duration_seconds` (count/sum/buckets), timer downstream `nt533_downstream_duration_seconds{service,instance,target,status}`; bucket giây `[0.005,0.01,0.02,0.05,0.1,0.2,0.5,1,2,5]`. Route là template (`/api/inventory/{productId}`), không ID thật. Không gắn requestId/clientId/runId vào metric; phase/algorithm/run được ghép theo manifest và timestamp, không tạo series mới mỗi request. JSONL log: `timestamp_utc,request_id,call_id,service,instance_id,route,profile,status,duration_ms`; NGINX thêm `peer_ip,effective_ip,upstream_addr,upstream_status,request_time_s,upstream_response_time_s,config_generation`. Request không thuộc downstream dùng call_id=null. Health/scrape không tính vào count nghiệp vụ.

Mỗi `results/<run_id>/` có `manifest.json,trace.csv,k6-raw.json,requests.jsonl,nginx.jsonl,app.jsonl,metrics/,events.jsonl,stdout.txt,stderr.txt,exit-code.txt,summary.json,SHA256SUMS`. Run ID: `<scenario>-<condition>-<algorithm>-b<block>-<UTC>-a<attempt>`. Rerun ID mới, manifest `supersedes` trỏ bản lỗi; không ghi đè. Manifest có schema_version=1, scenario/algorithm/condition/repeat/block_id, các seed/trace_sha256, commit/image_digests/config_sha256, host_spec/limits/topology, N/delay, target/actual rate/VU, ip_mode/key_mode, window/retry/fault, status và invalid_reason. Mapping CSV giữ schema `seed,variant,membership,sweep,client_id,instance_id,status,config_hash`; summary chứa sent/completed/success/errors/dropped/RPS/percentiles/per_instance_counts/CV/Jain/validity và sample counts. Chưa có dữ liệu → null/N/A, không thay bằng 0 thành công.

Count vector luôn chứa đủ instance membership kể cả 0; all-zero CV/Jain=N/A. Analyzer phải assert `[100,100,100]` → Jain=1, `[300,0,0]` → Jain=1/3, missing-map invalid, remap 1/4=25%, weighted 80/100=80%; test timeout/error dedup, start/completion boundary, ID/profile validation, percentile n=0/1 và retry-list parser. CI: build/unit từng service; quote contract/integration; `docker compose config`, `nginx -t` cho 5 biến thể; analyzer asserts; không chạy 104 benchmark trong CI. Mọi lệnh có stdout/stderr/exit code, không chỉ ảnh dashboard.

### Q07. Ownership, nghiệm thu và thay đổi sau chốt

| Nhóm quyết định / task PCCV liên quan | Owner / reviewer | Đầu ra đã xác định |
|---|---|---|
| Q01–Q02: D01-TDN, D02-TDN, D03-TDN, D04-TDN | Trương Danh Nhân / Đào Mạnh Nhân | API v1 ở đây; code/contract tests phải bám đặc tả, không còn API v0/nháp để lựa chọn |
| Fixture/CPU: D01-DMN, D04-DMN, D05-DMN, D08-DMN | Đào Mạnh Nhân / Trần Thanh Nguyên | Fixture và thuật toán CPU theo Q02/Q04; N được đo theo Q05 |
| Inventory/metric: D01-TTN, D04-TTN, D06-TTN, D08-TTN | Trần Thanh Nguyên / Đào Hồng Nhật | Delay/metric theo Q04/Q06; readiness và tài nguyên phải có evidence |
| Host/config/fault: D01-DHN, D05-DHN, D06-DHN, D08-DHN | Đào Hồng Nhật / Trương Danh Nhân | Topology/quota/trust theo Q03/Q04, ghi HOST/digest thực; A1=+300 ms, A2=90/150 s |
| Matrix/trace/runner: D01-HXN, D04-HXN, D05-HXN, D06-HXN, D08-HXN | Huỳnh Xuân Nin / Trần Thanh Nguyên | Matrix/seed/schema/schedule theo Q01/Q04–Q06; pilot chỉ điền giá trị đo |
| D07-TDN/D08-TDN, D11-HXN/D12-HXN, D14-TDN | Owner theo PCCV / reviewer theo PCCV | G2 kiểm tra tính năng, G3 kiểm tra protocol đã chốt; G4 khóa raw, G5 báo cáo, G7 bàn giao |

Họp **21:00–21:15 Asia/Ho_Chi_Minh** mỗi ngày, deadline task **22:00** ngày D tương ứng. D1–D14 vẫn là ngày tương đối; lịch 05–18/11/2026 trong workbook chỉ là mốc kế hoạch hiện có, không xác nhận ngày bắt đầu thật hoặc hạn nộp chính thức. Không tự dời lịch vì ngày sửa tài liệu. G0 cần chứng cứ host và phản hồi giảng viên nếu môn học yêu cầu; tài liệu này không thay chữ ký của người khác.

G0: scope/RQ/API đã có trong hồ sơ này, còn xác minh nguồn lực. G1: quote và lỗi đúng contract. G2: 9 replica + 5 biến thể/smoke/test đạt. G3: áp dụng SLO/seed/matrix đã chọn, thêm N/R_ref/VU và lock hashes từ pilot hợp lệ. G4: 104 run hợp lệ và 60 sweep, hoặc bảng thiếu/lý do công khai. G5: báo cáo bảy chương và H1–H6 có raw/run ID. G6: fresh-clone do người khác làm. G7: source tag `nt533-v1`, report PDF, slide PDF/PPTX, video MP4, raw archive/checksum, runbook và PCCV có evidence. Không đánh dấu code/benchmark hoàn tất chỉ vì đã viết đặc tả.

Nếu trễ, thứ tự cắt đã chọn: bỏ B0 trước (96→90 chính, 98 tổng hiệu năng); nếu vẫn không đủ, A4 giảm 5→3 bộ seed đầu (60→36 sweep, 36.000 request). Không cắt B3 xuống nữa vì chỉ còn một mức M. Không cắt thuật toán core, lặp/cell, validation hay raw. Chỉ kích hoạt trước run đầu của chiến dịch, nhóm trưởng ghi lý do và reviewer xác nhận; cập nhật đồng thời hai Markdown và workbook, tổng/claim tương ứng. **Bản hiện tại chưa kích hoạt cắt: vẫn 96+8 và 60 sweep.** Nếu đã chạy thì giữ nguyên dữ liệu, công bố thiếu thay vì đổi protocol hậu nghiệm.

Quyết định v1 không thay đổi bằng trao đổi miệng: PR nêu quyết định cũ/mới/lý do/case bị ảnh hưởng, owner và reviewer theo bảng; cập nhật cả hai Markdown. Đổi scope/matrix/effort/lịch phải cập nhật workbook trước khi chạy tiếp; đổi code/config/profile/SLO làm mất so sánh thì tạo protocol_version mới và chạy lại các cell bị ảnh hưởng, không gộp dữ liệu khác version. Raw lưu bất biến, backup sang thiết bị/thư mục lưu trữ thứ hai kèm SHA-256 trước khi cleanup; không commit secret, không xóa archive chưa bàn giao.

**Còn phải thực hiện, không phải còn phải tự lựa chọn:** kiểm kê HOST/LOADGEN, rà advisory/build/smoke, đo N/R_ref/VU, thu digest/hash thực, thực nghiệm, phản hồi giảng viên, bàn giao. Mỗi giá trị cần đo đã có owner, quy tắc và cổng chặn ở trên. Không có số liệu hiệu năng thật trong lần chốt tài liệu này.

### Q08. Từ số 0: môi trường, repository và quy ước source

**Môi trường v2:** HOST và LOADGEN là hai VM Ubuntu 24.04 riêng. Docker Engine/Compose chạy trên Ubuntu, không dùng Docker Desktop/WSL trên Windows cho thực thi đồ án. ADMIN nhập IP/user/password trên web và xác minh fingerprint. Windows giữ vai trò điều phối/Git/Codex client, không tự cài hoặc đổi cấu hình hệ điều hành Windows. Mỗi task có workspace Ubuntu riêng; bootstrap kiểm kê và dùng lại dependency phù hợp trước khi cài phần thiếu.

**Môi trường v2:** HOST và LOADGEN là hai VM Ubuntu 24.04 riêng. Docker Engine/Compose chạy trên Ubuntu, không dùng Docker Desktop/WSL trên Windows cho thực thi đồ án. ADMIN nhập IP/user/password trên web và xác minh fingerprint. Windows giữ vai trò điều phối/Git/Codex client, không tự cài hoặc đổi cấu hình hệ điều hành Windows. Mỗi task có workspace Ubuntu riêng; bootstrap kiểm kê và dùng lại dependency phù hợp trước khi cài phần thiếu.

**Môi trường v2:** HOST và LOADGEN là hai VM Ubuntu 24.04 riêng. Docker Engine/Compose chạy trên Ubuntu, không dùng Docker Desktop/WSL trên Windows cho thực thi đồ án. ADMIN nhập IP/user/password trên web và xác minh fingerprint. Windows giữ vai trò điều phối/Git/Codex client, không tự cài hoặc đổi cấu hình hệ điều hành Windows. Mỗi task có workspace Ubuntu riêng; bootstrap kiểm kê và dùng lại dependency phù hợp trước khi cài phần thiếu.

```text
NT533-DoAn/
  README.md                          # lệnh theo Q09, yêu cầu máy, giới hạn thực nghiệm
  .gitignore                         # .env, .venv, target/, raw results, runtime, release, key
  .gitattributes                     # source/config/scripts UTF-8 LF, *.sh text eol=lf
  .env.example                       # chỉ tên biến và giá trị lab không nhạy cảm
  versions.lock                      # version/image ID/digest thật sau build
  services/catalog/                  # pom.xml, mvnw, .mvn/, Dockerfile, src/main, src/test
  services/inventory/                # cùng cấu trúc, build/image riêng
  services/order/                    # cùng cấu trúc, build/image riêng
  infra/compose/compose.yaml          # project name nt533, services/limits/health/networks
  infra/nginx/nginx.conf              # cấu hình khung; include runtime/http.conf trong http
  infra/nginx/templates/              # common + rr/lc/iph/ch-id/gh-id, không copy trôi default
  infra/runtime/                      # file sinh ra, không commit; mount directory read-only
  observability/prometheus.yml
  observability/grafana/              # provision datasource + dashboard JSON đã export
  load-tests/main.js                  # k6, đọc trace theo iterationInTest, validate body
  load-tests/trace.py                 # sinh trace CSV/checksum theo Q04, stdlib
  experiments/matrix.csv              # toàn bộ cell/count/condition Q01, không tính tay lại
  experiments/run.py                  # runner CLI stdlib, gọi docker/ssh/scp/k6 bằng argv
  experiments/protocol.json           # version, giá trị pilot, seed, thời gian, SLO, topology
  experiments/schedule.csv            # thứ tự cố định, block, run ID/trace trước chạy
  analysis/analyze.py                 # audit → summary → tables/charts, không sửa raw
  analysis/tests/                     # unittest + tiny raw/mapping fixtures
  analysis/requirements.txt           # matplotlib==3.10.1, khóa dependency resolve trong lock
  docs/                              # bản chụp hai Markdown, API, kiến trúc, runbook, report
  results/                           # raw/manifest bất biến, không commit raw lớn
  release/                           # bộ nộp sinh ở Q15, không commit bản nén
  .github/workflows/ci.yml
```

Mỗi service dùng package `vn.edu.uit.nt533.<catalog|inventory|order>`; Maven groupId `vn.edu.uit.nt533`, artifactId `catalog-service`, `inventory-service`, `order-service`, version `1.0.0`. Dependencies chỉ Spring Boot web/validation/actuator, Micrometer Prometheus, Boot test (JUnit/Mockito từ BOM); không JPA/H2/Lombok/Spring Cloud/OpenFeign. DTO dùng Java record; fixture JSON đọc một lần lúc khởi động, bất biến, lỗi fixture làm readiness fail. Catalog/Inventory: Application, Controller, FixtureStore, BenchController; Order thêm QuoteService và DownstreamClient; mỗi service có local exception handler và request metadata filter, không tạo framework chung.

Order dùng một Java HttpClient dùng lại, HTTP/1.1/connect 200 ms; gửi từng call bằng sendAsync + BodyHandlers.ofString, chờ Future tối đa min(1 s, ngân sách quote còn lại), timeout thì cancel future và trả mã Q02. Quote vẫn là xử lý tuần tự đồng bộ ở MVC, không thêm fan-out song song. Jackson reject unknown fields, float→integer coercion và string/boolean→quantity; kiểm tra JSON type trước binding nếu cấu hình mapper chưa đủ, test các case Q02. Lab chỉ nhận profile/extra delay trong allowlist; không nhận arbitrary URL/file/command từ request.

`.env` local chỉ chứa `HOST_IP,LOADGEN_IP,LOADGEN_USER,REMOTE_ADDR,BACKUP_DIR`; `REMOTE_ADDR` là Git remote thật. Chọn địa chỉ sau kiểm kê, không hard-code account/IP của người khác. `.env.example` dùng slot `HOST`, `LOADGEN`, `USER`, `BACKUP`; runner từ chối slot chưa thay. Các biến workload/rate/SLO/seed không nằm trong `.env`, lấy từ protocol đã khóa để tránh sửa ngoài kiểm soát. Image local gắn `<service>:<git-short-sha>`; ghi cả `.Id` và RepoDigest nếu có, vì image build local có thể chưa có RepoDigest. Maven Wrapper/dependency lock và digest là evidence build, không bịa chúng trong tài liệu.

### Q09. Chuỗi dựng và vận hành end-to-end đã chốt

**Các lệnh dưới đây là giao diện triển khai đã chốt, không phải lệnh đã được chạy trong lần sửa Markdown.** `experiments/run.py`, `analysis/analyze.py` và source chưa tồn tại trong workspace hiện tại; owner phải tạo chúng theo hợp đồng bên dưới trước khi dùng. Không báo build/smoke/benchmark thành công chỉ vì có các dòng lệnh này.

**Môi trường v2:** HOST và LOADGEN là hai VM Ubuntu 24.04 riêng. Docker Engine/Compose chạy trên Ubuntu, không dùng Docker Desktop/WSL trên Windows cho thực thi đồ án. ADMIN nhập IP/user/password trên web và xác minh fingerprint. Windows giữ vai trò điều phối/Git/Codex client, không tự cài hoặc đổi cấu hình hệ điều hành Windows. Mỗi task có workspace Ubuntu riêng; bootstrap kiểm kê và dùng lại dependency phù hợp trước khi cài phần thiếu.

**Môi trường v2:** HOST và LOADGEN là hai VM Ubuntu 24.04 riêng. Docker Engine/Compose chạy trên Ubuntu, không dùng Docker Desktop/WSL trên Windows cho thực thi đồ án. ADMIN nhập IP/user/password trên web và xác minh fingerprint. Windows giữ vai trò điều phối/Git/Codex client, không tự cài hoặc đổi cấu hình hệ điều hành Windows. Mỗi task có workspace Ubuntu riêng; bootstrap kiểm kê và dùng lại dependency phù hợp trước khi cài phần thiếu.

`run.py` có đúng các subcommand nêu trên: config, smoke, pilot, plan, preflight, run, rerun, backup, reproduce, close; không thêm GUI/daemon. Exit 0=thao tác kỹ thuật hoàn tất và raw/audit hợp lệ, **không có nghĩa SLO đạt**; exit 2=preflight/input/schema/đủ tải không hợp lệ; exit 3=process/SSH/Docker/thu thập lỗi; Ctrl-C giữ raw và chạy finally. Giữ nguyên exit code child trong manifest (kể cả k6 threshold fail) và phân biệt performance fail với runner failure. Mọi subcommand ghi command/UTC/stdout/stderr/exit/evidence path; đường dẫn RUN_ID không được chứa `..` hoặc separator.

### Q10. Bộ test, CI và điều kiện dừng đã chốt

| Lớp kiểm tra | Case bắt buộc | Owner / bằng chứng đạt |
|---|---|---|
| Catalog | fixture đúng ba ID/giá/thứ tự; unknown/invalid ID; query/method lỗi; checksum CPU cùng N | Mạnh Nhân / JUnit XML và command log |
| Inventory | tồn 100/3/0; 20/200 và extra 300; mapping không sleep; reject profile lạ | Nguyên / JUnit và timer test có tolerance, không assert sleep đúng tuyệt đối từng ms |
| Order | toàn bộ case Q02; số call chính xác; Catalog fail không gọi Inventory; timeout cancel; ID/Call-ID xuyên hop; không retry | Nhân trưởng / JUnit + local fake HTTP server, không thêm mocking proxy dependency |
| Proxy/replica | nginx -t cả 5 variant; đúng route/body; C/I/O đúng service; đủ 9 instance; LC có concurrency | Nhật / smoke JSONL + config hash + inventory container/IP |
| Trust boundary | ngoài allowlist bị chặn; thiếu/sai lab ID/requestId; giả header public bị ghi đè; Actuator/8083 không truy cập từ LOADGEN | Nhật + Nin / negative smoke; không coi regex ID là authentication |
| Trace/runner | checksum tái sinh, client/delay độc lập, không dùng VU ID; allowlist/rate cap; Ctrl-C/child fail vẫn reset; resume không trùng run | Nin / unittest với fake child process, dry-run và một run ngắn thật |
| Analyzer | các expected values Q06; malformed/missing JSON/CSV, duplicate ID/key, zero samples, p95 nearest-rank, orphan downstream | Nin, Mạnh Nhân review / unittest + audit report |
| Recovery/mapping | I3 stop/start đúng container; ready timeline; I4 add/remove; không đổi I1–I3 endpoint; same-snapshot stability | Nhật + Nguyên / events/CSV và cleanup readiness |
| Reproduction/release | reviewer clone sạch, verify/build, một case ngắn, chart từ raw giữ nguyên; giải nén archive và verify checksum | Nhân trưởng, Mạnh Nhân review / fresh-clone log + release audit |

Workflow một file: PR/main → Java 21 → `mvnw verify` ba service → Python unit → Compose config → image build → `nginx -t` năm config → smoke core/private boundary với 1 replica/service → upload JUnit/audit/log và cleanup luôn chạy. Full 9-replica/all-variant/fault smoke chạy trên HOST G2 và trước chiến dịch vì tài nguyên CI có thể không đủ; không tuyên bố CI đã kiểm chín replica nếu chỉ chạy ba. Actions/dependency versions pin commit/digest khi dựng workflow, ghi trong versions.lock; không dùng action `@main`. Tham khảo [Maven CI chính thức](https://docs.github.com/en/actions/tutorials/build-and-test-code/java-with-maven).

Không merge khi compile/test/schema fail. Không qua G2 khi route/contract/reset fail. Không qua G3 khi IP/ID/trace/client/protocol sai. Không loại run chỉ vì lỗi/latency cao do quá tải. Hết thời gian nhưng evidence thiếu thì công bố thiếu và thu hẹp kết luận, không đổi `status=valid` bằng tay. Negative test được gắn suite riêng, không gộp 400/404 cố ý vào error benchmark.

### Q11. Triển khai proxy, reset, fault và an toàn dữ liệu đã chốt

`compose.yaml` dùng project name `nt533`, tên service/container tường minh Q03. NGINX chờ backend healthy ở lần khởi tạo bằng `depends_on: condition: service_healthy`; app readiness chỉ phản ánh instance tự sẵn sàng, không fail đồng loạt vì dependency tạm down. Order không restart tự động khi Inventory chết trong A2. Container restart policy `unless-stopped`, không watchdog riêng làm I3 tự quay lại giữa fault. [Quy tắc startup Compose](https://docs.docker.com/compose/how-tos/startup-order/).

Renderer tạo `infra/runtime/nginx/http.conf` từ common + đúng một variant, ghi file tạm rồi rename trong **directory** được bind mount read-only; không bind riêng inode file sinh. Validate config trước apply, lưu bản cũ; validate/reload fail → khôi phục file/config trước đó, giữ stderr và không chạy tiếp. Mỗi variant public/lab/internal route cùng upstream service; core đổi directive cả Catalog/Inventory/Order, CH-ID/GH-ID chỉ Inventory lab. Thay membership chỉ trong A4; mọi server weight=1, tên/port/thứ tự ổn định. Retry/cache/buffering/worker/connection/quota lấy common Q03, không rải default ở năm file.

A1 extra delay chọn bằng property `lab.extra-delay-ms` (allowlist 0 hoặc 300) trong directory config riêng từng Inventory, mount read-only và đọc lúc startup. Runner ghi property cho I3 rồi restart **cùng container** trước warm-up; không thêm admin/fault HTTP endpoint, không nhận delay tùy ý từ client. Trước mọi run hiệu năng: reset extra=0 rồi restart cùng chín app container theo cùng chính sách; A1 đặt extra=300 cho I3 ngay trong reset đó; chờ ready rồi warm-up. `INSTANCE_ID` không đổi. Không recreate trong A2; nếu phải recreate nơi khác và IP đổi, reload/xác minh membership trước run, không đổi giữa cửa sổ đo.

I4 khai báo sẵn dưới Compose profile `mapping`, cùng image/fixture/quota I1–I3; ngoài A4 không chạy. A4: start I4/ready → config membership=4/reload/drain → snapshot → config membership=3/reload/drain → stop I4, I1–I3 không recreate. A2: `docker compose -f infra/compose/compose.yaml stop -t 0 inventory-3` tại t=90, `start inventory-3` tại t=150; không sửa upstream config. Log Docker container ID và địa chỉ thực ở mọi transition, không chỉ tên I3.

Finally/reset luôn đưa extra=0, I3 running/ready, membership=3, I4 stopped, NGINX về RR, đóng client đang phát tải; lưu exit code cleanup riêng. Cleanup fail → dừng batch, đánh tình trạng môi trường lỗi và Nhật xử lý; không chạy tiếp trên stack còn fault. `docker compose down` chỉ dùng sau close; không `down -v`, không prune Docker toàn máy. Mọi đường dẫn backup/cleanup phải resolve nằm trong repo hoặc BACKUP_DIR đã chỉ định; không xóa theo input tự do.

Disk preflight: ngoài mức tối thiểu Q03, ước lượng raw bytes/s từ pilot × thời gian còn lại × **1,5**; không đủ thì dừng và bổ sung ổ lưu, không bỏ request log. Mỗi run sau audit tạo SHA256SUMS và copy nguyên run sang BACKUP_DIR trên thiết bị/thư mục lưu trữ thứ hai; kiểm tra checksum tại đích. Giữ cả archive invalid và log fault; logs chỉ ID giả lập, không dữ liệu cá nhân/token/key; bản release quét secret trước public. Giờ hệ thống đồng bộ, lưu UTC và monotonic offset; nếu lệch clock giữa máy >100 ms thì sửa trước run, không căn timeline bằng mắt sau đo.

### Q12. Pipeline dữ liệu → bảng/hình → trả lời RQ đã chốt

Một nguồn số liệu duy nhất: raw + manifest bất biến → `analysis/analyze.py audit` → `summary.json` từng run → `docs/generated/run_table.csv` → bảng aggregate và chart. Không nhập tay số benchmark vào Excel/Word/slide. Mọi table row/chart caption có protocol_version, scenario/condition/rate/algorithm/block/run IDs, n và đơn vị; dữ liệu khác protocol/topology không gộp chung. Gộp successful/HTTP/network/business errors theo Q06, không bỏ instance zero-count; reject duplicate result hoặc thiếu cohort.

| File trong docs/generated | Nội dung đã chốt | Kết luận được phép |
|---|---|---|
| `T01-environment.csv` | host/VM/LOADGEN/quota/version/image ID/config/fixture hashes | Mô tả môi trường thật, không phải thông số thiết kế giả làm đo |
| `T02-run-ledger.csv` | toàn bộ valid/invalid/rerun/missing, n thực mỗi cell | Độ đầy đủ, lý do loại; không giấu run xấu |
| `T03-performance.csv` | từng run + median/min–max success RPS/error/p50/p95/p99/count/CPU | RQ1/RQ5 theo M/H, không suy capacity_3/capacity_1 nếu chưa tìm capacity riêng |
| `T04-confirmation.csv` | 5 cặp/block của hai contrast, mean paired difference/CI/effect % | Chiều khác biệt và giới hạn small-n, không chọn contrast mới |
| `T05-affinity-remap.csv` | eligible keys/coverage, affinity, remap thường/có trọng số, stability từng seed | RQ3/RQ4; lỗi không thành remap, key thiếu làm snapshot invalid |
| `T06-recovery.csv` | stop/start/ready, cửa sổ/điều kiện/mốc recovery hoặc N/A | RQ2, tách slow/down/membership |
| `H1-architecture.svg` | sơ đồ public/lab/private/monitoring, C/I/O và fan-out | Sơ đồ thiết kế, không phải ảnh chụp bằng chứng đã deploy |
| `H2-performance-*.png` | success RPS, actual rate, error; mean/p95 ở panel riêng B1/B2 | Không lấy latency lỗi nhanh để xếp hạng |
| `H3-distribution-*.png` | count share đủ 3 instance, CV/Jain và CPU | Count fairness khác CPU fairness |
| `H4-fault-*.png` | A1 so healthy, A2 time series + stop/start/ready | Recovery theo Q05, không suy HA nhiều host |
| `H5-nat-*.png` | uniform/hot-ID, IPH/CH-ID và RR/LC controls, affinity/coverage | Đổi IP→ID và giới hạn hot-key |
| `H6-remap-*.png` | GH-ID/CH-ID, 3→4,4→3,3 đầu→3 cuối, 5 seed + stability | Tác động consistent cùng key, không ép 25% |

Chart PNG 1600×900 hoặc lớn hơn khi cần đọc nhãn, giữ cùng màu RR/LC/IPH/CH-ID/GH-ID giữa hình; không dual-axis che đơn vị, không vẽ missing thành 0. H1 giữ SVG để in rõ. Matplotlib dùng trực tiếp, không thêm notebook/dashboard phân tích. `build` thất bại nếu thiếu file/column/schema; trường hợp dataset chưa đủ thì xuất bảng missing và chỉ sinh hình từ phần hợp lệ, không xuất chart rỗng như kết quả.

Nhân trưởng viết kết luận theo mẫu cố định cho **từng RQ1–RQ5**: điều kiện → run/table/figure → số đo + n/độ bất định → giả thuyết ủng hộ/không ủng hộ/chưa đủ evidence → giới hạn. Nếu CI chứa 0, nói chưa đủ bằng chứng chiều khác biệt; nếu SLO trượt, nêu trượt; nếu không đo được cell thì đánh chưa trả lời được RQ tương ứng. Không chọn sẵn thuật toán thắng và không coi số minh họa trong lý thuyết là dữ liệu.

### Q13. Báo cáo cuối cùng đã chốt nội dung và hình thức

Bản chính viết tiếng Việt, tên đề tài **“Nghiên cứu và đánh giá các kỹ thuật cân bằng tải trong kiến trúc Microservices”**, output `NT533_BaoCao.docx` và `NT533_BaoCao.pdf`. Mục tiêu **30 trang nội dung**, chưa tính bìa/mục lục/tài liệu tham khảo/phụ lục; không kéo dài bằng log/code nguyên trang. Mặc định A4, Times New Roman 13, giãn dòng 1,3, lề trái 3 cm/phải 2 cm/trên dưới 2 cm, heading đánh số, hình/bảng có caption và nguồn, tài liệu tham khảo IEEE số thứ tự. Đây là quy cách nhóm chọn khi chưa có mẫu môn học; yêu cầu chính thức của giảng viên nếu được cung cấp ưu tiên hơn và phải cập nhật cả hai Markdown, không tự tuyên bố đã đúng template UIT.

| Chương / số trang mục tiêu | Nội dung phải viết, không để “sẽ chốt” | Chủ trì |
|---|---|---|
| 1. Giới thiệu — 2 | vấn đề, 5 RQ, H1–H4, scope/out-of-scope, đóng góp và giới hạn 14 ngày | Nhân trưởng |
| 2. Cơ sở lý thuyết/liên quan — 4 | service/replica/state, RR/LC/IPH, consistent key/ring, queue, metric, nghiên cứu liên quan có nguồn | Mạnh Nhân tổng hợp |
| 3. Thiết kế/triển khai — 6 | API/fixture Q02, source Q08, H1, network/trust, version/quota thật, timeout/retry, observability, A1/A2/A4 | Nhân trưởng + Nhật + Nguyên |
| 4. Phương pháp — 6 | biến độc lập/phụ thuộc/kiểm soát, 96+8/60, seed/trace/rate/pilot/SLO, windows/cohort, validity/stats, threats | Nin + Nguyên |
| 5. Kết quả/thảo luận — 8 | H2–H6/T01–T06, từng RQ1–RQ5, contrast/CI, hot-key, failure/recovery, giải thích và giới hạn | Nin xuất số; Mạnh Nhân đối soát; Nhật viết advanced |
| 6. Tái lập/đánh giá hạn chế — 3 | fresh-clone evidence, runbook/backup, missing/invalid, host/client bottleneck, không suy rộng production | Nhật + Nguyên |
| 7. Kết luận — 1 | trả lời gọn đủ 5 RQ bằng evidence, không thắng tuyệt đối; hướng phát triển ngoài scope | Nhân trưởng |

Phụ lục: OpenAPI/contract v1 xuất từ Q02; matrix/schedule/protocol; config/nginx -t; trace/manifest mẫu; test/fault/reproduction logs; link archive/checksum; PCCV và đóng góp có evidence. Trích tài liệu gốc cạnh nhận định rồi gom bibliography; ghi ngày truy cập, phiên bản thực; không bịa bài báo hoặc phát biểu kết quả. Word, PDF và slide lấy cùng thư mục docs/generated. D12 có đủ bảy chương với trạng thái dữ liệu thật; chưa có kết quả thì ghi thiếu, không điền số trông hợp lý.

Review cuối: Mạnh Nhân đối từng số/caption với run_table; Nguyên đối đơn vị/cohort/metrics; Nhật đối config/topology/fault; Nin kiểm chart/CI/reproducibility; Nhân trưởng kiểm RQ/scope/citation/bố cục và xuất PDF. Mở PDF sau xuất, kiểm trang trống/cắt hình/font/caption/link; sửa lỗi hiển thị rồi xuất lại. Đây là nghiệm thu bắt buộc, không chỉ kiểm file tồn tại.

### Q14. Slide, demo, video và bảo vệ đã chốt

Đầu ra `NT533_Slide.pptx` + PDF, **15 slide / 13 phút**, chữ chính ≥24 pt, không dán dashboard/log nhỏ. Thứ tự: (1) tên/nhóm; (2) vấn đề/RQ; (3) H1/scope; (4) API/fixture; (5) service/replica/test; (6) RR/LC/IPH; (7) protocol/matrix/SLO; (8) B1/B2 H2; (9) count/CPU H3; (10) A1/A2 H4; (11) NAT/hot-ID H5; (12) GH-ID/CH-ID H6; (13) paired CI/validity/giới hạn; (14) trả lời đủ 5 RQ; (15) tái lập/bàn giao/hướng sau này. Mỗi hình giữ caption/n/đơn vị/run IDs đọc được; không thêm số chưa có trong báo cáo.

Phân thời gian cố định: Nhân trưởng 2 phút (1–3), Mạnh Nhân 2 phút (4–5), Nhật 3 phút (6–7 và minh họa routing), Nguyên 2 phút (9–10), Nin 3 phút (8,11–14), Nhân trưởng 1 phút chốt (15); chuyển lời theo thứ tự slide, một người có thể trình bày hai đoạn. Q&A ngoài 13 phút. Mọi người chuẩn bị câu trả lời mục 13 của tài liệu lý thuyết và biết đường dẫn raw phần mình, không chỉ thuộc slide.

Demo dùng **lab và fixture đã chọn**, không dùng dịch vụ ngoài: (a) curl quote P001×2 và một lỗi P002×4; (b) xem X-Instance-ID/RR và metric trực tiếp; (c) minh họa NAT/IPH→CH-ID bằng trace demo seed 53501 ở 5 request/s, 20 s/biến thể; (d) trình bày timeline fault và 3→4→3 từ raw/video đã đo để không chờ full benchmark trên sân khấu. Trace demo riêng, không gộp vào 104 run; chỉ dùng ID giả lập. Không đổi matrix hoặc ngưỡng để “demo đẹp”. Live fail/quá 10 s không sẵn sàng → chuyển ngay video/ảnh offline, nói rõ đây là bản quay trước.

D12 Nhật quay `NT533_Demo.mp4`, 1080p/30 fps/H.264, **5 phút**: 30 s kiến trúc; 45 s API/test; 60 s RR/LC/IPH; 60 s NAT/CH-ID; 60 s fault/mapping; 45 s raw/checksum/tái lập. Che key/account/IP quản trị nếu xuất hiện; không chỉnh sửa log/số đo. Nguyên kiểm phát offline video/PDF/dashboard export; D13 tổng duyệt đủ 5 người, ghi thời lượng/lỗi/người sửa; D14 không thêm màn demo mới.

### Q15. Gói nộp, bàn giao và định nghĩa “xong đồ án” đã chốt

```text
release/nt533-v1/
  README_NopBai.md                   # mục lục/link, cách giải nén/verify/build/run, thiếu gì
  NT533_BaoCao.docx
  NT533_BaoCao.pdf
  NT533_Slide.pptx
  NT533_Slide.pdf
  NT533_Demo.mp4
  source/                           # snapshot source tại tag nt533-v1, không .env/key/raw
  docs/                             # hai Markdown + API/runbook/protocol/matrix/version lock
  data/                             # raw archive(s), summaries, charts, run ledger cả invalid
  03_NT533_PCCV.xlsx                 # trạng thái/evidence thật do owner cập nhật lúc bàn giao
  SHA256SUMS
  RELEASE_CHECK.json                 # file tồn tại/hash/link/secret/reproduce/người review
```

Nhân trưởng tạo tag `nt533-v1` **sau** khi G6 đạt; release metadata ghi commit/tag/image IDs/protocol version và timestamp. `analysis/analyze.py release` chỉ đọc source/raw đã khóa, sinh manifest và SHA256SUMS cho mọi file trong gói trừ SHA256SUMS/RELEASE_CHECK (hai file tự mô tả không hash vòng); quét secret và fail nếu thiếu file bắt buộc. Data archive chia part tối đa 1 GiB khi cần; raw đầy đủ nằm trong data hoặc link archive thứ hai do nhóm kiểm quyền tải thật, không để link giả/placeholder. Nếu phải nộp link vì cổng giới hạn dung lượng, README ghi từng part/hash/size và reviewer thử tải bằng tài khoản có quyền trước nộp.

Mạnh Nhân giải nén bản nộp vào thư mục sạch, kiểm checksum, mở PDF/PPTX/video/XLSX, chạy build/test và reproduction; lưu command/stdout/stderr/exit cùng RELEASE_CHECK. Nguyên đối metrics/fixtures, Nhật đối backup/đóng lab, Nin đối đủ/thiếu dataset và chart; Nhân trưởng xác nhận chỉ sau các reviewer. Không coi file ZIP giải nén được là tái lập thành công. Báo cáo/source/data phải cùng version; sửa code sau tag thì tag/release mới, không âm thầm thay nội dung cũ dưới cùng checksum.

Nhân trưởng nộp trên kênh chính thức do giảng viên cung cấp (slot `SUBMISSION_CHANNEL`), ghi biên nhận/URL/time trong `docs/evidence/submission.md`; người khác kiểm mở được. Không tự bịa deadline, quyền truy cập, URL LMS hoặc trạng thái “đã nộp”. Giữ hai bản sao đã verify ít nhất đến khi nhận điểm/phản hồi cuối; sau backup mới `run.py close`, dừng đúng stack nt533 và đóng rule/ingress lab đã mở. Bàn giao ownership source/config/analyzer/evidence theo PCCV; đóng góp thực tế dùng commit/PR/run/review, không tự chia đều phần trăm.

**Definition of Done end-to-end:** (1) đủ ba service/9 replica và test contract; (2) RR/LC/IPH, CH-ID/GH-ID và safety/reset có evidence; (3) protocol/pilot/version/seed/trace khóa thật; (4) run ledger đầy đủ/thiếu công khai, raw/summary/chart/checksum tái tạo được; (5) trả lời từng RQ đúng dữ liệu, không suy diễn; (6) báo cáo/slide/video mở đúng; (7) fresh-clone do reviewer; (8) PCCV/evidence trung thực; (9) gói nộp và biên nhận xác nhận; (10) backup kiểm được và đóng lab an toàn. Thiếu một mục thì chưa gọi hoàn tất, ghi đúng mục còn thiếu.

**Chuỗi quyết định cuối cùng:** chuẩn bị máy/repo → code ba service → contract/test → Compose/NGINX → metric/trace → advanced/fault/reset → smoke G2 → pilot/preflight G3 → 104 run + 60 sweep → audit/backup → bảng/hình/RQ → báo cáo/slide/video → fresh-clone → release/nộp/biên nhận → đóng lab/bàn giao. Q01–Q15 chốt toàn bộ lựa chọn triển khai và đầu ra từ số 0; dữ kiện cần đo hoặc xác nhận bên ngoài vẫn phải thu evidence thật, không thể thay bằng một tuyên bố trong Markdown.

<!-- END NT533-v1 DECISIONS -->

## 1. Hệ phân tán và vấn đề cần giải quyết

Hệ phân tán gồm các thành phần chạy trong những tiến trình/nút riêng, trao đổi qua mạng để thực hiện chức năng chung. Một lời gọi qua mạng khác lời gọi hàm cục bộ: có độ trễ, có thể timeout, mất kết nối hoặc một phía lỗi trong khi phía còn lại vẫn chạy. Vì vậy, thiết kế phải quan tâm đến lỗi từng phần, giới hạn tài nguyên và khả năng quan sát.

Trong đồ án, ba dịch vụ và các replica là những tiến trình độc lập. Chạy chúng trong nhiều container trên cùng máy giúp kiểm tra giao tiếp và điều phối, nhưng chưa chứng minh chịu được lỗi máy chủ: mất host có thể làm cả cụm dừng. Báo cáo phải phân biệt **phân tán ở mức tiến trình** với **phân tán qua nhiều máy/failure domain**.

Các khái niệm cần phân biệt:

| Khái niệm | Ý nghĩa trong đồ án |
|---|---|
| Concurrency | Nhiều request cùng đang được xử lý/chờ; không nhất thiết chạy CPU đồng thời |
| Parallelism | Nhiều phép tính thực sự chạy đồng thời trên tài nguyên thực thi |
| Scalability | Khả năng tăng tải phục vụ khi tăng tài nguyên, với chất lượng được xác định |
| Availability | Khả năng phục vụ thành công trong phạm vi và cửa sổ quan sát |
| Fault tolerance | Tiếp tục cung cấp chức năng khi một phần hệ thống lỗi |
| Elasticity | Tự điều chỉnh tài nguyên theo nhu cầu; khác với chỉ cấu hình nhiều replica |
| Bottleneck | Thành phần giới hạn throughput hoặc làm hàng chờ tăng mạnh |

Không suy từ “có nhiều container” thành “hệ thống high availability”. Một NGINX duy nhất vẫn là single point of failure. Đồ án core đo lỗi backend, chưa đo lỗi load balancer hay network partition toàn hệ thống.

## 2. Microservices, replica và quản lý trạng thái

### 2.1. Ranh giới dịch vụ

Microservices chia ứng dụng theo trách nhiệm nghiệp vụ, mỗi dịch vụ có thể build/deploy riêng và giao tiếp qua hợp đồng API. Ba controller trong cùng một JVM không tự tạo thành ba microservice. Trong thiết kế đã chốt (Q01–Q02): Catalog quản lý thông tin sản phẩm, Inventory cung cấp tồn kho, Order lập báo giá bằng cách gọi hai dịch vụ còn lại.

Một **service** là vai trò logic; một **instance/replica** là một bản chạy của service. Ba dịch vụ, mỗi dịch vụ ba replica, tạo ra chín backend. NGINX chọn upstream theo route trước, sau đó mới chọn replica trong upstream. Không gửi request Catalog sang Order chỉ vì Order rảnh.

Ưu điểm kỳ vọng: triển khai/scale theo từng dịch vụ, cô lập một số lỗi, phân chia ownership. Chi phí đi kèm: thêm lời gọi mạng, phiên bản API, quan sát xuyên dịch vụ, timeout và vận hành nhiều tiến trình. Với đồ án nhỏ, đây là đánh đổi cần trình bày, không phải khẳng định microservices luôn tốt hơn monolith.

### 2.2. Stateless và stateful

Stateless ở tầng xử lý request nghĩa là request tiếp theo không buộc phải quay về đúng instance trước đó để hiểu phiên làm việc. Nó không có nghĩa toàn hệ thống không có dữ liệu. Replica có thể dùng dữ liệu bền vững dùng chung theo ranh giới service, hoặc token/session store phù hợp.

Nếu giỏ hàng chỉ nằm trong RAM của C1, chuyển request sang C2 có thể mất trạng thái. IP affinity chỉ giảm khả năng đổi instance, không bảo vệ dữ liệu khi C1 chết. Trong core, fixture chỉ đọc và báo giá không có side effect giúp tránh lẫn vấn đề state vào thí nghiệm scheduler. Nếu thêm đặt hàng thật, cần persistence, idempotency và kiểm soát cập nhật tồn kho; không thể chỉ nhân container chứa database in-memory rồi coi dữ liệu nhất quán.

### 2.3. Lỗi dây chuyền

Order chờ Inventory; Inventory chậm làm thread/request ở Order tồn tại lâu hơn. Khi hàng chờ dâng cao, thêm request mới có thể khiến cả chuỗi xấu đi. Timeout có ngân sách, giới hạn concurrency và retry có giới hạn là những biện pháp khác nhau. Circuit breaker là hướng mở rộng, không được bật riêng cho một thuật toán trong benchmark chính.

Với lời gọi nối tiếp, latency end-to-end gần tổng các giai đoạn cộng mạng/xếp hàng. Với gọi song song, thời gian thường bị chi phối bởi nhánh chậm nhất cộng overhead. Đây là mô hình giải thích, phải kiểm chứng bằng log/timing vì các hàng chờ và tài nguyên có thể tương tác.

## 3. Container, tài nguyên và quan sát

Container đóng gói ứng dụng và môi trường chạy, không tạo thêm CPU/RAM vật lý. Chín replica cùng tranh bốn lõi CPU không có năng lực tương đương chín máy độc lập. CPU quota gây throttling; giới hạn RAM có thể dẫn đến OOM. Heap JVM chỉ là một phần bộ nhớ: còn thread stack, metaspace, native buffer và phần ngoài heap khác.

Readiness trả lời “có thể nhận traffic chưa”; liveness trả lời “có cần khởi động lại tiến trình không”; startup bảo vệ giai đoạn khởi động. Không dùng một probe lỗi dependency ngắn hạn để vô tình restart toàn bộ dịch vụ. Với Compose, cần healthcheck phù hợp để chờ ứng dụng thật sự sẵn sàng, không chỉ container đã chạy. [Docker startup order](https://docs.docker.com/compose/how-tos/startup-order/).

Actuator và Micrometer hỗ trợ xuất metric ứng dụng; cần registry tương ứng và cấu hình endpoint. [Spring Boot Metrics](https://docs.spring.io/spring-boot/reference/actuator/metrics.html). Với đồ án, nên quan sát request count/duration từng instance, JVM memory/GC, CPU và thread pool. Metric labels chỉ dùng tập giá trị hữu hạn như service/instance/route/status/profile; request ID và user ID thuộc log/trace, không đưa vào label vì cardinality tăng không kiểm soát.

Scrape qua load balancer có thể mỗi lần lấy số liệu từ một replica khác nhau. Vì vậy phải scrape trực tiếp từng instance và giữ nhãn instance ổn định trong từng run. Monitoring cũng tốn tài nguyên, nên giữ cùng chế độ thu thập cho mọi thuật toán.

## 4. Load balancer và mô hình NGINX

Load balancer nhận traffic và chọn backend. Reverse proxy đại diện backend trước client; ngoài chọn server, nó có thể xử lý routing, timeout và logging. Load balancing không đồng nghĩa autoscaling: một bên phân phối công việc, bên kia thay đổi số tài nguyên xử lý.

L4 chọn theo thông tin kết nối ở tầng vận chuyển; L7 hiểu giao thức ứng dụng như HTTP và có thể route theo URL. Đồ án dùng HTTP reverse proxy, nên cần phân biệt request, client connection và upstream connection. Keepalive tái sử dụng kết nối; một connection không nhất thiết tương ứng đúng một request trong toàn bộ vòng đời.

NGINX hỗ trợ RR, LC và IPH; RR là cơ chế mặc định khi không chọn phương pháp khác. [NGINX HTTP load balancing](https://nginx.org/en/docs/http/load_balancing.html).

### 4.1. Round Robin

Mô hình đơn giản: lần lượt chọn A, B, C, A, B, C. Khi trọng số bằng nhau, backend sẵn sàng và nhiều request tương tự nhau, kỳ vọng số request tương đối đều. Không yêu cầu đọc CPU của backend.

**Ví dụ tư duy:** sáu request đều cần một đơn vị công việc có thể chia 2–2–2. Nếu hai request đến A đều nặng gấp mười, số request vẫn đều nhưng công việc không đều. Đây là lý do không đánh giá bằng count đơn thuần.

Weighted RR cho phép tỷ lệ mong muốn khác nhau khi năng lực khác nhau; core giữ trọng số bằng nhau để tránh thêm biến. Nếu bổ sung trọng số, phải đo năng lực trước và trình bày đó là thí nghiệm riêng.

### 4.2. Least Connections

LC chọn backend có ít kết nối đang hoạt động hơn, có xét trọng số. Nó không trực tiếp chọn server có CPU thấp nhất hoặc response time thấp nhất. [NGINX HTTP load balancing](https://nginx.org/en/docs/http/load_balancing.html).

**Mô hình giải thích:** A có 8 request kéo dài, B có 2 và C có 1; nếu các request đó tương ứng các kết nối bận đang được theo dõi, C là ứng viên hợp lý. Backend chậm giữ công việc lâu hơn nên có thể nhận ít request mới. Tuy nhiên sự tương ứng giữa connection và workload thay đổi theo giao thức, pooling và multiplexing; LC không phải bộ đo “công việc còn lại”.

Nếu chỉ gửi request tuần tự, nhiều lúc cả ba backend đều rảnh trước request mới. Khi đó thí nghiệm khó thể hiện khác biệt của LC. Cần concurrency đủ lớn và profile có thời gian xử lý biến thiên; không tự tăng delay chỉ để làm LC thắng mà không công khai thiết kế.

### 4.3. IP Hash

IPH ánh xạ khóa địa chỉ nguồn về backend để duy trì affinity. Với NGINX, IPv4 dùng ba octet đầu, IPv6 dùng toàn địa chỉ; cùng khóa thường giữ backend khi membership/khả dụng không đổi. [NGINX upstream — ip_hash](https://nginx.org/en/docs/http/ngx_http_upstream_module.html#ip_hash).

Mô hình `backend = H(key) mod N` chỉ để hiểu ý tưởng, **không phải** mô tả chính xác triển khai NGINX. IPH cũng không đồng nhất với generic consistent hashing. Hash đều theo khóa chưa chắc đều theo request: một khóa có thể tạo phần lớn traffic.

**Ví dụ tư duy:** 100 client đều truy cập nhưng 80 client đi qua cùng NAT; từ phía NGINX chúng có thể tập trung thành một khóa. Tăng số VU trên một máy không giải quyết được điều này. Ngay cả IP khác nhau trong một `/24` cũng chưa tạo ra nhiều khóa IPv4 hữu ích.

Khi dùng real-IP header trong lab, chỉ proxy/nguồn test tin cậy được phép sửa địa chỉ hiệu lực. Header client tự gửi không phải bằng chứng về IP thật. Module real-IP cần cấu hình vùng tin cậy và header rõ ràng. [NGINX real-IP](https://nginx.org/en/docs/http/ngx_http_realip_module.html).

### 4.4. So sánh bằng lập luận, chưa phải kết quả

| Thuật toán | Tín hiệu lựa chọn | Điều kiện đáng khảo sát | Hạn chế cần kiểm chứng |
|---|---|---|---|
| RR | Lượt phân phối/trọng số | Backend đồng nhất, chi phí request gần nhau | Count đều nhưng công việc không đều |
| LC | Kết nối bận quan sát được | Request kéo dài, backend chậm, concurrency cao | Connection là proxy không hoàn hảo cho tải |
| IPH | Khóa địa chỉ nguồn | Cần affinity, nhiều khóa có traffic cân đối | NAT/prefix/skew làm tập trung traffic |

Đây là khung hình thành giả thuyết của nhóm. Không có quy tắc “LC luôn nhanh nhất” hay “IPH luôn tệ nhất”. Kết luận phụ thuộc workload, mức tải, key distribution, trạng thái backend và cấu hình proxy.

## 5. Cấu hình minh họa và các yếu tố dễ gây nhiễu

Ví dụ dưới đây giả định các backend đã tồn tại trong mạng lab. Giữ `zone` để chia sẻ trạng thái upstream giữa worker; khóa phiên bản trước khi dùng. [NGINX upstream — zone](https://nginx.org/en/docs/http/ngx_http_upstream_module.html#zone).

```nginx
upstream catalog_backend {
    zone catalog_backend 64k;

    # RR: không thêm directive thuật toán.
    # LC: thêm least_conn;
    # IPH: thêm ip_hash;
    # Chỉ chọn một biến thể trong mỗi run.

    server catalog-1:8080 max_fails=1 fail_timeout=5s;
    server catalog-2:8080 max_fails=1 fail_timeout=5s;
    server catalog-3:8080 max_fails=1 fail_timeout=5s;
    keepalive 32;
}

server {
    listen 80;
    location /api/catalog/ {
        proxy_pass http://catalog_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header X-Request-ID $request_id;
        proxy_connect_timeout 200ms;
        proxy_read_timeout 3s;
        proxy_next_upstream off;
        proxy_buffering off;
    }
}
```

Đây là đoạn trong ngữ cảnh `http`, không phải toàn bộ `nginx.conf`. Thêm upstream/location cho Inventory và Order theo cùng quy ước. Dạng `proxy_pass` ở trên không có URI thay thế nên giữ route; phải khớp route Spring. `proxy_read_timeout` là timeout giữa các lần đọc liên tiếp, không phải deadline tổng request. Core đặt retry off để quan sát lỗi trực tiếp; bật retry là phép đo riêng. [NGINX proxy module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html).

Các điều kiện phải ghi vào báo cáo:

- **Worker/shared state:** giữ cùng số worker, cấu hình zone và tài nguyên NGINX.
- **Keepalive/protocol:** đặt rõ, không lệ thuộc default thay đổi theo version; không dùng HTTP/2 cho một thuật toán nhưng HTTP/1.1 cho thuật toán khác.
- **Health handling:** kiểm tra lỗi thụ động dựa vào traffic khác với chủ động gửi probe. Không mặc định mọi directive health-check có trong image/edition đang dùng; xác minh tài liệu phiên bản và `nginx -t`. [NGINX load balancing](https://nginx.org/en/docs/http/load_balancing.html).
- **Retry:** có thể làm client thành công sau một lỗi backend, đồng thời tăng attempts. Không tự retry thao tác ghi không idempotent; một timeout không đảm bảo backend chưa thực hiện thao tác.
- **DNS/membership:** container mới có thể đổi IP; ghi upstream thực sự được NGINX sử dụng, không chỉ tên trong file.
- **Cache/buffering/log:** giữ như nhau; tắt cache trong core nếu muốn mỗi request đến backend. Log đồng bộ quá nặng có thể trở thành bottleneck.
- **Nguồn IP:** log effective IP, peer khi dùng real-IP, upstream address, status, request time, upstream time và request ID. Khi có retry, trường upstream có thể chứa nhiều attempt; parser không được coi đó là một backend duy nhất.

## 6. Lý thuyết hàng đợi và quá tải

Ký hiệu: `λ` là tốc độ đến (request/s), `μ` là năng lực phục vụ lý tưởng của một server, `L` là số request trung bình trong hệ thống, `W` là thời gian lưu trung bình (giây).

### 6.1. Little's Law

Trong trạng thái ổn định, với ranh giới đo và quần thể request nhất quán:

```text
L = λ × W
```

Ví dụ minh họa: throughput 200 request/s và thời gian lưu trung bình 0,1 s tương ứng trung bình khoảng 20 request đang ở trong hệ thống. Không đồng nhất con số này với số TCP connection hay số VU nếu còn think time, pooling hoặc thời gian ở ngoài ranh giới đo.

Khi hàng chờ đang tăng không ngừng hoặc còn nhiều request chưa hoàn tất, không áp công thức trên một cửa sổ ngắn rồi kết luận hệ thống ổn định.

### 6.2. Mô hình đơn giản để hiểu tail latency

Với mô hình M/M/1 lý tưởng: đến Poisson, service time mũ, một server, hàng chờ vô hạn, ổn định khi `λ < μ`:

```text
ρ = λ / μ
W = 1 / (μ - λ)
```

Ví dụ giả định `μ = 100 request/s`: tại `λ = 50`, W = 20 ms; tại `λ = 90`, W = 100 ms. Đây là minh họa toán học cho việc latency tăng phi tuyến gần bão hòa, không phải dự báo cho JVM/NGINX thật. Hệ thống thực tế có nhiều thread, quota, GC, timeout và phân bố request khác giả định này.

Do đó, phải đo ở tải thấp, vừa và gần/vượt bão hòa. Chỉ đo ở tải rất thấp dễ thấy mọi thuật toán tương tự; chỉ đo quá tải có thể che mất hoạt động ổn định. Tham khảo nền tảng hàng đợi trong [MIT OCW — M/M/1 Queue](https://ocw.mit.edu/courses/2-854-introduction-to-manufacturing-systems-fall-2016/927056a1af54772a587fd84ad4951e71_MIT2_854F16_Mm1Queue.pdf).

## 7. Chỉ số đánh giá và cách tính

### 7.1. Throughput, offered load và lỗi

```text
Offered rate      = số request dự kiến phát / thời gian
Sent rate         = số request thực sự phát / thời gian
Success throughput = số request hoàn tất đạt điều kiện thành công / thời gian
Error rate        = số request đã kết thúc bị lỗi / số request đã kết thúc
```

Định nghĩa “thành công” gồm HTTP status mong đợi và kiểm tra body nghiệp vụ. HTTP 200 với dữ liệu sai không phải thành công. Phân loại network error, timeout, HTTP 4xx/5xx và business check failure; nếu một request thuộc nhiều cờ lỗi, tổng error rate vẫn chỉ đếm request đó một lần.

Phải báo request chưa hoàn tất ở cuối run và iteration không khởi chạy, không biến chúng thành response thành công. Throughput lỗi cao không phải năng lực phục vụ hữu ích.

### 7.2. Response time và percentile

```text
Mean = (Σ latency_i) / N
p95  = ngưỡng mà khoảng 95% mẫu có latency không vượt quá
p99  = ngưỡng mà khoảng 99% mẫu có latency không vượt quá
```

Thuật toán nội suy percentile phải được ghi theo công cụ sử dụng. Mean cho chi phí trung bình; p95/p99 phản ánh phần đuôi. Một hệ thống có mean thấp nhưng 1% request rất chậm vẫn có trải nghiệm xấu cho nhóm người dùng đó.

Trong k6, `http_req_duration` gồm sending + waiting + receiving, không gồm DNS/kết nối ban đầu. TTFB không phải tổng thời gian nhận response. Khi báo cáo cần phân biệt latency client, latency NGINX và service time tại ứng dụng. [k6 built-in metrics](https://grafana.com/docs/k6/latest/using-k6/metrics/reference/).

Không lấy trung bình p95 của các instance để tạo p95 hệ thống. Muốn percentile tổng hợp phải gộp mẫu hợp lệ hoặc histogram phù hợp. Histogram bucket làm percentile xấp xỉ; summaries không thể tùy tiện gộp quantile qua replica. [Prometheus histograms and summaries](https://prometheus.io/docs/practices/histograms/).

### 7.3. Độ đều phân phối

Gọi `x_i` là request count của instance i trong cùng upstream/cửa sổ, `n` là số instance được xét:

```text
mean_x = (Σ x_i) / n
σ      = sqrt(Σ(x_i - mean_x)^2 / n)
CV     = σ / mean_x
Jain J = (Σ x_i)^2 / (n × Σ x_i^2)
```

CV thấp nghĩa là count ít phân tán. Với tải không âm và tổng tải dương, Jain nằm trong `[1/n, 1]`; 1 là count đều. Ví dụ toán học: `[100,100,100]` cho J = 1; `[300,0,0]` cho J = 1/3. Nếu mọi count bằng 0, cả CV và J ghi `N/A`, không chia cho 0. Phải đưa instance có count 0 vào vector, không chỉ lấy instance xuất hiện trong log. Công thức Jain xuất phát từ [báo cáo DEC của Jain, Chiu và Hawe](https://www.cse.wustl.edu/~jain/papers/fairness.htm).

Với server khác năng lực, count đều chưa chắc tối ưu. Có thể xem thêm count/capacity đã hiệu chuẩn, nhưng phải ghi rõ đó là metric chuẩn hóa khác. Trong A2, báo cả vector trên membership ban đầu và vector chỉ backend khả dụng nếu cần; không loại backend chết âm thầm để chỉ số trông đẹp hơn.

### 7.4. Tài nguyên, phục hồi và hiệu quả mở rộng

- CPU phải ghi chuẩn hiển thị: phần trăm một core hay toàn host, quota và throttling; RAM phải phân biệt container memory và heap.
- GC, thread pool và queue giúp giải thích latency; chúng không tự chứng minh quan hệ nhân quả nếu có biến khác thay đổi.
- Thời gian phục hồi phải có mốc bắt đầu và điều kiện “đã phục hồi” định lượng, không chọn bằng mắt khi đồ thị vừa đẹp.
- Nếu dùng `speedup = capacity_3 / capacity_1`, capacity phải là tải tối đa vẫn đạt cùng SLO, cùng phương pháp tìm; tỷ số throughput ở một mức offered load thấp không chứng minh tốc độ tối đa tăng.
- Hiệu quả tài nguyên có thể đo success request/s trên CPU cấp phát hoặc chi phí, nhưng phải công bố mẫu số và phạm vi chi phí.

## 8. Load testing đúng phương pháp

### 8.1. Open model và closed model

Closed model cố định nhóm người dùng, mỗi người thường chờ thao tác trước kết thúc rồi mới tiếp tục. Khi server chậm, rate có thể tự giảm. Open model khởi tạo công việc theo lịch arrival độc lập hơn với việc công việc trước hoàn tất. Chọn open model cho so sánh cùng offered rate; closed model vẫn hữu ích cho mô phỏng một quần thể người dùng cụ thể. [k6 open/closed models](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/).

Open model không bảo đảm client luôn tạo đủ tải: thiếu VU/CPU/network vẫn gây thiếu request. Vì thế ghi actual rate và dropped iterations. Trong benchmark trực tiếp, quy ước một iteration một HTTP request giúp diễn giải đơn giản. Trong workflow nhiều request, iteration/s không bằng request/s.

### 8.2. Các loại kiểm thử

| Loại | Câu hỏi | Cách dùng trong đề tài |
|---|---|---|
| Smoke | Route/body/metric hoạt động chưa? | Trước mọi nhóm run |
| Load | Ở mức tải dự kiến có đạt SLO? | Low/medium chung cho các thuật toán |
| Stress | Điểm quá tải và kiểu thất bại là gì? | Tải high và pilot saturation |
| Spike | Tăng tải đột ngột có gây bất ổn? | Ngoài ma trận v1; chỉ là khái niệm/hướng sau này |
| Soak | Chạy lâu có rò rỉ/tích tụ queue? | Ngoài ma trận v1; điều tra riêng nếu có evidence memory leak |
| Fault injection | Hỏng một thành phần ảnh hưởng gì? | Stop/start và slow-backend có timeline |

### 8.3. Warm-up, lặp và randomization

JVM cần thời gian nạp lớp/JIT; cache và connection pool cũng thay đổi trong khởi động. Warm-up phải được loại khỏi dữ liệu steady-state theo cùng quy tắc. Không tùy ý bỏ một đoạn đầu chỉ vì latency xấu sau khi nhìn kết quả.

Một run dài không thay thế nhiều run độc lập. Dùng seed cố định theo block, đổi thứ tự thuật toán để giảm ảnh hưởng thời điểm chạy, nhiệt độ máy hoặc tác vụ nền. Nếu mọi RR chạy ngày đầu, LC ngày sau và IPH ngày cuối, tác động ngày có thể bị nhầm thành tác động thuật toán.

## 9. Thống kê, ngưỡng quyết định và cách viết kết luận

### 9.1. Đơn vị phân tích

Request trong cùng run dùng chung queue, JVM và điều kiện mạng nên thường tương quan. Lấy run làm đơn vị chính: tính metric mỗi run, sau đó xem phân bố giữa các run. Khi có cùng seed/block cho hai thuật toán, so sánh chênh lệch trong block để giảm nhiễu môi trường.

```text
Cải thiện latency (%) = (p95_baseline - p95_candidate) / p95_baseline × 100
Tăng throughput (%)   = (X_candidate - X_baseline) / X_baseline × 100
```

Baseline phải dương; nếu không, ghi N/A và giải thích. Không so phần trăm từ các run có workload hoặc offered rate khác nhau rồi gọi là lợi ích thuật toán.

### 9.2. Confidence interval và effect size

CI 95% mô tả độ bất định của ước lượng theo phương pháp lấy mẫu, không có nghĩa 95% request nằm trong khoảng đó. Có thể bootstrap theo run hoặc paired block, lưu seed và cách tạo CI. Mỗi cell chính có n=3: trình bày từng run, median/min–max và kết luận thăm dò. Hai contrast định trước có n=5 để dùng paired bootstrap; CI vẫn chưa đảm bảo ổn định với small-n.

P-value, nếu dùng, không phải độ lớn lợi ích và không chứng minh giả thuyết chắc chắn đúng. Nhiều phép so sánh làm tăng rủi ro kết luận tình cờ; ưu tiên ít câu hỏi đã đăng ký trước, hoặc điều chỉnh multiple comparisons khi kiểm định hàng loạt. Không dùng “CI riêng không chồng lấp” như quy tắc duy nhất: quan tâm CI của **chênh lệch**.

### 9.3. Quy tắc kết luận đã chốt (Q05)

1. Xác nhận run hợp lệ và cùng điều kiện; kiểm tra client đã tạo đủ tải.
2. Xét SLO và lỗi trước, tránh chọn thuật toán trả lỗi nhanh.
3. Xét successful throughput, p95 và hiệu ứng thực tiễn đã chốt trước (≥10% theo Q05).
4. Xem biến thiên/CI, count fairness và tài nguyên để giải thích.
5. Kết luận theo scenario, không chọn một “quán quân tuyệt đối”.

Mẫu diễn đạt chưa điền số: “Trong workload … ở offered rate … với … replica và phân bố IP …, LC có p95 thấp hơn RR …%; CI chênh lệch …; error rate …; chưa đủ cơ sở suy rộng sang workload khác.” Nếu dữ liệu không tách biệt, nói rõ chưa quan sát khác biệt đủ mạnh.

## 10. Nội dung nâng cao và giới hạn tính hợp lệ

### 10.1. Slow backend và fault injection

Slow backend không đồng nghĩa backend down. Một instance vẫn nhận request nhưng xử lý lâu có thể tạo tail latency lớn; dừng hẳn instance có thể được cơ chế lỗi phát hiện theo cách khác. Đo cả hai để tránh đánh đồng resilience với latency balancing.

Trong fault test, giữ nguyên lịch tải, đánh dấu thời điểm stop/start/ready, quan sát lỗi và request chuyển backend. Retry có thể che lỗi khỏi client nên cần đếm cả attempts. Case retry off và retry on trả lời hai câu hỏi khác nhau; không gộp chúng vào một so sánh scheduler.

### 10.2. IP distribution là biến nghiên cứu

Đối chứng ba phân bố: nhiều khóa traffic đều, một khóa, nhiều khóa nhưng hot key chiếm 80%. Điều này tách ảnh hưởng thuật toán khỏi ảnh hưởng đầu vào. Nếu dùng IP giả lập qua trusted header, phải gọi đúng là mô phỏng phân bố khóa; không suy kết quả thành đánh giá chất lượng mạng thật hoặc tập người dùng Internet.

### 10.3. Kubernetes và autoscaling

Kubernetes Service cung cấp điểm truy cập tới tập Pod; cơ chế forwarding phía sau phụ thuộc triển khai. NGINX chỉ nhìn thấy một Service VIP có thể không trực tiếp quyết định Pod nhận request. [Kubernetes Service](https://kubernetes.io/docs/concepts/services-networking/service/). Đây là rủi ro “hai tầng phân phối”, cần quan sát endpoint thực và xử lý discovery trước khi chuyển benchmark.

HPA điều chỉnh số replica dựa trên metric; cần cấu hình metric, requests và giới hạn phù hợp. [Kubernetes HPA](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/). Nếu để HPA chạy trong phép đo RR/LC/IPH, thuật toán có thể được so trong các trạng thái replica khác nhau. Vì vậy tắt autoscaling ở benchmark thuật toán; đánh giá scaling bằng protocol riêng có timeline.

### 10.4. Threats to validity

| Loại | Nguy cơ trong đồ án | Cách giảm |
|---|---|---|
| Construct validity | Dùng count thay CPU load; mean thay trải nghiệm đuôi; sleep thay I/O thật | Định nghĩa metric, nhiều góc quan sát, ghi rõ synthetic workload |
| Internal validity | JVM warm-up, retry, quota, IP hoặc config thay đổi cùng thuật toán | Khóa cấu hình, seed/block, preflight, manifest |
| External validity | Một host, một LAN, fixture nhỏ không đại diện production | Giới hạn kết luận, có end-to-end case, tùy chọn lặp môi trường khác |
| Conclusion validity | Ít run, cherry-picking, nhiều kiểm định, percentile ít mẫu | Công bố toàn bộ run/lý do loại, CI/effect size, tăng lặp khi cần |

Không cần triển khai mọi kỹ thuật phân tán để có đồ án tốt; cần kiểm soát được thứ mình đo và giải thích đúng phạm vi kết quả.

## 11. Advanced: Client-ID Consistent Hash và phép thử có đối chứng

### 11.1. Tách quyết định chọn khóa và chọn cách ánh xạ

Một cơ chế affinity có hai thành phần: **key extraction** chọn cái gì đại diện cho client; **mapping** ánh xạ khóa ấy vào tập backend. CH-ID dùng định danh giả lập ổn định rồi consistent hashing. Đổi từ IP sang ID và đổi hàm ánh xạ không phải cùng một tác động.

| Biến thể | Khóa | Mục đích |
|---|---|---|
| RR / LC | Không cố định theo client-ID | Đối chứng chất lượng phục vụ, không yêu cầu affinity |
| IPH | Khóa IP NGINX nhìn thấy | Phương án bắt buộc và đối chứng NAT |
| GH-ID | `X-Lab-Client-ID` | Generic Hash cùng khóa, đối chứng riêng cho A4 |
| CH-ID | Cùng `X-Lab-Client-ID` | Consistent Hash, đo affinity và remapping |

NGINX có `hash key` và tùy chọn `consistent`; tài liệu mô tả consistent variant sử dụng ketama nhằm giảm số khóa ánh xạ lại khi membership đổi. [NGINX hash](https://nginx.org/en/docs/http/ngx_http_upstream_module.html#hash). Đồ án sử dụng kỹ thuật này, không phát triển thuật toán mới.

**A3 trả lời câu hỏi ứng dụng:** cùng IP nhưng nhiều định danh, thay khóa có giúp chia tải? **A4 trả lời câu hỏi cơ chế:** giữ cùng ID, chỉ bật/tắt `consistent`, mapping đổi thế nào? Không lấy A3 để chứng minh riêng lợi ích của consistent ring.

### 11.2. Trực giác consistent hashing

Trong mô hình minh họa, hash key và các điểm đại diện backend lên một vòng; mỗi key được gán theo quy tắc chọn điểm tiếp theo. Thêm backend tác động một phần vùng khóa thay vì thay toàn bộ phép chia theo số server. Nhiều điểm đại diện cho một backend giảm phụ thuộc vào vài vị trí. Đây là trực giác giảng giải, không mô tả từng dòng triển khai NGINX hay cam kết công bằng tuyệt đối.

Trong mô hình lý tưởng cân đối, thêm server thứ tư có thể làm khoảng 1/4 khóa chuyển sang server mới. **Không dùng 25% làm assertion cho NGINX**: tập khóa hữu hạn, trọng số, server identity và failure state ảnh hưởng quan sát. Đo mapping thật và so GH-ID cùng khóa, không ép kết quả theo hình vẽ ring.

Giảm remapping có thể hữu ích cho locality/cache/session affinity; nhưng đồ án không triển khai cache/session store thật. Kết quả chỉ chứng minh độ ổn định routing, không chứng minh cache-hit tăng hoặc session không mất.

### 11.3. Cấu hình lab và ranh giới của khóa

Đặt đoạn sau trong ngữ cảnh `http`, cạnh config proxy chung. Bổ sung Real-IP/firewall đúng peer LOADGEN và network đã chốt tại Q03–Q04; đây không phải nginx.conf hoàn chỉnh. A3 dùng cùng validation cho RR/LC/IPH/GH-ID/CH-ID để không tạo overhead khác nhau. Header chỉ có ở mạng benchmark tin cậy, không phải xác thực người dùng.

```nginx
map $http_x_request_id $lab_request_valid {
    default 0;
    "~^[0-9a-f]{32}$" 1;
}

map $http_x_lab_client_id $lab_client_valid {
    default 0;
    "~^c-[0-9a-f]{16}$" 1;
}

upstream inventory_lab {
    zone inventory_lab 64k;
    hash $http_x_lab_client_id consistent;
    # A4 GH-ID: bỏ riêng consistent, giữ nguyên key/server/weight.
    server inventory-1:8080 max_fails=1 fail_timeout=5s;
    server inventory-2:8080 max_fails=1 fail_timeout=5s;
    server inventory-3:8080 max_fails=1 fail_timeout=5s;
    keepalive 32;
}

server {
    listen 8081;  # Chỉ publish vào mạng lab, firewall giới hạn LOADGEN.
    location = /bench/inventory {
        if ($lab_client_valid = 0) { return 400; }
        if ($lab_request_valid = 0) { return 400; }
        proxy_pass http://inventory_lab/internal/bench;
        proxy_set_header X-Request-ID $http_x_request_id;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_connect_timeout 200ms;
        proxy_read_timeout 3s;
        proxy_next_upstream off;
        proxy_buffering off;
    }
}
```

`map` tạo cờ hợp lệ từ header; regex được quote vì có ngoặc nhọn. [NGINX map](https://nginx.org/en/docs/http/ngx_http_map_module.html). `if` chỉ dùng `return`, không xử lý rewrite phức tạp. Ứng dụng phải kiểm tra profile trong allowlist. `proxy_pass` thay route thành `/internal/bench`, giữ query thông thường. Cấu hình mẫu cần `nginx -t` và smoke-test route/body trên phiên bản nhóm đã khóa; chưa được chạy tại đây.

**Thiếu ID:** lab reject thay vì fallback để đầu vào nhất quán. Nếu sản phẩm thật fallback về IP, phải đo tỷ lệ fallback và chấp nhận đổi thuộc tính routing. Hash chuỗi rỗng cho mọi request làm nhiều request thành một khóa; đó là lỗi input, không phải benchmark đáng tin.

**Trust boundary:** người gửi có thể chọn/đổi header để thay đường đi. Hash không xác thực, không phân quyền, không ngăn abuse. Production cần gateway xác thực và ghi đè key; lab chỉ dùng ID tổng hợp, không dùng dữ liệu cá nhân/MSSV làm key. Endpoint lab phải giới hạn mạng nguồn và tắt ngoài môi trường nghiên cứu.

### 11.4. NAT, hot-IP và hot-client

- **NAT:** nhiều client-ID cùng IP; CH-ID có cơ hội tách thành nhiều khóa.
- **Hot-IP:** một IP/prefix chiếm nhiều traffic, có thể chứa nhiều client; IPH tập trung traffic theo khóa đó.
- **Hot-client:** một ID tạo 80% request; CH-ID giữ affinity nên backend của ID ấy vẫn có thể quá tải. Nó không tự chia một hot key.

Ví dụ tư duy: 1.000 ID cùng một IP, mỗi ID 10 request, tạo 10.000 request. IPH chỉ nhìn một khóa thì số ID lớn không giúp nó. CH-ID có nhiều khóa nhưng không bảo đảm đúng 1/3 traffic mỗi server. Nếu một ID tạo 8.000 request, affinity lại là nguyên nhân tập trung. Đây không phải số đo của nhóm.

Không dùng ID mới mỗi request để làm biểu đồ đều: đó là request hashing, không còn session affinity. Lịch chọn workload nhanh/chậm và lịch chọn client phải dùng luồng seed độc lập, tránh vô tình gắn hot-client với slow-request.

### 11.5. Affinity, stability và remapping

Gọi `n(k,b)` là response thành công của key k ở backend b trong membership cố định; `N_k` là tổng response thành công của key đó. Chỉ xét key có ít nhất hai request:

```text
affinity(k) = max_b n(k,b) / N_k
weighted_affinity = Σ_k max_b n(k,b) / Σ_k N_k
```

Report số key đủ điều kiện, key chỉ một request, lỗi và coverage. Một request/key tự nhiên cho affinity=1, không chứng minh ổn định. RR/LC không tối ưu affinity theo ID, nên affinity thấp không tự nghĩa là cân bằng tải kém.

Với tập K có mapping đầy đủ trước và sau:

```text
remap_ratio = số key có backend_before != backend_after / |K|
traffic_weighted_remap = Σ_k w_k × 1[backend_before != backend_after] / Σ_k w_k
stability_same_membership = 1 - remap_ratio(sweep_1, sweep_2)
```

`w_k` lấy từ trace đã đăng ký, không từ count sau khi loại timeout. Tập rỗng/tổng weight bằng 0 → N/A. Key thiếu mapping phải được report và đánh invalid snapshot theo protocol, không âm thầm bỏ khỏi mẫu số.

**Unit-test minh họa:** mapping 4 key `[A,A,B,C]` → `[A,D,B,C]` cho remap 25%. Nếu key thứ hai weight 80, ba key khác tổng weight 20, weighted remap là 80%. Đây là expected value cho analyzer, không phải dự đoán NGINX.

### 11.6. Membership khác failover

**A4:** thêm/xóa I4 trong cấu hình, reload/chờ ổn định rồi đo. **A2:** không đổi membership; I3 vẫn nằm trong config nhưng dừng rồi start lại. Hai loại thay đổi không được gộp thành một chỉ số remapping chung.

Reload có thể để worker cũ phục vụ connection cũ. Trước snapshot mới: drain worker cũ, chốt config generation, đóng client cũ/mở mới, giữ endpoint I1–I3 ổn định. `nginx -t` thành công không tự chứng minh mọi request đã dùng config mới. Recreate đổi IP có thể làm biến gây nhiễu.

Retry off làm client có thể thấy lỗi của attempt đó, nhưng không đồng nghĩa mọi theo dõi failure thụ động đều bị tắt. Connection error/timeout và các HTTP status có quy tắc khác nhau khi tính failure; phải kiểm tra cấu hình và quan sát. [NGINX proxy_next_upstream](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_next_upstream).

### 11.7. Không suy diễn quá kết quả

CH-ID tốt ở NAT không chứng minh p95 luôn thấp nhất; mapping ổn định không bảo vệ dữ liệu RAM; thêm I4 không chứng minh autoscaling/HA; ID hợp lệ không chứng minh đã xác thực; một bộ khóa đẹp không đại diện mọi người dùng. Công bố hot-key case và toàn bộ seed định trước, không chọn tập khóa sau khi xem phân bố.

## 12. Từ lý thuyết đến thí nghiệm 14 ngày

### 12.1. Trạng thái tài liệu khác trạng thái hệ thống

Config/example mô tả việc sẽ làm, chưa phải testbed đã chạy. Benchmark chỉ có kết quả khi raw/manifest và command/exit status tồn tại. Dashboard không thay raw. Ví dụ Jain=1/remap=25% là bài toán kiểm thử analyzer, không dùng làm số đo báo cáo.

### 12.2. Ma trận và độ tin cậy

Kế hoạch gồm 96 run chính, 8 xác nhận (104 run hiệu năng) và 60 lượt mapping. Mỗi cell chính n=3: từng run/median/min–max; hai contrast đăng ký trước n=5 để ước lượng paired CI. A4 dùng 5 tập khóa độc lập, không đổi thứ tự cùng một tập rồi coi là lặp độc lập. Đây là ngân sách, không phải bảo đảm statistical power.

Đơn vị phân tích latency là run/block; đơn vị khảo sát A4 là bộ khóa ở membership đã xác minh. Paired bootstrap resample nguyên cặp RR–LC hoặc IPH–CH-ID cùng block, không resample hai phía độc lập rồi gọi paired. Không lấy hàng triệu request tương quan làm hàng triệu lần lặp độc lập.

### 12.3. Ranh giới thời gian và cohort

```text
Client wall time ≈ chờ phía client + DNS/connect/TLS nếu có
                 + gửi request + proxy/backend/queue + nhận response
NGINX request time: ranh giới tại NGINX
Application timer: ranh giới tại ứng dụng
```

Không lấy client latency trừ app timer rồi gọi toàn bộ phần dư là chi phí NGINX; còn mạng, queue, buffering và ranh giới đo. B4 direct C1 so với B0 một replica qua NGINX là diagnostic hai đường đi, không cô lập hoàn toàn overhead proxy.

Throughput completion-window và latency start-cohort có ranh giới khác nhau. Lưu start/end/phase; warm-up không tính vào steady-state. Request bắt đầu trong cửa sổ nhưng kết thúc sau đó được theo dõi đến drain/deadline; ghi pending/timeout, không để biến mất. Đối soát counters phải dùng cùng cohort và tính fan-out, không đòi tổng counter ba service bằng số quote.

### 12.4. Recovery là định nghĩa vận hành

Kế hoạch dùng ba cửa sổ 10 giây liên tiếp đạt error, p95 và throughput target để xác nhận phục hồi. Phân biệt mốc fault-onset và ready-again. Nếu hai backend còn lại không đủ tải, hệ thống có thể chưa hồi phục SLO trước khi I3 quay lại; đây là kết quả, không kéo dài thời gian tùy ý để được số đẹp.

Timeline cần: gửi lệnh stop; lệnh kết thúc; lỗi được quan sát; start; ứng dụng ready; chất lượng phục vụ phục hồi. Số “failover = X giây” không có định nghĩa các mốc này rất khó bảo vệ.

### 12.5. Lý thuyết → bằng chứng

| Khái niệm | Dữ liệu cần | Phát biểu có thể bảo vệ |
|---|---|---|
| Load distribution | Count/CPU từng instance, gồm zero-count | Count và CPU có độ lệch riêng, không đồng nhất |
| Tail latency | Raw/histogram tương thích, sample count, lỗi | Percentile đúng quần thể, không lấy trung bình percentile |
| NAT/key | Effective IP/peer, ID trace, config | NGINX thực sự thấy một/nhiều khóa, không suy từ VU |
| Consistent ring | GH-ID/CH-ID cùng key/membership | Chênh lệch remapping trong điều kiện đo |
| Resilience | Fault/ready events, time series | Phục hồi hoặc chưa phục hồi theo protocol |
| Tái lập | Commit/digest/hash/seed/runner, người chạy thứ hai | Quy trình và evidence kiểm tra lại được |

### 12.6. Sau hai tuần mới mở rộng

Weighted balancing theo năng lực đã đo, cache thật, authenticated session key, retry/idempotency, Kubernetes endpoint discovery/HPA và nhiều failure domain là hướng sau này. Mỗi hướng cần RQ/protocol mới, không gắn vào tuần cuối làm thay đổi dữ liệu đang chốt.

## 13. Câu hỏi bảo vệ thường gặp

1. **Tại sao chọn 3 service?** Để có ranh giới chức năng và một luồng xuyên dịch vụ, đồng thời giữ hệ thống đủ nhỏ để kiểm soát; số 3 không tự bảo đảm kiến trúc tốt.
2. **Ba service khác gì ba replica?** Service khác trách nhiệm/API; replica là nhiều bản chạy cùng dịch vụ.
3. **Tại sao LC có thể tốt hơn RR?** Connection bận có thể phản ánh công việc đang tồn tại khi thời gian xử lý khác nhau; phải chứng minh trong workload có concurrency.
4. **LC có luôn chọn server nhanh nhất?** Không; nó không trực tiếp đo CPU hay latency tương lai.
5. **Tại sao 1.000 VU mà IPH vẫn dồn một server?** VU không phải IP; NAT hoặc prefix hashing có thể cho cùng khóa.
6. **Tại sao không chỉ báo mean?** Mean che tail latency và nhóm người dùng gặp request rất chậm.
7. **Tại sao throughput tăng nhưng chất lượng giảm?** Có thể hệ thống hoàn tất nhiều lỗi nhanh hơn, hoặc rate tăng cùng timeout; cần success throughput và SLO.
8. **Tại sao thêm replica không tăng tuyến tính?** Host/downstream/LB/client có thể là bottleneck; overhead và tài nguyên dùng chung giới hạn lợi ích.
9. **Một backend chết có mất dữ liệu không?** Benchmark fixture/stateless không trả lời được độ bền dữ liệu; nghiệp vụ ghi thật cần thiết kế persistence riêng.
10. **Tại sao không để Kubernetes tự cân bằng?** Mục tiêu là cô lập và so sánh ba thuật toán NGINX; thêm tầng chọn Pod có thể thay đổi đối tượng đang đo.
11. **Phần advanced nằm ở đâu?** CH-ID xử lý bài toán khóa IP bị gộp bởi NAT; GH-ID/CH-ID cùng khóa cô lập tác động consistent ring; slow/fault và tái lập bổ trợ đánh giá.
12. **Nếu các thuật toán gần như bằng nhau?** Đó vẫn là kết quả hợp lệ trong điều kiện đã đo; không sửa workload hậu nghiệm để cố tạo chiến thắng.
13. **Tại sao không dùng CAP để giải thích mọi lỗi?** CAP liên quan đánh đổi consistency/availability khi có partition trong mô hình dữ liệu phân tán; benchmark read-only hiện tại không kiểm chứng lựa chọn đó.
14. **Làm sao tin dữ liệu?** Manifest/config hash, raw bất biến, analyzer có test, đối soát client/log/backend và một người khác chạy tái lập.
15. **CH-ID cải thiện do đổi khóa hay ring?** A3 đo ứng dụng khi đổi IP sang ID; A4 so GH-ID/CH-ID cùng khóa để tách tác động ring.
16. **Vì sao CH-ID vẫn lệch tải?** Traffic từng key khác nhau, đặc biệt hot-client; affinity không đồng nghĩa chia đều công việc.
17. **Vì sao mapping thay ngay sau reload?** Có thể trộn worker/connection cũ hoặc endpoint identity đổi; cần drain/xác minh trước snapshot.
18. **Ba lần lặp đủ khẳng định chắc chắn không?** Không; công bố từng run và giới hạn. Hai contrast n=5 định trước vẫn cần thận trọng với small-n.

## 14. Lộ trình đọc và dùng tài liệu

- **Cả nhóm:** mục 1–4, 7–9 và câu hỏi bảo vệ; phải thống nhất từ vựng trước khi viết báo cáo.
- **Nhân trưởng:** ranh giới dịch vụ, fan-out, lỗi dây chuyền, phương pháp kết luận và giới hạn phạm vi.
- **Đào Mạnh Nhân:** workload CPU, stateless/fixture, JVM và kiểm thử API.
- **Trần Thanh Nguyên:** metrics, histogram, percentile, tài nguyên và đối soát quan sát.
- **Đào Hồng Nhật:** NGINX, IP topology, Docker, fault handling, CH-ID/GH-ID và kiểm chứng mapping.
- **Huỳnh Xuân Nin:** open model, ma trận, thống kê theo run, metric definition và analyzer.

Các liên kết đặt cạnh nội dung là nguồn gốc để tra cứu; khi viết báo cáo chính thức, ghi ngày truy cập và phiên bản phần mềm thật của nhóm. Tài liệu upstream có thể thay đổi: lưu cấu hình/version đã kiểm chứng, không sao chép mặc định mới vào một chiến dịch benchmark đang chạy.

**Chưa thực hiện:** xây dựng ứng dụng, kiểm tra cấu hình mẫu bằng NGINX và chạy thực nghiệm. Không có số liệu hiệu năng thật trong tài liệu này.

<!-- NT533_PROGRESS_BEGIN v1 -->
```json
[]
```
<!-- NT533_PROGRESS_END -->
