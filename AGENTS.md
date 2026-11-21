# AGENTS.md — NT533, mô hình ADMIN + 5 worker

## Đặc tả bắt buộc và trạng thái ban đầu

- Đọc [kế hoạch](./01_KE_HOACH_DO_AN.md) và [cơ sở lý thuyết](./02_CO_SO_LY_THUYET.md) trước khi làm.
- Repository public: `thnguyen290106/NT533-DoAn`; thế hệ/repo ID do server xác minh, không dùng PR/commit từ repo cũ.
- Ba tài liệu là đặc tả, không phải bằng chứng đã làm. Cả 70 nhiệm vụ D1–D14 ban đầu đều CHƯA THỰC HIỆN.
- Giữ PCCV, RQ, API và protocol kỹ thuật đã chốt. Không bịa số đo, kết quả test hoặc biên nhận nộp bài.

## Ai điều phối

- ADMIN chọn một ngày D1–D14 và cấp quyền chạy năm task của ngày đó; chỉ ADMIN được đổi prompt/cấu hình, bắt đầu, tiếp tục hoặc dừng run.
- TDN, DMN, TTN, DHN, HXN đăng nhập Codex của chính mình trên máy cá nhân và ghép worker. Tài khoản worker không được điều khiển task/run qua web hoặc API.
- Từ D3, bắt đầu khi worker lượt đầu có Codex và GitHub hợp lệ, cùng HOST/LOADGEN đã xác thực SSH. Các worker khác được kiểm tra khi tới lượt. Không bỏ qua kiểm tra xác thực, fingerprint, công cụ cần thiết hoặc CI.
- Không chặn bắt đầu theo số CPU, dung lượng RAM hoặc disk VM. Nếu chạy thực tế OOM/hết disk/test lỗi thì báo đúng lỗi, không tự báo đạt.
- Ngày đã chọn xong thì chờ ADMIN chọn ngày tiếp theo. Không tự chạy D2 sau D1.

## Bắt buộc làm trên Ubuntu

- TDN (Order), DMN (Catalog), TTN (Inventory/metrics), DHN (hạ tầng): workspace riêng trên HOST. HXN (k6/trace/analyzer): workspace riêng trên LOADGEN. DHN có thể kiểm tra/cấu hình cả hai VM khi task yêu cầu.
- Source được sửa và test trên Ubuntu qua MCP/SSH broker, không viết/build source trên Windows. Không sửa chung checkout với người khác.
- IP, username và đường dẫn workspace do server cấp; không tự đoán, ghi cứng hoặc đổi máy đích bằng prompt.
- Không gửi SSH password, sudo password, GitHub token hoặc Codex auth cho agent. Broker giữ credential riêng trên server.
- Được tự kiểm kê/cài công cụ và dependency thiếu trên hai VM, dùng lại bản phù hợp đã có. Sudo chỉ qua adapter có kiểm soát, không thay hệ điều hành/phần mềm/firewall Windows.
- Thao tác phá hủy dữ liệu, reset OS hoặc đổi mạng có thể làm mất SSH phải hỏi ADMIN. Không xóa raw/backup hay dữ liệu ngoài vùng NT533.

## Git, review và triển khai tự động

- Server quản lý Git bằng tài khoản GitHub hiện tại; thông tin thành viên/PCCV nằm trong metadata, không giả tác giả.
- Mỗi task bắt đầu từ main mới nhất trong workspace riêng. Sửa nhỏ nhất đúng mục tiêu, chạy test thật và giữ nguyên validation/error handling.
- Sau test, worker/server tin cậy cập nhật bằng chứng trong CẢ BA FILE MD trước commit. Chỉ cập nhật tiến độ liên quan task, giữ kết quả của mọi thành viên; không tự viết lại khối JSON do hệ thống sinh.
- Từ D3, server tự commit, push, PR và điều phối tuần tự. Các worker bàn giao qua ba MD và làm độc lập theo phạm vi.
- Merge tuần tự, bắt buộc kiểm tra Ubuntu và CI trên đúng HEAD. Main đổi thì hợp nhất lại, test lại và chạy lại CI. Không force-push, bỏ test hoặc dùng duyệt của HEAD cũ.
- Conflict tiến độ được hợp nhất có cấu trúc. Conflict khác gửi Codex phụ trách tự sửa và kiểm thử tối đa ba vòng; không chọn toàn bộ ours/theirs để hết lỗi.
- Hết ba vòng chưa đạt thì chặn task và task phụ thuộc; task độc lập khác vẫn có thể xong. Không báo DONE giả.
- Deploy đúng SHA/image digest đã merge, kiểm tra readiness/API/smoke thật; lỗi thì rollback bản tốt trước đó và ghi kết quả. D1 chưa có dịch vụ thì không báo đã deploy ứng dụng.
- Thu log, exit status, artifact và checksum. Mất kết nối phải xác minh checkpoint/job ID trước khi retry, không chạy lặp mù.

## Bằng chứng và dữ liệu

- Khối tiến độ là bản chụp bằng chứng trước commit, không phải lệnh điều phối. Website/GitHub ghi trạng thái hiện tại, không tạo chuỗi commit vô hạn để tự dẫn SHA của chính mình.
- Không đưa `.state`, database, mật khẩu, private key, raw lớn, backup hoặc sáu folder điều phối vào repo public.
- Test cơ chế điều phối phải ghi rõ simulated hay Codex thật, số máy và số login; không gọi test một máy là năm máy vật lý.
- Dọn test theo manifest chỉ gồm file/container/package do chính lượt test tạo. Không có snapshot thì không cam kết xóa mọi dấu vết/log hệ điều hành hoặc hoàn nguyên VM tuyệt đối.




## Hoàn tất phần việc D1 — phục hồi điều phối 17/11/2026

ADMIN đã tạm dừng cả năm worker và trực tiếp ghép tài liệu của TDN, DMN, TTN, DHN, HXN. Giữ nguyên thiết kế, bằng chứng kiểm tra cũ và lịch sử lỗi; loại các marker Git trong thân và hợp nhất JSON tiến độ theo task ID. Nội dung này ghi nhận phần thiết kế/kiểm kê D1, không xác nhận dịch vụ, benchmark hoặc triển khai ứng dụng đã chạy. Không tự chuyển D2.

Theo yêu cầu ADMIN, không chạy lại bộ test hay các harness Ubuntu trong lượt phục hồi. Các biên nhận cũ được giữ nguyên, gồm kết quả thất bại ban đầu; kết quả kiểm kê dưới đây là thao tác chỉ đọc mới, không phải kiểm thử tải. CI của nhánh tích hợp vẫn do GitHub chạy theo bảo vệ main.

**Đề cương:** ADMIN xác nhận trong phiên làm việc ngày 17/11/2026 rằng đề cương đã được gửi giảng viên. Chưa đính kèm kênh, thời điểm gửi hoặc biên nhận; bổ sung khi ADMIN cung cấp. Xác nhận này không có nghĩa giảng viên đã duyệt phạm vi hoặc phần nâng cao.

| Kiểm kê host thực qua SSH đã ghim fingerprint | HOST | LOADGEN |
|---|---|---|
| IP | 10.70.197.121 | 10.70.197.172 |
| Ubuntu | 24.04.5 LTS | 24.04.3 LTS |
| Kernel | 6.8.0-149-generic | 6.8.0-149-generic |
| CPU logic | 8 | 8 |
| RAM tổng / available tại thời điểm thu (MiB) | 5878 / 5139 | 3868 / 3185 |
| Swap | 0 | 0 |
| Disk available vùng Docker (GiB) | 8.99 | 12.93 |
| Docker Engine | 29.1.3 | 29.1.3 |
| Compose | 2.40.3 | 2.40.3 |
| Managed image ID rút gọn | eb1984d39325 | 64174dda1b88 |
| Route tới máy kia | ens33; source 10.70.197.121 | ens33; source 10.70.197.172 |
| Thời điểm UTC | 2026-11-17T08:48:21.107Z | 2026-11-17T08:48:22.330Z |

