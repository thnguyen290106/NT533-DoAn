package vn.edu.uit.nt533.order;

import com.fasterxml.jackson.databind.JsonNode;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
final class OrderController {
    private final QuoteService quotes;

    OrderController(QuoteService quotes) {
        this.quotes = quotes;
    }

    @PostMapping(path = "/api/orders/quote", consumes = MediaType.APPLICATION_JSON_VALUE)
    Quote quote(@RequestBody JsonNode body, HttpServletRequest request) {
        String query = request.getQueryString();
        JsonNode productId = body.path("productId");
        JsonNode quantity = body.path("quantity");
        if (!body.isObject() || body.size() != 2 || !productId.isTextual()
                || !productId.textValue().matches("P[0-9]{3}") || !quantity.isIntegralNumber()
                || !quantity.canConvertToInt() || quantity.intValue() < 1 || quantity.intValue() > 10
                || request.getRequestURI().contains(";") || (query != null && !query.isEmpty())) {
            throw new OrderException(HttpStatus.BAD_REQUEST, "INVALID_INPUT", "Invalid request");
        }
        return quotes.quote(productId.textValue(), quantity.intValue(), RequestMetadata.from(request));
    }

    record Quote(String productId, int quantity, long unitPrice, long totalPrice, String currency,
                 int availableStock, String requestId, String instanceId) {}
}
