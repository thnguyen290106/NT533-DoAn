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







<!-- NT533_PROGRESS_BEGIN v1 -->
```json
[
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