**Giới hạn tài nguyên:** HOST có RAM tổng thấp hơn cả budget thường 5888 MiB và budget I4 6400 MiB, chưa tính OS/Docker. D1 chỉ hoàn tất thiết kế và ghi nhận máy thực; cần tăng RAM hoặc có quyết định điều chỉnh đồng bộ đã được duyệt trước khi chạy đủ stack/pilot. Không giảm replica/quota riêng một thuật toán, không nhận G2/G3 đạt và không thay đổi cấu hình VM trong lượt này. Route read-only không chứng minh firewall, Real-IP, cổng dịch vụ hay khả năng chịu tải.


## Bàn giao vận hành sau D2

ADMIN tạm dừng năm worker và trực tiếp hoàn tất D2. PR #5 chứa Catalog, PR #6 chứa Inventory, Order, Compose và smoke. Từ D3, mỗi lượt chỉ có worker được giao; ai làm lượt kế tiếp đọc ba MD và source đã merge. Thiếu thông tin môi trường thì dùng get_lab/probe_lab trên hai Ubuntu rồi ghi dữ kiện đã xác minh. Trong từng MD, thêm đúng một mục `## Bàn giao Dxx-MEMBER` ở cuối thân, giữ nguyên mục cũ và sổ JSON do coordinator ghi. Worker đăng nhập GitHub bằng thông tin xác thực cục bộ; app đối chiếu quyền ghi collaborator trên chính repo trước khi giao lượt.

D2 trên HOST đã kiểm 47 test Catalog, 4 Inventory, 3 Order và Compose từng service đều healthy. LOADGEN chạy k6 được 24/24 kiểm tra; test đối chứng trả HTTP 200 nhưng tổng tiền sai làm k6 thoát 99. [Kết quả smoke D2](experiments/d2/smoke-summary.txt).

## Bàn giao D03-DMN

- Phần mã nguồn trong `services/catalog` gồm `Dockerfile`, `.dockerignore` và `docker_smoke_test.py`, trên base `96068aee2d23bef76ff973765930234ae2bbe273`. Dockerfile dùng context riêng, hai base image ghim digest theo `infra/Dockerfile`, chạy Maven `verify` trong tầng build và chạy JAR bằng Java 21 với UID/GID 10001. API dùng cổng 8080 và readiness dùng cổng 8082.
- Smoke khởi động C1–C3 trên cùng image ID, dùng cổng tạm trên loopback và dọn các container tạo trong lượt chạy. Smoke kiểm tra readiness, list theo thứ tự, detail P001–P003, sáu ca lỗi HTTP, header `Allow` và metadata trong header/body. Nó so từng byte của `BOOT-INF/classes/catalog-products.json` trong JAR lấy từ từng container với fixture nguồn.
- Kiểm tra lại trên workspace Ubuntu HOST qua `vm_exec` ngày 18/11/2026. Từ `services/catalog`, `mvn -B -ntp -o verify -DfailIfNoTests=true` in `BUILD SUCCESS` và `Tests run: 47, Failures: 0, Errors: 0, Skipped: 0` (26 HTTP, 21 fixture), exit 0. Biên nhận `be3c1a30ca791d1a956d0ca6c0b357ea8c94ea36e163c6ba`.
- `python3 -B -c '<harness trong biên nhận vm_exec>'` gọi `check_replica` cho ba tiến trình `java -jar target/catalog-service-1.0.0.jar` với `INSTANCE_ID=C1/C2/C3` và cổng loopback riêng. Cả ba in `readiness UP, list, 3 details, six error cases`. Fixture trùng từng byte và có SHA-256 `bd76926a87fd55258a567c248146ff215632ae323bd276fcc7a76eae227d850e`. Hai ca đối chứng in `Rejected as expected` khi đưa sai `instanceId` và khi thêm một byte vào fixture đối chiếu. Lệnh thoát 0, biên nhận `5453b8a67908f2b69be51eacee414b34ca3f95cb7134cb75`. `python3 -B docker_smoke_test.py --help` in cú pháp nhận tag hoặc ID, exit 0, biên nhận `223f3539db2a34d5f1056ce7e20201106481828b2c2662a6`.
- `get_lab` xác nhận workspace `/workspace` thuộc HOST. `probe_lab` trên HOST và LOADGEN đều exit 0. HOST báo Ubuntu 24.04.5 LTS, LOADGEN báo Ubuntu 24.04.3 LTS, cùng kernel 6.8.0-149-generic và Docker Compose 2.40.3. Kiểm tra trong container broker xác nhận thiếu Docker CLI, các socket Docker mặc định và rootless, cùng biến `DOCKER_HOST`, exit 0, biên nhận `818ae74b065c5ba0a466976b16378bc20cd842471231b00f`. `docker build -t nt533-catalog:d03-dmn .` tiếp tục trả `executable file not found in $PATH`, exit 127, biên nhận `911d6895b91ea0f51d9f57377a098bb34ccf72fae2e0e0e2`.
- Còn thiếu image ID và kết quả chạy Docker C1–C3. Bằng chứng trên xác minh contract và fixture ở mức JAR. Bộ điều phối cần chạy các lệnh sau trên HOST có Docker từ gốc checkout chứa thay đổi của task, lưu SHA checkout, image ID, RepoDigests nếu có và đầu ra/exit code của smoke, rồi xác minh CI trên HEAD được nộp.

```bash
cd services/catalog &&
  git rev-parse HEAD &&
  docker build -t nt533-catalog:d03-dmn . &&
  image_id=$(docker image inspect --format '{{.Id}}' nt533-catalog:d03-dmn) &&
  docker image inspect --format 'ID={{.Id}} RepoDigests={{json .RepoDigests}}' "$image_id" &&
  python3 -B docker_smoke_test.py "$image_id"
```



- Nghiệm thu bổ sung trên Ubuntu HOST (2026-11-18T09:42:40.826Z UTC, biên nhận máy chủ 26243eec9c53-smoke-retry). Docker build từ snapshot Catalog trên base `96068aee2d23bef76ff973765930234ae2bbe273` thành công, image `sha256:356d1d2cc3e67a9e54e85001cb941ae5bbff85cd4c2b9f1bb3def4da291311d1` (tag `nt533-catalog:d03-verify-26243eec9c53`).
- Lượt smoke đầu gặp `ConnectionResetError` lúc cổng đã được publish nhưng tiến trình Java còn khởi động. Đã sửa `check_ready` để thử lại khi gặp `ConnectionError` trong cửa sổ 45 giây có sẵn. Kiểm tra hồi quy xác nhận ca reset rồi HTTP UP thực hiện đúng hai lần gọi. Đầu vào image giữ nguyên sau khi sửa script smoke.
- Chạy `python3 -I -B docker_smoke_test.py nt533-catalog:d03-verify-26243eec9c53` trên HOST. C1, C2 và C3 đều đạt readiness, list, ba detail và sáu ca HTTP lỗi. Fixture trong JAR của cả ba replica trùng từng byte với fixture nguồn, SHA-256 `bd76926a87fd55258a567c248146ff215632ae323bd276fcc7a76eae227d850e`. Smoke và kiểm tra hồi quy đều exit 0.

## Bàn giao D03-TTN

- ADMIN thực hiện D3. Prometheus scrape trực tiếp chín management endpoint C1–C3, I1–I3, O1–O3 tại cổng 8082 mỗi 5 giây. `honor_labels` giữ nhãn service/instance của ứng dụng. Kiểm thử Inventory xác nhận readiness, nhãn `service=inventory`, `instance=I2` và tách cổng management khỏi API.
- `mvn -B -ntp verify -DfailIfNoTests=true` tại `services/inventory` trên HOST, exit 0, 5/5 ca đạt.
- `promtool check config` trên HOST, exit 0.

## Bàn giao D03-DHN

- ADMIN thực hiện D3. Compose khai báo ba replica mỗi dịch vụ, healthcheck riêng, NGINX có ba upstream RR độc lập và listener nội bộ 8083 cho các call của Order. Cổng backend chỉ dùng nội bộ. Prometheus bind loopback, retention 15 ngày. Kiểm tra cả chín replica và phân phối thật ở lần triển khai tích hợp.
- `docker compose config`, kiểm tra ranh giới Compose bản gốc/bản resolve và `nginx -t` trên HOST, exit 0.

