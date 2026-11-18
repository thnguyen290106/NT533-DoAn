package vn.edu.uit.nt533.order;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpTimeoutException;
import java.time.Duration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

@Service
final class QuoteService {
    private final HttpClient http = HttpClient.newBuilder()
            .connectTimeout(Duration.ofMillis(200))
            .followRedirects(HttpClient.Redirect.NEVER)
            .build();
    private final ObjectMapper mapper;
    private final String catalog;
    private final String inventory;

    QuoteService(ObjectMapper mapper, @Value("${order.catalog-url}") String catalog,
                 @Value("${order.inventory-url}") String inventory) {
        this.mapper = mapper;
        this.catalog = catalog;
        this.inventory = inventory;
    }

    OrderController.Quote quote(String id, int quantity, RequestMetadata metadata) {
        JsonNode product = load(catalog + "/api/catalog/products/" + id, "catalog", metadata.requestId());
        JsonNode price = product.path("price");
        if (!id.equals(product.path("id").asText()) || !price.isIntegralNumber() || !price.canConvertToLong()
                || price.longValue() <= 0 || !"VND".equals(product.path("currency").asText())) {
            throw badResponse();
        }

        JsonNode stock = load(inventory + "/api/inventory/" + id, "inventory", metadata.requestId());
        JsonNode available = stock.path("availableStock");
        if (!id.equals(stock.path("productId").asText()) || !available.isIntegralNumber()
                || !available.canConvertToInt() || available.intValue() < 0) {
            throw badResponse();
        }
        if (available.intValue() < quantity) {
            throw new OrderException(HttpStatus.CONFLICT, "INSUFFICIENT_STOCK", "Insufficient stock");
        }
        long total;
        try {
            total = Math.multiplyExact(price.longValue(), quantity);
        } catch (ArithmeticException error) {
            throw badResponse();
        }
        return new OrderController.Quote(id, quantity, price.longValue(), total, "VND",
                available.intValue(), metadata.requestId(), metadata.instanceId());
    }

    private JsonNode load(String url, String service, String requestId) {
        HttpRequest request = HttpRequest.newBuilder(URI.create(url))
                .timeout(Duration.ofSeconds(1))
                .header("X-Request-ID", requestId)
                .header("X-Call-ID", requestId + "-" + service)
                .header("Accept", "application/json")
                .GET().build();
        HttpResponse<String> response;
        try {
            response = http.send(request, HttpResponse.BodyHandlers.ofString());
        } catch (HttpTimeoutException error) {
            throw new OrderException(HttpStatus.GATEWAY_TIMEOUT, "DOWNSTREAM_TIMEOUT", "Downstream timed out");
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt();
            throw unavailable();
        } catch (IOException error) {
            throw unavailable();
        }
        int status = response.statusCode();
        if (status == 404 && service.equals("catalog")) {
            throw new OrderException(HttpStatus.NOT_FOUND, "PRODUCT_NOT_FOUND", "Product not found");
        }
        if (status >= 500) {
            throw unavailable();
        }
        if (status != 200) {
            throw badResponse();
        }
        try {
            JsonNode body = mapper.readTree(response.body());
            if (body == null || !body.isObject() || !requestId.equals(body.path("requestId").asText())) {
                throw badResponse();
            }
            return body;
        } catch (IOException error) {
            throw badResponse();
        }
    }

    private static OrderException badResponse() {
        return new OrderException(HttpStatus.BAD_GATEWAY, "DOWNSTREAM_BAD_RESPONSE", "Bad downstream response");
    }

    private static OrderException unavailable() {
        return new OrderException(HttpStatus.SERVICE_UNAVAILABLE, "DOWNSTREAM_UNAVAILABLE", "Downstream unavailable");
    }
}
