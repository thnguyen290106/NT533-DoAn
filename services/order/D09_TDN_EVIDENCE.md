# D09-TDN · Phương pháp và đối chiếu Quote B3

Protocol `nt533-q05-remote-v4`, topology `remote-zerotier` (giữ đầy đủ p95/p99 LOADGEN & NGINX cùng telemetry WAN RTT/jitter/loss theo Q07).

Kiểm tra 9 lượt B3. Mọi Quote thành công trong cửa sổ đo đã nối với hai call-ID downstream trong log HOST. Ingress giữ IP LOADGEN thật. Hai call nội bộ không được cộng vào external RPS.

| Case | Lượt | LOADGEN p95 median (ms) | NGINX p95 median (ms) |
|---|---:|---:|---:|
| B0 | 6 | 203.50 | 187.50 |
| B1 | 18 | 118.50 | 98.50 |
| B2 | 18 | 227.00 | 202.00 |
| B3 | 9 | 3043.00 | 2287.00 |
| B4 | 3 | 231.00 | N/A |

SHA-256 ledger: `1807334fa548507cc300ca5164677416df087ea11cc3f82da08da8c819b4ddf4`
