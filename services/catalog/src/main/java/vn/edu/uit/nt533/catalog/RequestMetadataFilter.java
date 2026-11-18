package vn.edu.uit.nt533.catalog;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Tags;
import io.micrometer.core.instrument.Timer;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.time.Duration;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.concurrent.TimeUnit;
import org.slf4j.LoggerFactory;
import java.util.UUID;
import java.util.regex.Pattern;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
final class RequestMetadataFilter extends OncePerRequestFilter {
    private static final String REQUEST_ID = "X-Request-ID";
    private static final String INSTANCE_ID = "X-Instance-ID";
    private static final Pattern REQUEST_ID_PATTERN = Pattern.compile("[0-9a-f]{32}");

    private static final Duration[] BUCKETS = {Duration.ofMillis(5), Duration.ofMillis(10), Duration.ofMillis(20),
            Duration.ofMillis(50), Duration.ofMillis(100), Duration.ofMillis(200), Duration.ofMillis(500),
            Duration.ofSeconds(1), Duration.ofSeconds(2), Duration.ofSeconds(5)};
    private static final Pattern CALL_ID = Pattern.compile("[0-9a-f]{32}-(catalog|inventory)");

    private final String instanceId;
    private final MeterRegistry metrics;
    private final ObjectMapper json;

    RequestMetadataFilter(@Value("${catalog.instance-id}") String instanceId, MeterRegistry metrics, ObjectMapper json) {
        if (!instanceId.matches("C[1-3]")) {
            throw new IllegalArgumentException("Catalog INSTANCE_ID must be C1, C2 or C3");
        }
        this.instanceId = instanceId;
        this.metrics = metrics;
        this.json = json;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain chain) throws ServletException, IOException {
        String requestId = request.getHeader(REQUEST_ID);
        if (requestId == null || !REQUEST_ID_PATTERN.matcher(requestId).matches()) {
            requestId = UUID.randomUUID().toString().replace("-", "");
        }
        new RequestMetadata(requestId, instanceId).attachTo(request);
        response.setHeader(REQUEST_ID, requestId);
        response.setHeader(INSTANCE_ID, instanceId);
        String uri = request.getRequestURI();
        if (!uri.startsWith("/api/") && !uri.equals("/internal/bench")) {
            chain.doFilter(request, response);
            return;
        }
        long started = System.nanoTime();
        boolean completed = false;
        try {
            chain.doFilter(request, response);
            completed = true;
        } finally {
            int status = completed || response.isCommitted() ? response.getStatus() : 0;
            record(request, requestId, route(uri), status, System.nanoTime() - started);
        }
    }

    private void record(HttpServletRequest request, String requestId, String route, int status, long elapsed) {
        String profile = profile(request, route);
        Tags tags = Tags.of("service", "catalog", "instance", instanceId, "route", route,
                "profile", profile, "status", status == 0 ? "aborted" : Integer.toString(status));
        metrics.counter("nt533.requests", tags).increment();
        Timer.builder("nt533.request.duration").tags(tags).serviceLevelObjectives(BUCKETS)
                .register(metrics).record(elapsed, TimeUnit.NANOSECONDS);
        String callId = request.getHeader("X-Call-ID");
        var row = new LinkedHashMap<String, Object>();
        row.put("timestamp_utc", Instant.now().toString());
        row.put("request_id", requestId);
        row.put("call_id", callId != null && CALL_ID.matcher(callId).matches() && callId.startsWith(requestId + "-") ? callId : null);
        row.put("service", "catalog");
        row.put("instance_id", instanceId);
        row.put("route", route);
        row.put("profile", profile);
        row.put("status", status == 0 ? null : status);
        row.put("duration_ms", elapsed / 1_000_000.0);
        try {
            System.out.println(json.writeValueAsString(row));
        } catch (com.fasterxml.jackson.core.JsonProcessingException error) {
            LoggerFactory.getLogger(RequestMetadataFilter.class).warn("Unable to serialize request telemetry");
        }
    }

    private static String route(String uri) {
        if (uri.equals("/api/catalog/products")) return "/api/catalog/products";
        if (uri.matches("/api/catalog/products/[^/]+")) return "/api/catalog/products/{id}";
        if (uri.equals("/internal/bench")) return uri;
        return "unknown";
    }

    private static String profile(HttpServletRequest request, String route) {
        if (!route.equals("/internal/bench")) return "none";
        String profile = request.getParameter("profile");
        return switch (profile == null ? "" : profile) {
            case "cpu-fixed" -> "cpu-fixed";
            default -> "unknown";
        };
    }
}
