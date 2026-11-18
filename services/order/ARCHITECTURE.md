# Architecture and fault review

Catalog owns product identity and integer prices. Inventory owns stock. Both read static fixtures. Order owns Quote validation and arithmetic. It never writes stock or creates an order. NGINX owns public, private and optional lab routing, and Prometheus observes each management endpoint independently.

## One Quote

1. Validate the product and integer quantity. Input failure makes no downstream call.
2. Call Catalog with the Quote request ID and a distinct Catalog call ID. A Catalog 404 ends Quote before Inventory. Malformed DTO or mismatched ID is 502.
3. Call Inventory with a separate call ID. Insufficient stock is 409. A connection refusal or upstream 5xx is 503. A one-second downstream deadline, including body, is 504 and cancels the outstanding future.
4. Return price × quantity in integer VND with Order's instance ID and the same request ID.

## Fault scope and evidence

I3 stop and restoration affect Inventory only. Routing configuration and membership remain constant during A2. Capture container identity, observed stop, restart and readiness with UTC and monotonic clocks. NGINX passive failures and application readiness are separate observations. A recovering target can resume serving before all clients return to baseline. Compute recovery from the stated client cohort, while tracking app, gateway and downstream failure separately.

A1 changes the lab delay on I3. The other two Inventory replicas and all Catalog and Order replicas use unchanged settings. A4 alone changes Inventory membership between three and four; it is a mapping exercise. Neither proves resilience to HOST, NGINX or network failure. Default Compose keeps three Inventory replicas, lab routes disabled and management unexposed. The nominal deployment has one Docker HOST and one NGINX; a failure of either remains a shared fault domain.
