# Catalog benchmark contract

The `lab` Spring profile enables `GET /internal/bench?profile=cpu-fixed`. The public API gateway never routes to this endpoint. The only accepted parameter is a single `profile=cpu-fixed`.

`NT533_BENCH_ITERATIONS` selects one common iteration count for all replicas. A request repeatedly hashes the UTF-8 bytes of `NT533-v1` with SHA-256, passing each binary digest to the next round. The response returns the lowercase checksum and the number of rounds. The default 1,000 is a smoke-test setting. Q05 determines the campaign setting through a separate pilot.

Catalog reads its fixture once and refuses an invalid fixture at startup. The packaged bytes have SHA-256 `bd76926a87fd55258a567c248146ff215632ae323bd276fcc7a76eae227d850e`. Compare each replica's packaged file before recording a run.
