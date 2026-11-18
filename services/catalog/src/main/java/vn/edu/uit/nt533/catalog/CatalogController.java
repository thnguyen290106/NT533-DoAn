package vn.edu.uit.nt533.catalog;

import com.fasterxml.jackson.annotation.JsonUnwrapped;
import jakarta.servlet.http.HttpServletRequest;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/catalog/products")
final class CatalogController {
    private final CatalogFixtureStore store;

    CatalogController(CatalogFixtureStore store) {
        this.store = store;
    }

    @GetMapping
    ProductList list(HttpServletRequest request) {
        validateQuery(request);
        RequestMetadata metadata = RequestMetadata.from(request);
        return new ProductList(store.products(), metadata.requestId(), metadata.instanceId());
    }

    @GetMapping("/{id}")
    ProductDetail detail(@PathVariable String id, HttpServletRequest request) {
        validateQuery(request);
        // Spring removes matrix parameters from the bound ID but preserves them in the request URI.
        if (request.getRequestURI().indexOf(';', request.getContextPath().length()) >= 0 || !Product.hasValidId(id)) {
            throw invalidInput();
        }
        Product product = store.find(id)
                .orElseThrow(() -> new CatalogException(
                        HttpStatus.NOT_FOUND, "PRODUCT_NOT_FOUND", "Product not found"));
        RequestMetadata metadata = RequestMetadata.from(request);
        return new ProductDetail(product, metadata.requestId(), metadata.instanceId());
    }

    private static void validateQuery(HttpServletRequest request) {
        String query = request.getQueryString();
        if (query != null && !query.isEmpty()) {
            throw invalidInput();
        }
    }

    private static CatalogException invalidInput() {
        return new CatalogException(HttpStatus.BAD_REQUEST, "INVALID_INPUT", "Invalid request");
    }

    record ProductList(List<Product> products, String requestId, String instanceId) {}

    record ProductDetail(@JsonUnwrapped Product product, String requestId, String instanceId) {}
}
