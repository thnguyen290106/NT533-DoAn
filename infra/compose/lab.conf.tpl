    map $http_x_request_id $lab_request_valid {
        default 0;
        "~^[0-9a-f]{32}$" 1;
    }
    map $http_x_lab_client_id $lab_client_valid {
        default 0;
        "~^c-[0-9a-f]{16}$" 1;
    }
    geo $realip_remote_addr $lab_peer_valid {
        default 0;
        @PEER@ 1;
    }
    map $http_x_lab_source_ip $lab_ip_valid {
        default 0;
        "~^10\.(64|65|66|67)\.(0|[1-9][0-9]?|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.10$" 1;
        10.250.0.10 1;
    }
    upstream catalog_lab {
        zone catalog_lab 64k;
        @CATALOG@
        server catalog-1:8080 max_fails=1 fail_timeout=5s;
        server catalog-2:8080 max_fails=1 fail_timeout=5s;
        server catalog-3:8080 max_fails=1 fail_timeout=5s;
        keepalive 32;
    }
    upstream inventory_lab {
        zone inventory_lab 64k;
        @INVENTORY@
        server inventory-1:8080 max_fails=1 fail_timeout=5s;
        server inventory-2:8080 max_fails=1 fail_timeout=5s;
        server inventory-3:8080 max_fails=1 fail_timeout=5s;
        @I4@
        keepalive 32;
    }
    server {
        listen 8081;
        proxy_set_header Host $host;
        proxy_set_header Connection "";
        proxy_set_header X-Request-ID $http_x_request_id;
        proxy_set_header X-Call-ID "";
        proxy_set_header X-Lab-Client-ID "";
        proxy_set_header X-Lab-Source-IP "";
        if ($lab_peer_valid = 0) { return 403; }
        @REAL_IP@
        if ($lab_request_valid = 0) { return 400; }
        if ($lab_client_valid = 0) { return 400; }
        add_header X-NT533-Generation @GENERATION@ always;
        location = /bench/catalog { proxy_pass http://catalog_lab/internal/bench; }
        location = /bench/inventory { proxy_pass http://inventory_lab/internal/bench; }
        location = /api/orders/quote { proxy_pass http://order_rr; }
        location / { return 404; }
    }