## Bàn giao D03-TDN

- ADMIN thực hiện D3. Củng cố contract Quote bằng hai HTTP call theo thứ tự Catalog rồi Inventory. Kiểm tra giá, tồn, tổng tiền, request ID và call ID của từng downstream. HTTP 502 khi Inventory trả request ID khác. Kiểm thử xuyên cụm dùng bản triển khai D3.
- `mvn -B -ntp verify -DfailIfNoTests=true` tại `services/order` trên HOST, exit 0, 4/4 ca đạt.

## Bàn giao D03-HXN

- ADMIN thực hiện D3. Parser Python stdlib đọc `requests.jsonl`, k6 JSONL và log NGINX JSONL tùy chọn. Tách lỗi HTTP, transport và contract, giữ instance zero-count, percentile nearest-rank đơn vị ms và tách riêng k6 duration. Fixture kiểm tra lỗi trùng ID và unknown instance. Cohort theo manifest và aggregate theo block thuộc lượt sau.
- `python3 -m unittest discover -s analysis -p test*.py -v` trên LOADGEN, exit 0.

## Bàn giao D04-DMN

- ADMIN trực tiếp thực hiện. Profile CPU chỉ có trong Spring lab. SHA-256 chạy đúng số vòng cấu hình, bắt đầu bằng NT533-v1. Kiểm thử checksum chuẩn, cấm điều khiển vòng lặp từ request và xác nhận route tắt ngoài lab. N mặc định 1000 dùng để smoke, N chính thức chốt ở pilot.

## Bàn giao D04-TTN

- ADMIN trực tiếp thực hiện. Inventory lab xử lý fast 20 ms, slow 200 ms và mapping không delay; fault I3 thêm đúng 300 ms. Dashboard có CPU, JVM RAM, GC và bộ đếm theo service/instance. Tỷ lệ lớp delay do trace quyết định.
- Ubuntu HOST . · `python3 -m json.tool observability/dashboard.json` · exit 0.

## Bàn giao D04-TDN

- ADMIN trực tiếp thực hiện. Order giới hạn connect 200 ms, cả body từng call 1 s và deadline Quote 2,5 s. Timeout hủy future, trả 504 và dừng fan-out. Integration test giữ headers rồi chặn body, kiểm 5xx downstream trả 503 và không gọi Inventory khi Catalog thất bại.

## Bàn giao D04-DHN

- ADMIN trực tiếp thực hiện. RR, LC và IPH sinh từ chung một cấu hình. Ba upstream giữ nguyên membership và chính sách proxy, chỉ thay directive thuật toán. Đối chiếu byte phần chung và kiểm nginx -t từng bản.
- Ubuntu HOST . · `python3 -m unittest discover -s infra/tests -v` · exit 0.
- Kiểm tra cấu hình/runtime bằng adapter HOST · exit 0.

## Bàn giao D04-HXN

- ADMIN trực tiếp thực hiện. Sinh trace UTF-8/LF từ request index, seed client và luồng delay độc lập. Test tái sinh byte/checksum, 1000 ID, 80/20 và đúng các cột quote/IP/profile.
- Ubuntu LOADGEN . · `python3 -m unittest discover -s analysis -p test*.py -v` · exit 0.

## Bàn giao D05-DMN

- ADMIN trực tiếp thực hiện. Khóa SHA-256 fixture chuẩn, ghi rõ workload và profile allowlist. Catalog ghi request/timer một lần theo route template và nhãn hữu hạn để phục vụ đối soát sau này.

## Bàn giao D05-TTN

- ADMIN trực tiếp thực hiện. Dashboard export theo service, instance và cửa sổ đã chọn. Inventory đối chiếu custom counter, timer và route template, loại health/scrape và không đưa requestId vào label.
- Ubuntu HOST . · `python3 -m json.tool observability/dashboard.json` · exit 0.

## Bàn giao D05-DHN

- ADMIN trực tiếp thực hiện. CH-ID và GH-ID dùng cùng client ID, chỉ khác consistent. Ingress lab cần đúng peer và header hợp lệ; public bỏ header lab và không route /internal/bench.
- Ubuntu HOST . · `python3 -m unittest discover -s infra/tests -v` · exit 0.
- Kiểm tra cấu hình/runtime bằng adapter HOST · exit 0.

## Bàn giao D05-HXN

- ADMIN trực tiếp thực hiện. Runner trên LOADGEN kiểm trace/checksum, target lab, tool và dung lượng, dùng index theo phase. Lưu manifest với commit, digest, seed và config/protocol hash; giữ nguyên stdout/stderr, exit code, raw và lý do invalid.
- Ubuntu LOADGEN . · `python3 -m unittest discover -s analysis -p test*.py -v` · exit 0.

## Bàn giao D05-TDN

- ADMIN trực tiếp thực hiện. Review ranh giới public/lab/private, port management riêng và không route benchmark từ public. Order bổ sung metrics/log có nhãn hữu hạn, giữ status downstream thực và không đưa ID vào metric.

## Bàn giao D06-TTN

- ADMIN trực tiếp thực hiện. Tách phép đếm completion-window và cohort bắt đầu đo, so drain và observation thiếu. Audit UTC và monotonic timestamp của sự kiện fault, giữ reset/mất scrape là dữ liệu thiếu thay vì 0.
- Ubuntu HOST . · `python3 -m unittest discover -s observability/tests -v` · exit 0.

## Bàn giao D06-DHN

- ADMIN trực tiếp thực hiện. Real-IP chỉ tin peer /32, kiểm dải IP mô phỏng theo Q04 và log peer/effective IP. I4 tách profile mapping, giữ image/quota Inventory. Fault chỉ định đúng I3 theo nhãn Compose, start lại trong finally, xác minh readiness và lưu UTC/monotonic.
- Ubuntu HOST . · `python3 -m unittest discover -s infra/tests -v` · exit 0.
- Ubuntu HOST . · `python3 infra/fault.py --help` · exit 0.
- Kiểm tra cấu hình/runtime bằng adapter HOST · exit 0.

## Bàn giao D06-HXN

- ADMIN trực tiếp thực hiện. A3 giữ một IP NAT với uniform và hot-ID. A4 có năm keyset 1000 ID khác nhau, snapshot tuần tự 10 request/s, xác nhận generation, coverage và ổn định giữa hai sweep. Số đo đầy đủ thuộc chiến dịch sau.
- Ubuntu LOADGEN . · `python3 -m unittest discover -s analysis -p test*.py -v` · exit 0.

## Bàn giao D06-DMN

- ADMIN trực tiếp thực hiện. Fixture độc lập kiểm phân phối đều/lệch/toàn zero, percentile n=0/1, remap 1/4=25% và trọng số 80/100=80%; không đồng nhất dữ liệu thiếu với 0.
- Ubuntu HOST . · `python3 -m unittest discover -s services/catalog/analysis-tests -v` · exit 0.

## Bàn giao D06-TDN

- ADMIN trực tiếp thực hiện. Chương kiến trúc mô tả quyền sở hữu Catalog/Inventory/Order, chuỗi Quote tuần tự, ranh giới 502/503/504 và phạm vi A1/A2/A4. Review fault ghi rõ I3, readiness, restore và điểm lỗi chung HOST/NGINX.

## Bàn giao D07-DMN

- ADMIN trực tiếp thực hiện. Baseline so từng byte fixture của ba JAR trong cụm và của C1 độc lập. Ghi image ID thực tế của từng replica; xác nhận cả ba image trả cùng SHA-256 của 1000 vòng (smoke) trong container lab độc lập.
- Ubuntu HOST . · `python3 -m py_compile services/catalog/baseline.py` · exit 0.

## Bàn giao D07-TTN

- ADMIN trực tiếp thực hiện. Audit một cohort Quote gồm 200, Catalog 404, input 400 theo request/call ID. Sau deploy so đúng 3 request client với 6 app/gateway records, delta counter/timer từng service và 3 downstream observations.
- Ubuntu HOST . · `python3 -m py_compile observability/verify_live.py` · exit 0.

## Bàn giao D07-DHN

