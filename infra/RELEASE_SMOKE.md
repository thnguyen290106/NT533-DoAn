# G2 routing smoke and cleanup

Render RR, LC, IPH, CH-ID and GH-ID from the same base. Validate each with `nginx -t` and run a short gate against the same Inventory image. Require selection only within active membership. CH-ID/GH-ID must map each repeated key consistently. Test the 3→4→3 configuration separately and verify the 3-member mapping returns to its initial value.

Reject missing or malformed client IDs and untrusted peers on the lab ingress. Keep that listener out of the default public deployment. Check the observed peer IP, effective IP and generation in NGINX logs.

Run the smoke in a uniquely labelled disposable Docker network, record the exact containers it creates, and remove just those resources when it exits. Check the inventory of resources under that label when cleanup completes. Keep evidence outside the disposable network.
