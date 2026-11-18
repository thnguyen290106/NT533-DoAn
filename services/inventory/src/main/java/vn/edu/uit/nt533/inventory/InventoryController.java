package vn.edu.uit.nt533.inventory;

import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import org.springframework.core.io.ClassPathResource;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

@RestController
final class InventoryController {
    private final Map<String, Integer> fixture;

    InventoryController(ObjectMapper mapper) throws IOException {
        var parser = mapper.copy().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION.mappedFeature());
        try (var input = new ClassPathResource("inventory-stock.json").getInputStream()) {
            JsonNode rows = parser.readTree(input);
            if (rows == null || !rows.isObject() || rows.isEmpty()) {
                throw new IllegalStateException("Invalid inventory fixture");
            }
            Map<String, Integer> stock = new HashMap<>();
            rows.fields().forEachRemaining(entry -> {
                JsonNode value = entry.getValue();
                if (!entry.getKey().matches("P[0-9]{3}") || !value.isIntegralNumber()
                        || !value.canConvertToInt() || value.intValue() < 0) {
                    throw new IllegalStateException("Invalid inventory fixture entry");
                }
                stock.put(entry.getKey(), value.intValue());
            });
            fixture = Map.copyOf(stock);
        }
    }

    @GetMapping("/api/inventory/{productId}")
    Stock stock(@PathVariable String productId, HttpServletRequest request) {
        String query = request.getQueryString();
        if (!productId.matches("P[0-9]{3}") || request.getRequestURI().contains(";")
                || (query != null && !query.isEmpty())) {
            throw new InventoryException(HttpStatus.BAD_REQUEST, "INVALID_INPUT", "Invalid request");
        }
        Integer available = fixture.get(productId);
        if (available == null) {
            throw new InventoryException(HttpStatus.NOT_FOUND, "PRODUCT_NOT_FOUND", "Product not found");
        }
        RequestMetadata metadata = RequestMetadata.from(request);
        return new Stock(productId, available, metadata.requestId(), metadata.instanceId());
    }

    record Stock(String productId, int availableStock, String requestId, String instanceId) {}
}