- ADMIN trực tiếp thực hiện. G2 smoke năm biến thể trên cùng image, kiểm ID/trust, membership và khôi phục mapping 3→4→3. Kiểm kê dọn đúng container/network thuộc lượt thử; bảo toàn cụm đang chạy.
- Ubuntu HOST . · `python3 -m unittest discover -s infra/tests -v` · exit 0.
- Kiểm tra cấu hình/runtime bằng adapter HOST · exit 0.

## Bàn giao D07-HXN

- ADMIN trực tiếp thực hiện. Dry-run Quote trên LOADGEN, raw→summary→PNG có checksum và nguồn truy ngược. Attempt invalid giữ riêng raw và exit code; không tính mẫu smoke vào chiến dịch.
- Ubuntu LOADGEN . · `python3 -m unittest discover -s analysis -p test*.py -v` · exit 0.

## Bàn giao D07-TDN

- ADMIN trực tiếp thực hiện. Tích hợp API/error/Quote, CI và G2 trên main. Tag feature-freeze gắn đúng commit được nghiệm thu sau khi đủ bằng chứng; không thêm tính năng ngoài D7.

## Bàn giao D08-DHN

- ADMIN trực tiếp thực hiện. Kiểm kê thật hai Ubuntu, khóa digest cấu hình NGINX đang chạy, đối chiếu quota/connection và trace 1.000 prefix /24 cùng NAT một IP. Hồ sơ infra/D08_PREFLIGHT.md ghi nguyên điều kiện còn thiếu trước pilot, không chứng nhận G3.

## Bàn giao D08-DMN

- ADMIN trực tiếp thực hiện. ?o CPU pilot 80 req/s tr?n b?n c? ghi nh?n 2.850 l?i 504 v? 991 l?i 502 ? c?a s? ?o. D?ng l?i m?t buffer SHA-256 trong t?ng request, gi? nguy?n s? v?ng, checksum v? contract. ??i chi?u JDK 21 tr?n HOST kh?p s?u m?c t? 1 ??n 1.024.000 v?ng. ? 256.000 v?ng, heap allocation ?o ???c l? 12288448 B/request tr??c s?a v? 496 B/request sau s?a. N v? R_ref c?a b?n sau s?a s? ???c ?o l?i tr??c G3.
- Ubuntu HOST services/catalog · `mvn -B -ntp test` · exit 0.

## Bàn giao D08-TTN

- ADMIN trực tiếp thực hiện. Đo ba đường CPU/Mixed/Quote trên runtime a96cfe9dec1d250456b21e1813672b584ac3e71b. R_ref lần lượt 80, 320, 320 req/s. Mỗi bậc dùng warm-up 300 s và lưu dữ liệu phía LOADGEN.

## Bàn giao D08-HXN

- ADMIN trực tiếp thực hiện. Chốt lịch từ ba biên nhận R_ref và ghi SHA-256 trace trước chiến dịch. B0–B4 54 lượt, A1/A3 và hai contrast 41 lượt, A2 9 lượt cùng 60 sweep A4.
- Ubuntu LOADGEN . · `python3 -m unittest discover -s analysis/tests` · exit 0.

## Bàn giao D08-TDN

- ADMIN trực tiếp thực hiện. Chấp nhận G3 với ba R_ref đo thật, N=512000 và digest runtime/runner đã khóa. D9–D11 dùng đúng schedule 104 lượt và 60 sweep.

### Bổ sung Q07 · Warm-up trên mạng từ xa

- Áp dụng [nt533-q05-remote-v3](experiments/PROTOCOL_REMOTE_V3.md) cho topology remote-zerotier. Hai cửa sổ 30 s cuối dùng p95 NGINX với ngưỡng 10% và success RPS tại LOADGEN với ngưỡng 5%. Sau nhánh 300 s, vượt một trong hai ngưỡng thì dừng G3.
- SLO tiếp tục dùng p95 đầu cuối tại LOADGEN. Báo cáo giữ p95/p99 của hai phía, RTT, jitter, mất gói và tài nguyên LOADGEN. Dữ liệu v1 giữ riêng theo phiên bản, cùng bằng chứng và SHA-256.

## Bàn giao D09-DHN

- ADMIN trực tiếp thực hiện. Vận hành 54 lượt core. Kiểm tra từ các archive đã đối chiếu SHA-256; 54 lượt hiệu năng và 0 sweep hợp lệ trong ngày.

## Bàn giao D09-HXN

- ADMIN trực tiếp thực hiện. Ledger core B0–B4. Kiểm tra từ các archive đã đối chiếu SHA-256; 54 lượt hiệu năng và 0 sweep hợp lệ trong ngày.

## Bàn giao D09-DMN

- ADMIN trực tiếp thực hiện. Đối chiếu B0, B1 và B4. Kiểm tra từ các archive đã đối chiếu SHA-256; 54 lượt hiệu năng và 0 sweep hợp lệ trong ngày.

## Bàn giao D09-TTN

- ADMIN trực tiếp thực hiện. Cửa sổ B2 và JVM. Kiểm tra từ các archive đã đối chiếu SHA-256; 54 lượt hiệu năng và 0 sweep hợp lệ trong ngày.

## Bàn giao D09-TDN

- ADMIN trực tiếp thực hiện. Phương pháp và đối chiếu Quote B3. Kiểm tra từ các archive đã đối chiếu SHA-256; 54 lượt hiệu năng và 0 sweep hợp lệ trong ngày.

## Bàn giao D10-DHN

- ADMIN trực tiếp thực hiện. A1, A3 và bằng chứng effective IP. Kiểm tra từ các archive đã đối chiếu SHA-256; 41 lượt hiệu năng và 0 sweep hợp lệ trong ngày.

## Bàn giao D10-HXN

- ADMIN trực tiếp thực hiện. 33 lượt advanced và 8 xác nhận. Kiểm tra từ các archive đã đối chiếu SHA-256; 41 lượt hiệu năng và 0 sweep hợp lệ trong ngày.

## Bàn giao D10-TTN

- ADMIN trực tiếp thực hiện. Delay I3 và phân phối hot-ID. Kiểm tra từ các archive đã đối chiếu SHA-256; 41 lượt hiệu năng và 0 sweep hợp lệ trong ngày.

## Bàn giao D10-DMN

- ADMIN trực tiếp thực hiện. Đối chiếu raw, summary và hình. Kiểm tra từ các archive đã đối chiếu SHA-256; 41 lượt hiệu năng và 0 sweep hợp lệ trong ngày.

## Bàn giao D10-TDN

- ADMIN trực tiếp thực hiện. Thảo luận theo hai contrast đã đăng ký. Kiểm tra từ các archive đã đối chiếu SHA-256; 41 lượt hiệu năng và 0 sweep hợp lệ trong ngày.

## Bàn giao D11-DHN

- ADMIN trực tiếp thực hiện. Stop/start I3 và membership A4. Kiểm tra từ các archive đã đối chiếu SHA-256; 9 lượt hiệu năng và 60 sweep hợp lệ trong ngày.

## Bàn giao D11-HXN

- ADMIN trực tiếp thực hiện. Khóa G4 với 104 lượt và 60 sweep. Kiểm tra từ các archive đã đối chiếu SHA-256; 9 lượt hiệu năng và 60 sweep hợp lệ trong ngày.

## Bàn giao D11-DMN

- ADMIN trực tiếp thực hiện. Mapping có và không có trọng số. Kiểm tra từ các archive đã đối chiếu SHA-256; 9 lượt hiệu năng và 60 sweep hợp lệ trong ngày.












































