# D10-DHN · A1, A3 và bằng chứng effective IP

Protocol `nt533-q05-remote-v4`, topology `remote-zerotier` (giữ đầy đủ p95/p99 LOADGEN & NGINX cùng telemetry WAN RTT/jitter/loss theo Q07).

A3 giữ IP NAT 10.250.0.10 với peer LOADGEN thật. Bốn biến thể trong mỗi block dùng cùng trace checksum theo plan. A1 thay delay trong đúng I3 và reset giữa các lượt.

| Case | Lượt | LOADGEN p95 median (ms) | NGINX p95 median (ms) |
|---|---:|---:|---:|
| A1 | 9 | 514.00 | 501.00 |
| A3 | 28 | 224.50 | 202.00 |
| B2 | 4 | 226.50 | 202.00 |

SHA-256 ledger: `1765bbc38bde882ac17da8ab4c33532c0947acad88533b7689f50ac59d1d5d64`
