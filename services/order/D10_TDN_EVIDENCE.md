# D10-TDN · Thảo luận theo hai contrast đã đăng ký

Protocol `nt533-q05-remote-v4`, topology `remote-zerotier` (giữ đầy đủ p95/p99 LOADGEN & NGINX cùng telemetry WAN RTT/jitter/loss theo Q07).

B2/H: lc trừ rr, mean p95 -866 ms, CI95% [-1868.2, -14.2] ms.

A3/uniform: ch-id trừ iph, mean p95 -0.2 ms, CI95% [-0.6, 0] ms.

A3 đo tác dụng đổi khóa dưới NAT. Phần kiểm riêng consistent ring thuộc A4 và dùng GH-ID làm đối chứng cùng khóa. Chỉ diễn giải hiệu ứng khi đồng thời xét p95, throughput và error theo Q05.

SHA-256 ledger: `1765bbc38bde882ac17da8ab4c33532c0947acad88533b7689f50ac59d1d5d64`