<!-- NT533_PROGRESS_BEGIN v1 -->
```json
[
  {
    "id": "06d9bc4cd7c6eeaca7fe528c02dcc58b3129f12ddf4fc2c8:code",
    "taskId": "06d9bc4cd7c6eeaca7fe528c02dcc58b3129f12ddf4fc2c8",
    "member": "DHN",
    "pccvId": "D11-DHN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-21T05:27:42.372Z",
    "base": "adf5a7e312d98ff537d31436545f189b01c75454",
    "files": [
      "infra/D11_DHN_EVIDENCE.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "06e5c475aaaefe7536e04d46e46ae43ea47fbcc755776405:code",
    "taskId": "06e5c475aaaefe7536e04d46e46ae43ea47fbcc755776405",
    "member": "DHN",
    "pccvId": "D08-DHN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T14:20:21.057Z",
    "base": "f3c1ae21a14a62d491ed16a7ce7dff0da8bebb71",
    "files": [
      "infra/D08_PREFLIGHT.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "08b03fe4b201e38ad777cd56b1220617b5304068f5e46154:code",
    "taskId": "08b03fe4b201e38ad777cd56b1220617b5304068f5e46154",
    "member": "DMN",
    "pccvId": "D07-DMN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T13:13:25.949Z",
    "base": "8f3f781c1f6bc2d8aadf4746bd591839735216bd",
    "files": [
      "services/catalog/baseline.py"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "0a9f823dc492ea3b9b440730c914c0ac0dc3663af0f6dc88:code",
    "taskId": "0a9f823dc492ea3b9b440730c914c0ac0dc3663af0f6dc88",
    "member": "DHN",
    "pccvId": "D04-DHN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T12:32:36.210Z",
    "base": "2777d569ef429ce38c005d7721b7c2a7c9b3e042",
    "files": [
      "infra/routing.py",
      "infra/tests/test_routing.py"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "186f6979f031df50f7fe4c6307f5edec99c31963f4f91cd4:code",
    "taskId": "186f6979f031df50f7fe4c6307f5edec99c31963f4f91cd4",
    "member": "TTN",
    "pccvId": "D04-TTN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T12:27:40.175Z",
    "base": "2df0d6143a1774a2f992155aa93363a869ed53c5",
    "files": [
      "observability/dashboard.json",
      "services/inventory/src/main/java/vn/edu/uit/nt533/inventory/InventoryBenchController.java",
      "services/inventory/src/test/java/vn/edu/uit/nt533/inventory/InventoryBenchTest.java"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "18f2f7b93645676d63e915eca69ae1b296e34e9b990157e5:code",
    "taskId": "18f2f7b93645676d63e915eca69ae1b296e34e9b990157e5",
    "member": "DHN",
    "pccvId": "D07-DHN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T13:17:17.592Z",
    "base": "619191dd6907956f25bcdd38e2ff7712300c1b20",
    "files": [
      "infra/tests/lab_smoke.py",
      "infra/RELEASE_SMOKE.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "259b04f8751eb99e6766357b0e79bb04f8fc0de9caac318e:code",
    "taskId": "259b04f8751eb99e6766357b0e79bb04f8fc0de9caac318e",
    "member": "TTN",
    "pccvId": "D08-TTN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-21T02:42:05.348Z",
    "base": "a96cfe9dec1d250456b21e1813672b584ac3e71b",
    "files": [
      "observability/D08_RESOURCE_PILOT.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "260ff6fb8b480986728d3b8b82043de269238b695ee9daf8:code",
    "taskId": "260ff6fb8b480986728d3b8b82043de269238b695ee9daf8",
    "member": "TDN",
    "pccvId": "D02-TDN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T04:59:54.935Z",
    "base": "fe64bceeb078c8e4962bdb8789fe2462f29b335d",
    "files": [
      "services/order/.gitignore",
      "services/order/.mvn/wrapper/maven-wrapper.properties",
      "services/order/mvnw",
      "services/order/mvnw.cmd",
      "services/order/pom.xml",
      "services/order/src/main/java/vn/edu/uit/nt533/order/OrderApplication.java",
      "services/order/src/main/java/vn/edu/uit/nt533/order/OrderController.java",
      "services/order/src/main/java/vn/edu/uit/nt533/order/OrderException.java",
      "services/order/src/main/java/vn/edu/uit/nt533/order/OrderExceptionHandler.java",
      "services/order/src/main/java/vn/edu/uit/nt533/order/QuoteService.java",
      "services/order/src/main/java/vn/edu/uit/nt533/order/RequestMetadata.java",
      "services/order/src/main/java/vn/edu/uit/nt533/order/RequestMetadataFilter.java",
      "services/order/src/main/resources/application.properties",
      "services/order/src/test/java/vn/edu/uit/nt533/order/OrderHttpTest.java",
      ".github/workflows/nt533-ci.yml"
    ],
    "tests": [
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "390fee983640cc534432c926ff0e6a899eb07dbf1276e4d3:code",
    "taskId": "390fee983640cc534432c926ff0e6a899eb07dbf1276e4d3",
    "member": "TTN",
    "pccvId": "D07-TTN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T13:15:16.852Z",
    "base": "8c5d4d1d579f5ca652c1f54038ad0c253dae457b",
    "files": [
      "observability/verify_live.py"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "3ee7fc38a4832bb722c7608320eb53c788b5ddfe13ff11c0:code",
    "taskId": "3ee7fc38a4832bb722c7608320eb53c788b5ddfe13ff11c0",
    "member": "TTN",
    "pccvId": "D10-TTN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-21T04:37:22.130Z",
    "base": "a4dca95085f11547a5c7b5609fa3454145e660bf",
    "files": [
      "observability/D10_TTN_EVIDENCE.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "3efe8f41d93a815dddbe5e2e9bf5a47a73f1cd0d9ebee0d9:code",
    "taskId": "3efe8f41d93a815dddbe5e2e9bf5a47a73f1cd0d9ebee0d9",
    "member": "HXN",
    "pccvId": "D08-HXN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-21T02:45:37.451Z",
    "base": "d65065081ae6e1cd884642c14fb688ce8a2c4b36",
    "files": [
      "analysis/analyze.py",
      "analysis/chart.py",
      "analysis/mapping.py",
      "analysis/run.py",
      "analysis/tests/test_analyze.py",
      "analysis/tests/test_mapping.py",
      "analysis/tests/test_run.py",
      "analysis/trace.py",
      "load-tests/workload.js",
      "analysis/pilot.py",
      "analysis/pilot_gate.py",
      "analysis/schedule.py",
      "analysis/summary_report.py",
      "analysis/tests/test_pilot_gate.py",
      "analysis/tests/test_pilot_resume.py",
      "analysis/tests/test_schedule.py",
      "analysis/tests/test_summary_report.py",
      "analysis/tests/test_wan.py",
      "analysis/wan.py",
      "experiments/D08_SCHEDULE_LOCK.md",
      "experiments/PROTOCOL_REMOTE_V4.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "k6",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "449625522e7b8ccbd16d88a5d211a9d24d773db3ca3bcc20:code",
    "taskId": "449625522e7b8ccbd16d88a5d211a9d24d773db3ca3bcc20",
    "member": "DMN",
    "pccvId": "D11-DMN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-21T05:36:02.418Z",
    "base": "2d0c451c45a185c36165db5410b871685c584e56",
    "files": [
      "services/catalog/D11_DMN_EVIDENCE.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "476853838b4e98155c11a32960c7211f71d99c1f51b8a5b6:code",
    "taskId": "476853838b4e98155c11a32960c7211f71d99c1f51b8a5b6",
    "member": "DHN",
    "pccvId": "D09-DHN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-21T03:37:47.764Z",
    "base": "8f949138e45fefbf173308875b9a7595ef58b8d7",
    "files": [
      "infra/D09_DHN_EVIDENCE.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "4a1e67af68c5c564a6ad23a3c53b41f53143849e8bcc7ff4:code",
    "taskId": "4a1e67af68c5c564a6ad23a3c53b41f53143849e8bcc7ff4",
    "member": "HXN",
    "pccvId": "D07-HXN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T13:19:20.406Z",
    "base": "5dfcfd2aed187c0e4b5f3c547e6a7d678fc4ee0e",
    "files": [
      "analysis/run.py",
      "load-tests/workload.js",
      "analysis/chart.py",
      "analysis/requirements.txt",
      "experiments/DRY_RUN.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "k6",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "584f70085b5700ea1d556f758a4556646529ad65d3da7819:code",
    "taskId": "584f70085b5700ea1d556f758a4556646529ad65d3da7819",
    "member": "TDN",
    "pccvId": "D09-TDN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-21T03:54:06.783Z",
    "base": "c1f90bc0787a269c1afdabe1594e16fbea91838d",
    "files": [
      "services/order/D09_TDN_EVIDENCE.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "5ae6e7b9f2bb2fc3944f744a0a16f648417c67b96326cd4c:code",
    "taskId": "5ae6e7b9f2bb2fc3944f744a0a16f648417c67b96326cd4c",
    "member": "DMN",
    "pccvId": "D08-DMN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T16:34:23.335Z",
    "base": "c42546329ef8b92c51847b5fd75eea4f246ff220",
    "files": [
      "services/catalog/src/main/java/vn/edu/uit/nt533/catalog/CatalogBenchController.java"
    ],
    "tests": [
      {
        "program": "mvn",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "5c9cf480b52f4fee120f8afa9bd1e4529d6e5ccc8a69ed69:code",
    "taskId": "5c9cf480b52f4fee120f8afa9bd1e4529d6e5ccc8a69ed69",
    "member": "TTN",
    "pccvId": "D03-TTN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T12:01:40.943Z",
    "base": "79b1637e6cf19825078fc4d02d61c07ad4105dd3",
    "files": [
      "observability/prometheus.yml",
      "services/inventory/src/test/java/vn/edu/uit/nt533/inventory/InventoryActuatorTest.java"
    ],
    "tests": [
      {
        "program": "mvn",
        "exitCode": 1
      },
      {
        "program": "mvn",
        "exitCode": 0
      },
      {
        "program": "promtool",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "6ec53ea01d438a5a374b42c99112e65cd5c4b3ef64ff0c51:code",
    "taskId": "6ec53ea01d438a5a374b42c99112e65cd5c4b3ef64ff0c51",
    "member": "HXN",
    "pccvId": "D01-HXN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-17T08:57:44.366Z",
    "base": "8459d8257b94fc81d8acaa433a9098c7ef92a54e",
    "files": [],
    "tests": [
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 1
      },
      {
        "program": "git",
        "exitCode": 2
      },
      {
        "program": "python3",
        "exitCode": 1
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 2
      },
      {
        "program": "python3",
        "exitCode": 1
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 2
      },
      {
        "program": "python3",
        "exitCode": 1
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 2
      },
      {
        "program": "python3",
        "exitCode": 1
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 2
      },
      {
        "program": "python3",
        "exitCode": 1
      },
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "7037a610a2f182341a70c308f2f751dece4ca4793d53bbcf:code",
    "taskId": "7037a610a2f182341a70c308f2f751dece4ca4793d53bbcf",
    "member": "TTN",
    "pccvId": "D06-TTN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T12:58:16.157Z",
    "base": "5f1432abb299caa079a7da89a61bbf521ef73932",
    "files": [
      "observability/grafana/dashboards.yml",
      "observability/grafana/datasource.yml",
      "observability/tests/test_window.py",
      "observability/window.py"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "7180de16b2f2537b8b2e20c07f941ca91d4dc3019c5413cb:code",
    "taskId": "7180de16b2f2537b8b2e20c07f941ca91d4dc3019c5413cb",
    "member": "TDN",
    "pccvId": "D10-TDN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-21T04:52:36.001Z",
    "base": "4aa69bcf1bfa1c1d609ec637e5bf2a10c5d24f15",
    "files": [
      "services/order/D10_TDN_EVIDENCE.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "758383a836a60fc3f6133f4b4543a22aef2745fbcea5b2ff:code",
    "taskId": "758383a836a60fc3f6133f4b4543a22aef2745fbcea5b2ff",
    "member": "DHN",
    "pccvId": "D03-DHN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T12:03:36.346Z",
    "base": "dfb2c4f649ac6c265f25fe2d497ddfae9aac71dd",
    "files": [
      "infra/compose/compose.yaml",
      "infra/compose/nginx.conf"
    ],
    "tests": [
      {
        "program": "docker",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "7586ef1be61b73424182023ce545debc6bfac3018aac6a53:code",
    "taskId": "7586ef1be61b73424182023ce545debc6bfac3018aac6a53",
    "member": "HXN",
    "pccvId": "D11-HXN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-21T05:30:46.208Z",
    "base": "e4eca24505a011c10bb0d776517b5293c881edf3",
    "files": [
      "experiments/D11_HXN_EVIDENCE.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "772df110efe9de3a8b7dcc614e99c26af633dd68b74204ae:code",
    "taskId": "772df110efe9de3a8b7dcc614e99c26af633dd68b74204ae",
    "member": "DMN",
    "pccvId": "D10-DMN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-21T04:45:46.608Z",
    "base": "9eb41f03c57a997f68cc4085ef8863f7cc35c1dd",
    "files": [
      "services/catalog/D10_DMN_EVIDENCE.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "78629fb949499a64f0ac0c00a669f0c2e6099ac76698809e:code",
    "taskId": "78629fb949499a64f0ac0c00a669f0c2e6099ac76698809e",
    "member": "TDN",
    "pccvId": "D08-TDN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-21T02:50:54.403Z",
    "base": "fa4cc10f060fd72049279efba521258a7e5fa34e",
    "files": [
      "services/order/D08_PROTOCOL_LOCK.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "78e4160bb00160bd63cac39708a36367a8f4073ac7903d98:code",
    "taskId": "78e4160bb00160bd63cac39708a36367a8f4073ac7903d98",
    "member": "HXN",
    "pccvId": "D04-HXN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T12:35:47.854Z",
    "base": "89505188bbd010678ca51f86a387202ad3fc5dfb",
    "files": [
      "analysis/tests/test_trace.py",
      "analysis/trace.py"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "7a3c724b023cd720442563a6741cf1bf4984495ff0b5be18:code",
    "taskId": "7a3c724b023cd720442563a6741cf1bf4984495ff0b5be18",
    "member": "HXN",
    "pccvId": "D10-HXN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-21T04:34:06.570Z",
    "base": "73527c525c4b2130adb57efc249f84e6f1b2fdcc",
    "files": [
      "experiments/D10_HXN_EVIDENCE.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "7d29538dc8656b6c8c651518540a128481e8daf2341539d0:code",
    "taskId": "7d29538dc8656b6c8c651518540a128481e8daf2341539d0",
    "member": "DHN",
    "pccvId": "D02-DHN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T04:59:54.946Z",
    "base": "fe64bceeb078c8e4962bdb8789fe2462f29b335d",
    "files": [
      "infra/Dockerfile",
      "infra/compose/compose.yaml",
      "infra/compose/nginx.conf"
    ],
    "tests": [
      {
        "program": "docker",
        "exitCode": 0
      },
      {
        "program": "curl",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "89e00a555775e2fb6a6d2f88e9b4586349b197ade9867be9:code",
    "taskId": "89e00a555775e2fb6a6d2f88e9b4586349b197ade9867be9",
    "member": "DMN",
    "pccvId": "D09-DMN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-21T03:45:54.068Z",
    "base": "21376b7d5e73ddf46b3e69da74502bd17c0b0b42",
    "files": [
      "services/catalog/D09_DMN_EVIDENCE.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "8fd6c6bb3b7a97206a4d4870500e999cec58d708f85d54de:code",
    "taskId": "8fd6c6bb3b7a97206a4d4870500e999cec58d708f85d54de",
    "member": "DMN",
    "pccvId": "D03-DMN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T09:57:08.171Z",
    "base": "96068aee2d23bef76ff973765930234ae2bbe273",
    "files": [
      "services/catalog/.dockerignore",
      "services/catalog/Dockerfile",
      "services/catalog/docker_smoke_test.py"
    ],
    "tests": [
      {
        "program": "bash",
        "exitCode": 0
      },
      {
        "program": "bash",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      },
      {
        "program": "docker",
        "exitCode": 127
      },
      {
        "program": "cat",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "docker",
        "exitCode": 127
      },
      {
        "program": "mvn",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "rg",
        "exitCode": 127
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "docker",
        "exitCode": 127
      },
      {
        "program": "mvn",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "rg",
        "exitCode": 127
      },
      {
        "program": "docker",
        "exitCode": 127
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "docker",
        "exitCode": 127
      },
      {
        "program": "mvn",
        "exitCode": 1
      },
      {
        "program": "bash",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "docker",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "9619cf5adffc7569e80a0f30752a85aca81d84986cc40cca:code",
    "taskId": "9619cf5adffc7569e80a0f30752a85aca81d84986cc40cca",
    "member": "TTN",
    "pccvId": "D05-TTN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T12:47:03.123Z",
    "base": "3b0b76a3fa94bbc216fdfc798480d69b2fe7d316",
    "files": [
      "observability/dashboard.json",
      "services/inventory/src/main/java/vn/edu/uit/nt533/inventory/RequestMetadataFilter.java",
      "services/inventory/src/test/java/vn/edu/uit/nt533/inventory/InventoryActuatorTest.java",
      "observability/COUNTERS.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "99bc49d85bc9cc024b7de3474574d07a2f07f81b98c3ac61:code",
    "taskId": "99bc49d85bc9cc024b7de3474574d07a2f07f81b98c3ac61",
    "member": "DHN",
    "pccvId": "D10-DHN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-21T04:31:26.791Z",
    "base": "a7d2a8940871565e850a4a9a10e87d487dde6c9c",
    "files": [
      "infra/D10_DHN_EVIDENCE.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "9b5ccb469808a7cac917e00996134bf7a0d417b4ed70d361:code",
    "taskId": "9b5ccb469808a7cac917e00996134bf7a0d417b4ed70d361",
    "member": "DMN",
    "pccvId": "D02-DMN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T04:31:48.309Z",
    "base": "856ebb0e017acc008d3fe016f6bca30ae846fd63",
    "files": [
      "services/catalog/.gitignore",
      "services/catalog/.mvn/wrapper/maven-wrapper.properties",
      "services/catalog/mvnw",
      "services/catalog/mvnw.cmd",
      "services/catalog/pom.xml",
      "services/catalog/src/main/java/vn/edu/uit/nt533/catalog/CatalogApplication.java",
      "services/catalog/src/main/java/vn/edu/uit/nt533/catalog/CatalogController.java",
      "services/catalog/src/main/java/vn/edu/uit/nt533/catalog/CatalogException.java",
      "services/catalog/src/main/java/vn/edu/uit/nt533/catalog/CatalogExceptionHandler.java",
      "services/catalog/src/main/java/vn/edu/uit/nt533/catalog/CatalogFixtureStore.java",
      "services/catalog/src/main/java/vn/edu/uit/nt533/catalog/Product.java",
      "services/catalog/src/main/java/vn/edu/uit/nt533/catalog/RequestMetadata.java",
      "services/catalog/src/main/java/vn/edu/uit/nt533/catalog/RequestMetadataFilter.java",
      "services/catalog/src/main/resources/application.properties",
      "services/catalog/src/main/resources/catalog-products.json",
      "services/catalog/src/test/java/vn/edu/uit/nt533/catalog/CatalogFixtureStoreTest.java",
      "services/catalog/src/test/java/vn/edu/uit/nt533/catalog/CatalogHttpTest.java"
    ],
    "tests": [
      {
        "program": "bash",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "rg",
        "exitCode": 127
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "bash",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      },
      {
        "program": "bash",
        "exitCode": 1
      },
      {
        "program": "bash",
        "exitCode": 0
      },
      {
        "program": "bash",
        "exitCode": 0
      },
      {
        "program": "bash",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "bash",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "bash",
        "exitCode": 0
      },
      {
        "program": "bash",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 1
      },
      {
        "program": "mvn",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "bash",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "bash",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 1
      },
      {
        "program": "bash",
        "exitCode": 126
      },
      {
        "program": "bash",
        "exitCode": 0
      },
      {
        "program": "bash",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 128
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "bash",
        "exitCode": 0
      },
      {
        "program": "bash",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "9c601301c3569281daeb0fa004e53de710802e4917abfbd2:code",
    "taskId": "9c601301c3569281daeb0fa004e53de710802e4917abfbd2",
    "member": "DMN",
    "pccvId": "D05-DMN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T12:43:57.699Z",
    "base": "81fe46c2fffb6fb6ea697aca77ce866757bdb6e3",
    "files": [
      "services/catalog/src/main/java/vn/edu/uit/nt533/catalog/RequestMetadataFilter.java",
      "services/catalog/src/test/java/vn/edu/uit/nt533/catalog/CatalogFixtureStoreTest.java",
      "services/catalog/WORKLOAD.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "b634393e9071ef8858b3fffab773e21536cd3418be5b803a:code",
    "taskId": "b634393e9071ef8858b3fffab773e21536cd3418be5b803a",
    "member": "TDN",
    "pccvId": "D04-TDN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T12:30:33.957Z",
    "base": "baf4ca180dd3955bea66bcda1bdc94fffef1708e",
    "files": [
      "services/order/src/main/java/vn/edu/uit/nt533/order/QuoteService.java",
      "services/order/src/test/java/vn/edu/uit/nt533/order/OrderHttpTest.java"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "b9513e18f4738431f4ff86b37a604f2fa1aa6f59a276cef9:code",
    "taskId": "b9513e18f4738431f4ff86b37a604f2fa1aa6f59a276cef9",
    "member": "TTN",
    "pccvId": "D01-TTN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-17T07:39:35.789Z",
    "base": "c73d70eac79395d2bbf83821acbe31d592150381",
    "files": [],
    "tests": [
      {
        "program": "bash",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 1
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 2
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "c5ebfaa9ec5eddb107f4d213df3def27ff1c3e57123af3d2:code",
    "taskId": "c5ebfaa9ec5eddb107f4d213df3def27ff1c3e57123af3d2",
    "member": "HXN",
    "pccvId": "D05-HXN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T12:51:07.076Z",
    "base": "c8a94fad90bdc4b1503465f8f06b9324262a41bb",
    "files": [
      "analysis/run.py",
      "analysis/tests/test_run.py",
      "experiments/manifest.schema.json",
      "load-tests/workload.js"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "k6",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "c82a077a068d32b6f848d380e963a4af97cd76c2b7ce1293:code",
    "taskId": "c82a077a068d32b6f848d380e963a4af97cd76c2b7ce1293",
    "member": "DHN",
    "pccvId": "D05-DHN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T12:49:10.705Z",
    "base": "bb7dcb08010d5cbae95d5b6841f8fe0ff933b410",
    "files": [
      "infra/compose/nginx.conf",
      "infra/routing.py",
      "infra/tests/test_routing.py",
      "infra/compose/lab.conf.tpl",
      "infra/tests/lab_smoke.py"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "c9fdc6f55bf3342744f84b39dc62eba6e79e03c8aeaedd1d:code",
    "taskId": "c9fdc6f55bf3342744f84b39dc62eba6e79e03c8aeaedd1d",
    "member": "HXN",
    "pccvId": "D09-HXN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-21T03:40:49.010Z",
    "base": "e849861d8a735d04139f68155df3ccce913a34c4",
    "files": [
      "experiments/D09_HXN_EVIDENCE.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "ce3786dbe1ef5b7c948cd6ad27cc26cd62e27fa5ffc676ad:code",
    "taskId": "ce3786dbe1ef5b7c948cd6ad27cc26cd62e27fa5ffc676ad",
    "member": "DMN",
    "pccvId": "D06-DMN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T13:05:03.821Z",
    "base": "9289aa4fecbb1d9d6a156e880acce26ec88bc01d",
    "files": [
      "services/catalog/analysis-tests/test_metrics.py"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "cfc4a3c4b70587b3302c92c22cb1cba30bb5779345273844:code",
    "taskId": "cfc4a3c4b70587b3302c92c22cb1cba30bb5779345273844",
    "member": "TDN",
    "pccvId": "D01-TDN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-17T08:57:44.377Z",
    "base": "8459d8257b94fc81d8acaa433a9098c7ef92a54e",
    "files": [],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "pwd",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "rg",
        "exitCode": 127
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 2
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "d4e480e540eb126d4515e20307e876d528da62ed615ed395:code",
    "taskId": "d4e480e540eb126d4515e20307e876d528da62ed615ed395",
    "member": "TTN",
    "pccvId": "D09-TTN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-21T03:48:47.629Z",
    "base": "d43cb515ff81ab33b4d8db9b54c43cfce15ef462",
    "files": [
      "observability/D09_TTN_EVIDENCE.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "de613e7941c17fe4c90d71eea9ce6909d785d3b14e6c4cd5:code",
    "taskId": "de613e7941c17fe4c90d71eea9ce6909d785d3b14e6c4cd5",
    "member": "DMN",
    "pccvId": "D04-DMN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T12:24:06.606Z",
    "base": "cc1cb9f1e6fd7b3b4b1353f8aba091376f4b63c5",
    "files": [
      "services/catalog/src/test/java/vn/edu/uit/nt533/catalog/CatalogHttpTest.java",
      "services/catalog/src/main/java/vn/edu/uit/nt533/catalog/CatalogBenchController.java",
      "services/catalog/src/test/java/vn/edu/uit/nt533/catalog/CatalogBenchTest.java"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "deb01fe457f32de21a1ea663d7d5568b275bd2941eea18a1:code",
    "taskId": "deb01fe457f32de21a1ea663d7d5568b275bd2941eea18a1",
    "member": "DHN",
    "pccvId": "D06-DHN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T13:00:14.863Z",
    "base": "8cf4c47d7911bde0b12331ae600f56e462bf1fc7",
    "files": [
      "infra/compose/compose.yaml",
      "infra/compose/lab.conf.tpl",
      "infra/compose/nginx.conf",
      "infra/routing.py",
      "infra/tests/test_routing.py",
      "infra/compose/mapping.yaml",
      "infra/fault.py"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "e05277ac8a024131eff87bf1f9b4b19fb3a2cd8dd64bc41c:code",
    "taskId": "e05277ac8a024131eff87bf1f9b4b19fb3a2cd8dd64bc41c",
    "member": "TDN",
    "pccvId": "D06-TDN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T13:08:03.348Z",
    "base": "b0f7b14bd1f8ed2d2f0120684971094bdcd2b851",
    "files": [
      "services/order/ARCHITECTURE.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "e8a28ee8ee8416a5288b1d05496380a739cd5e538175dd24:code",
    "taskId": "e8a28ee8ee8416a5288b1d05496380a739cd5e538175dd24",
    "member": "TDN",
    "pccvId": "D07-TDN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T13:23:10.047Z",
    "base": "179c844b3724b0a444f132079cfba4d67b9e12eb",
    "files": [
      "services/order/FEATURE_FREEZE.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "e9016887071f65d1dc81ea81679494ceb7c601cebbc12ee7:code",
    "taskId": "e9016887071f65d1dc81ea81679494ceb7c601cebbc12ee7",
    "member": "HXN",
    "pccvId": "D03-HXN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T12:09:15.488Z",
    "base": "025991c0564c70f69bc2965a074453e00a2e6e35",
    "files": [
      "analysis/analyze.py",
      "analysis/tests/__init__.py",
      "analysis/tests/test_analyze.py"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "ec63dd3891f3096ff6e9963d5332635c7fc5c5aa7e9a827a:code",
    "taskId": "ec63dd3891f3096ff6e9963d5332635c7fc5c5aa7e9a827a",
    "member": "TTN",
    "pccvId": "D02-TTN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T04:59:54.955Z",
    "base": "fe64bceeb078c8e4962bdb8789fe2462f29b335d",
    "files": [
      "services/inventory/.gitignore",
      "services/inventory/.mvn/wrapper/maven-wrapper.properties",
      "services/inventory/mvnw",
      "services/inventory/mvnw.cmd",
      "services/inventory/pom.xml",
      "services/inventory/src/main/java/vn/edu/uit/nt533/inventory/InventoryApplication.java",
      "services/inventory/src/main/java/vn/edu/uit/nt533/inventory/InventoryController.java",
      "services/inventory/src/main/java/vn/edu/uit/nt533/inventory/InventoryException.java",
      "services/inventory/src/main/java/vn/edu/uit/nt533/inventory/InventoryExceptionHandler.java",
      "services/inventory/src/main/java/vn/edu/uit/nt533/inventory/RequestMetadata.java",
      "services/inventory/src/main/java/vn/edu/uit/nt533/inventory/RequestMetadataFilter.java",
      "services/inventory/src/main/resources/application.properties",
      "services/inventory/src/main/resources/inventory-stock.json",
      "services/inventory/src/test/java/vn/edu/uit/nt533/inventory/InventoryHttpTest.java"
    ],
    "tests": [
      {
        "program": "mvn",
        "exitCode": 0
      },
      {
        "program": "curl",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "ef72864aeabac39d94febc0692d94c3eb38f89c8884cde8b:code",
    "taskId": "ef72864aeabac39d94febc0692d94c3eb38f89c8884cde8b",
    "member": "DHN",
    "pccvId": "D01-DHN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-17T08:57:44.384Z",
    "base": "8459d8257b94fc81d8acaa433a9098c7ef92a54e",
    "files": [],
    "tests": [
      {
        "program": "bash",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 1
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 1
      },
      {
        "program": "python3",
        "exitCode": 1
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "host-inventory",
        "exitCode": 0
      },
      {
        "program": "host-inventory",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "f4148c2a72d3045fb6b131cfda0f46fa0bfda30261984a7e:code",
    "taskId": "f4148c2a72d3045fb6b131cfda0f46fa0bfda30261984a7e",
    "member": "TDN",
    "pccvId": "D05-TDN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T12:53:54.765Z",
    "base": "2c07af9acc6ee51b08e06270a9db34bf97df85ae",
    "files": [
      "services/order/src/main/java/vn/edu/uit/nt533/order/QuoteService.java",
      "services/order/src/main/java/vn/edu/uit/nt533/order/RequestMetadataFilter.java",
      "services/order/TRUST_BOUNDARY.md"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "f63eff6bfa681667dc94b2533848dad5509e6c78df925c0b:code",
    "taskId": "f63eff6bfa681667dc94b2533848dad5509e6c78df925c0b",
    "member": "HXN",
    "pccvId": "D02-HXN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T04:59:54.959Z",
    "base": "fe64bceeb078c8e4962bdb8789fe2462f29b335d",
    "files": [
      "load-tests/d2-smoke.js",
      "experiments/d2/smoke-summary.txt"
    ],
    "tests": [
      {
        "program": "k6",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "f75a1c3602e24369f1609e52ff61e0637a3806aa89a601af:code",
    "taskId": "f75a1c3602e24369f1609e52ff61e0637a3806aa89a601af",
    "member": "DMN",
    "pccvId": "D01-DMN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-17T08:57:44.391Z",
    "base": "8459d8257b94fc81d8acaa433a9098c7ef92a54e",
    "files": [],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "pkill",
        "exitCode": 1
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 2
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 1
      },
      {
        "program": "git",
        "exitCode": 2
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 1
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 2
      },
      {
        "program": "python3",
        "exitCode": 1
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 1
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 2
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 1
      },
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "f897a6dcb47efc0d8f83ef8edfa3498e94094c4d8fb372d4:code",
    "taskId": "f897a6dcb47efc0d8f83ef8edfa3498e94094c4d8fb372d4",
    "member": "HXN",
    "pccvId": "D06-HXN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T13:02:08.978Z",
    "base": "ae5470113f055c38b32e701db41e62ae26988be2",
    "files": [
      "analysis/trace.py",
      "analysis/mapping.py",
      "analysis/tests/test_mapping.py"
    ],
    "tests": [
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  },
  {
    "id": "fea7088e3f7d17aa1e6d24473a9892193f9e597bc98662a6:code",
    "taskId": "fea7088e3f7d17aa1e6d24473a9892193f9e597bc98662a6",
    "member": "TDN",
    "pccvId": "D03-TDN",
    "state": "VERIFIED_PENDING_MERGE",
    "recordedAt": "2026-11-18T12:06:07.989Z",
    "base": "adc88a2fa2d424aae9f90b3ebcd2d5bae3e655b9",
    "files": [
      "services/order/src/test/java/vn/edu/uit/nt533/order/OrderHttpTest.java"
    ],
    "tests": [
      {
        "program": "mvn",
        "exitCode": 0
      },
      {
        "program": "git",
        "exitCode": 0
      },
      {
        "program": "python3",
        "exitCode": 0
      },
      {
        "program": "mvn",
        "exitCode": 0
      }
    ],
    "remoteJobs": []
  }
]
```
<!-- NT533_PROGRESS_END -->