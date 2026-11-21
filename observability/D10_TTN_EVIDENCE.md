# D10-TTN · Delay I3 và phân phối hot-ID

Protocol `nt533-q05-remote-v4`, topology `remote-zerotier` (giữ đầy đủ p95/p99 LOADGEN & NGINX cùng telemetry WAN RTT/jitter/loss theo Q07).

Có 9 lượt A1 kiểm contract applied delay theo từng instance, với I3 thêm 300 ms. Các lượt A3 ghi log theo profile mixed-delay và giữ riêng uniform/hot-ID. Metrics theo instance và time series nằm cùng archive HOST của từng lượt.

SHA-256 ledger: `1765bbc38bde882ac17da8ab4c33532c0947acad88533b7689f50ac59d1d5d64`
