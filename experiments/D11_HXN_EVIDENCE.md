# D11-HXN · Khóa G4 với 104 lượt và 60 sweep

Protocol `nt533-q05-remote-v4`, topology `remote-zerotier` (giữ đầy đủ p95/p99 LOADGEN & NGINX cùng telemetry WAN RTT/jitter/loss theo Q07).

| Run ID | Profile | Algorithm | Error | LOADGEN p95/p99 ms | NGINX p95/p99 ms | RTT p95 ms | Jitter ms | Loss |
|---|---|---|---:|---:|---:|---:|---:|---:|
| A2-M-lc-b1-20261121T045517956Z-a1 | mixed-delay | lc | 16.02% | 215.00 / 263.00 | 202.00 / 202.00 | 14.60 | 3.24 | 0/71 |
| A2-M-iph-b1-20261121T045647535Z-a1 | mixed-delay | iph | 16.30% | 216.00 / 707.00 | 202.00 / 203.00 | 17.90 | 10.77 | 0/71 |
| A2-M-rr-b1-20261121T045817093Z-a1 | mixed-delay | rr | 16.18% | 225.00 / 1465.00 | 202.00 / 203.00 | 17.60 | 19.18 | 1/70 |
| A2-M-iph-b2-20261121T045946791Z-a1 | mixed-delay | iph | 16.65% | 225.00 / 2999.00 | 202.00 / 656.00 | 15.50 | 6.90 | 0/71 |
| A2-M-lc-b2-20261121T050116853Z-a1 | mixed-delay | lc | 15.91% | 217.00 / 263.00 | 202.00 / 203.00 | 17.00 | 13.06 | 0/71 |
| A2-M-rr-b2-20261121T050246714Z-a1 | mixed-delay | rr | 16.60% | 219.00 / 2622.00 | 202.00 / 204.00 | 14.10 | 6.77 | 1/70 |
| A2-M-rr-b3-20261121T050416552Z-a1 | mixed-delay | rr | 16.21% | 216.00 / 318.00 | 202.00 / 203.00 | 13.80 | 1.66 | 0/71 |
| A2-M-lc-b3-20261121T050546441Z-a1 | mixed-delay | lc | 15.80% | 224.00 / 269.00 | 202.00 / 203.00 | 32.70 | 11.26 | 0/71 |
| A2-M-iph-b3-20261121T050716520Z-a1 | mixed-delay | iph | 16.30% | 218.00 / 443.00 | 202.00 / 203.00 | 20.20 | 17.59 | 0/71 |

Có 60.000 request mapping kiểm đủ key và stability giữa hai sweep trong từng snapshot. Archive HOST và LOADGEN có bản sao thứ hai đối chiếu checksum.

SHA-256 ledger: `cacdf38e99c45e9894171836da0eb1c8719a127d9a670b3e317fd869a8c5b32c`
