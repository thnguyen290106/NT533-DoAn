# D11-DHN · Stop/start I3 và membership A4

Protocol `nt533-q05-remote-v4`, topology `remote-zerotier` (giữ đầy đủ p95/p99 LOADGEN & NGINX cùng telemetry WAN RTT/jitter/loss theo Q07).

- A2-M-lc-b1-20261121T045517956Z-a1 · stop 2026-11-21T04:55:47.710191Z · start 2026-11-21T04:55:57.699445Z · ready 2026-11-21T04:56:26.852827Z · recovery N/A
- A2-M-iph-b1-20261121T045647535Z-a1 · stop 2026-11-21T04:57:17.176605Z · start 2026-11-21T04:57:27.215720Z · ready 2026-11-21T04:57:57.296694Z · recovery N/A
- A2-M-rr-b1-20261121T045817093Z-a1 · stop 2026-11-21T04:58:46.835642Z · start 2026-11-21T04:58:56.836596Z · ready 2026-11-21T04:59:26.729683Z · recovery N/A
- A2-M-iph-b2-20261121T045946791Z-a1 · stop 2026-11-21T05:00:16.476214Z · start 2026-11-21T05:00:26.542203Z · ready 2026-11-21T05:00:57.231658Z · recovery N/A
- A2-M-lc-b2-20261121T050116853Z-a1 · stop 2026-11-21T05:01:46.494537Z · start 2026-11-21T05:01:56.593725Z · ready 2026-11-21T05:02:25.662976Z · recovery N/A
- A2-M-rr-b2-20261121T050246714Z-a1 · stop 2026-11-21T05:03:16.330244Z · start 2026-11-21T05:03:26.404521Z · ready 2026-11-21T05:03:57.958368Z · recovery N/A
- A2-M-rr-b3-20261121T050416552Z-a1 · stop 2026-11-21T05:04:46.307814Z · start 2026-11-21T05:04:56.306435Z · ready 2026-11-21T05:05:26.321872Z · recovery N/A
- A2-M-lc-b3-20261121T050546441Z-a1 · stop 2026-11-21T05:06:15.970708Z · start 2026-11-21T05:06:25.999870Z · ready 2026-11-21T05:06:58.269526Z · recovery N/A
- A2-M-iph-b3-20261121T050716520Z-a1 · stop 2026-11-21T05:07:46.115413Z · start 2026-11-21T05:07:56.090479Z · ready 2026-11-21T05:08:24.771426Z · recovery N/A

A4 đối chiếu 30 snapshot theo chuỗi 3→4→3 cho 10 cặp seed/variant. Container và endpoint I1–I3 giữ nguyên trong từng chuỗi. Lệnh cấu hình kiểm generation trước sweep và dừng I4 sau khi trả membership về 3.

SHA-256 ledger: `cacdf38e99c45e9894171836da0eb1c8719a127d9a670b3e317fd869a8c5b32c`
