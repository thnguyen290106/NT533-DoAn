# D09-TTN · Cửa sổ B2 và JVM

Protocol `nt533-q05-remote-v4`, topology `remote-zerotier` (giữ đầy đủ p95/p99 LOADGEN & NGINX cùng telemetry WAN RTT/jitter/loss theo Q07).

Kho đo giữ counter Prometheus, GC, CPU và bộ nhớ theo bước 5 s cùng dấu thời gian của từng lượt. B2 có 18 lượt và overload hợp lệ vẫn xuất hiện trong bảng kiểm. Diễn giải error/latency theo cohort bắt đầu trong measure và throughput theo completion-window.

SHA-256 ledger: `1807334fa548507cc300ca5164677416df087ea11cc3f82da08da8c819b4ddf4`
