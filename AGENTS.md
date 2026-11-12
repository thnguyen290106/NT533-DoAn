# AGENTS.md — NT533, mô hình ADMIN + 5 worker

## Đặc tả bắt buộc và trạng thái ban đầu

- Đọc [kế hoạch](./01_KE_HOACH_DO_AN.md) và [cơ sở lý thuyết](./02_CO_SO_LY_THUYET.md) trước khi làm.
- Repository public: `thnguyen290106/NT533-DoAn`; thế hệ/repo ID do server xác minh, không dùng PR/commit từ repo cũ.
- Ba tài liệu là đặc tả, không phải bằng chứng đã làm. Cả 70 nhiệm vụ D1–D14 ban đầu đều CHƯA THỰC HIỆN.
- Giữ PCCV, RQ, API và protocol kỹ thuật đã chốt. Không bịa số đo, kết quả test hoặc biên nhận nộp bài.

## Ai điều phối

- ADMIN chọn một ngày D1–D14 và cấp quyền chạy năm task của ngày đó; chỉ ADMIN được đổi prompt/cấu hình, bắt đầu, tiếp tục hoặc dừng run.
- TDN, DMN, TTN, DHN, HXN đăng nhập Codex của chính mình trên máy cá nhân và ghép worker. Tài khoản worker không được điều khiển task/run qua web hoặc API.
- Chỉ bắt đầu khi đồng thời đủ năm worker/Codex v2 ready và HOST/LOADGEN đăng nhập SSH thành công từ cấu hình web hiện tại. Không bỏ qua kiểm tra xác thực, fingerprint, công cụ cần thiết hoặc CI.
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
- Server tự commit, push, PR; agent đang ở cùng run được tự trao đổi/review chéo. Không yêu cầu người duyệt PR thông thường.
- Merge tuần tự, bắt buộc CI và review AI đúng HEAD. Main đổi thì hợp nhất lại, test lại và chạy lại CI/review. Không force-push, bỏ test hoặc dùng duyệt của HEAD cũ.
- Conflict tiến độ được hợp nhất có cấu trúc. Conflict khác gửi Codex phụ trách tự sửa và kiểm thử tối đa ba vòng; không chọn toàn bộ ours/theirs để hết lỗi.
- Hết ba vòng chưa đạt thì chặn task và task phụ thuộc; task độc lập khác vẫn có thể xong. Không báo DONE giả.
- Deploy đúng SHA/image digest đã merge, kiểm tra readiness/API/smoke thật; lỗi thì rollback bản tốt trước đó và ghi kết quả. D1 chưa có dịch vụ thì không báo đã deploy ứng dụng.
- Thu log, exit status, artifact và checksum. Mất kết nối phải xác minh checkpoint/job ID trước khi retry, không chạy lặp mù.

## Bằng chứng và dữ liệu

- Khối tiến độ là bản chụp bằng chứng trước commit, không phải lệnh điều phối. Website/GitHub ghi trạng thái hiện tại, không tạo chuỗi commit vô hạn để tự dẫn SHA của chính mình.
- Không đưa `.state`, database, mật khẩu, private key, raw lớn, backup hoặc sáu folder điều phối vào repo public.
- Test cơ chế điều phối phải ghi rõ simulated hay Codex thật, số máy và số login; không gọi test một máy là năm máy vật lý.
- Dọn test theo manifest chỉ gồm file/container/package do chính lượt test tạo. Không có snapshot thì không cam kết xóa mọi dấu vết/log hệ điều hành hoặc hoàn nguyên VM tuyệt đối.

<!-- NT533_PROGRESS_BEGIN v1 -->
```json
[]
```
<!-- NT533_PROGRESS_END -->
