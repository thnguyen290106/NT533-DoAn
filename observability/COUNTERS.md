# Request counter audit

Select the measurement start and end from the run manifest. The dashboard range is the cohort selected by the operator. Its `increase(nt533_requests_total[$__range])` panels are diagnostic. A run audit must join client, gateway and app records by request ID and, downstream, call ID.

Group by `service`, `instance`, `route`, `status`, and `profile`. Request IDs belong in logs only. On a scrape gap or counter reset, retain the logs and mark the measurement incomplete until both boundaries are verified. Zero traffic and missing telemetry are distinct.

Inventory increments the request counter and observes its timer exactly once per completed request. Readiness and scrapes are outside that count. Count and timer samples use requests and observations, latency buckets use seconds, and the application JSON log uses milliseconds.
