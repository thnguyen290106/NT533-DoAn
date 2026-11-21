# D09-DMN · Đối chiếu B0, B1 và B4

Protocol `nt533-q05-remote-v4`, topology `remote-zerotier` (giữ đầy đủ p95/p99 LOADGEN & NGINX cùng telemetry WAN RTT/jitter/loss theo Q07).

| Case | Lượt | LOADGEN p95 median (ms) | NGINX p95 median (ms) |
|---|---:|---:|---:|
| B0 | 6 | 203.50 | 187.50 |
| B1 | 18 | 118.50 | 98.50 |
| B2 | 18 | 227.00 | 202.00 |
| B3 | 9 | 3043.00 | 2287.00 |
| B4 | 3 | 231.00 | N/A |

B0/B1/B4 dùng cùng họ input với N đã khóa. B4 đi qua kết nối riêng đến C1, không sử dụng NGINX ingress (p95/p99 NGINX là N/A). Dùng kết quả này để chẩn đoán đường đi, không suy ra chi phí proxy thuần.

SHA-256 ledger: `1807334fa548507cc300ca5164677416df087ea11cc3f82da08da8c819b4ddf4`
