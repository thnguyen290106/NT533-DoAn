# D7 dry-run

Run the small B3 Quote trace with the runner on LOADGEN. Use a new attempt ID each time. Supply the deployed revision, image digests, configuration hash and protocol hash recorded by the lab operator. The bounded public Quote dry run accepts at most 12 requests. The public gateway assigns the IDs that are recorded in the result. Benchmark profiles and campaign runs use the protected lab listener.

```bash
python3 -m analysis.run trace.csv plan.json facts.json results/B3-smoke-RR-b1-UTC-a1
python3 -m analysis.chart results/B3-smoke-RR-b1-UTC-a1 --instances O1,O2,O3
(cd results/B3-smoke-RR-b1-UTC-a1 && sha256sum -c SHA256SUMS)
```

The runner keeps stdout, stderr, numeric exit status, the manifest and raw data for each attempt. The chart requires a valid manifest and verifies source hashes before analysis. Its summary points to the original request and k6 raw checksums. Keep invalid attempts under their original IDs. Dry-run samples validate the path and format and are separate from campaign data.
