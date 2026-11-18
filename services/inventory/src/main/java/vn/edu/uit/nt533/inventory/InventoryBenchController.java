package vn.edu.uit.nt533.inventory;

import jakarta.servlet.http.HttpServletRequest;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.http.HttpStatus;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Profile("lab")
@RestController
final class InventoryBenchController {
    private final int extraDelayMs;

    InventoryBenchController(@Value("${nt533.bench.extra-delay-ms:0}") int extraDelayMs,
            @Value("${inventory.instance-id}") String instance) {
        if (extraDelayMs != 0 && (extraDelayMs != 300 || !instance.equals("I3"))) {
            throw new IllegalArgumentException("Only I3 can use the 300 ms fault delay");
        }
        this.extraDelayMs = extraDelayMs;
    }

    @GetMapping("/internal/bench")
    Object bench(@RequestParam MultiValueMap<String, String> query, HttpServletRequest request) {
        RequestMetadata metadata = RequestMetadata.from(request);
        if (query.size() == 1 && List.of("mapping").equals(query.get("profile"))) {
            return new Mapping("mapping", metadata.requestId(), metadata.instanceId());
        }
        if (query.size() != 2 || !List.of("mixed-delay").equals(query.get("profile"))) {
            throw invalid();
        }
        List<String> delay = query.get("delayClass");
        int baseDelay;
        if (List.of("fast").equals(delay)) baseDelay = 20;
        else if (List.of("slow").equals(delay)) baseDelay = 200;
        else throw invalid();
        int applied = baseDelay + extraDelayMs;
        try {
            Thread.sleep(applied);
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt();
            throw new InventoryException(HttpStatus.SERVICE_UNAVAILABLE, "INTERRUPTED", "Benchmark request interrupted");
        }
        return new Delayed("mixed-delay", delay.getFirst(), applied, metadata.requestId(), metadata.instanceId());
    }

    private static InventoryException invalid() {
        return new InventoryException(HttpStatus.BAD_REQUEST, "INVALID_INPUT", "Invalid benchmark profile or query");
    }

    record Mapping(String profile, String requestId, String instanceId) {}
    record Delayed(String profile, String delayClass, int appliedDelayMs, String requestId, String instanceId) {}
}
