package vn.edu.uit.nt533.catalog;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;

@Component
final class CatalogFixtureStore {
    // Q02 invariants checked at startup. All API data comes from the JSON resource.
    private static final List<Product> CONTRACT = List.of(
            new Product("P001", "Ban phim", 100_000, "VND"),
            new Product("P002", "Chuot", 250_000, "VND"),
            new Product("P003", "Cap USB", 50_000, "VND"));

    private final List<Product> products;

    CatalogFixtureStore(ObjectMapper mapper) throws IOException {
        try (InputStream input = new ClassPathResource("catalog-products.json").getInputStream()) {
            products = load(mapper, input);
        }
    }

    List<Product> products() {
        return products;
    }

    Optional<Product> find(String id) {
        return products.stream().filter(product -> product.id().equals(id)).findFirst();
    }

    static List<Product> load(ObjectMapper mapper, InputStream input) throws IOException {
        JsonNode fixture = mapper.reader()
                .with(JsonParser.Feature.STRICT_DUPLICATE_DETECTION)
                .with(DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
                .readTree(input);
        JsonNode entries = fixture.path("products");
        if (!fixture.isObject() || fixture.size() != 1 || !entries.isArray()) {
            throw new IllegalStateException("Catalog fixture must contain a products array");
        }

        List<Product> parsed = new ArrayList<>();
        for (JsonNode entry : entries) {
            parsed.add(parseProduct(entry));
        }
        if (!parsed.equals(CONTRACT)) {
            throw new IllegalStateException("Catalog fixture must match Q02 in product ID order");
        }
        return List.copyOf(parsed);
    }

    private static Product parseProduct(JsonNode entry) {
        JsonNode id = entry.path("id");
        JsonNode name = entry.path("name");
        JsonNode price = entry.path("price");
        JsonNode currency = entry.path("currency");
        if (!entry.isObject() || entry.size() != 4
                || !id.isTextual() || !Product.hasValidId(id.textValue())
                || !name.isTextual() || name.textValue().isEmpty()
                || !price.isIntegralNumber() || !price.canConvertToLong() || price.longValue() < 0
                || !currency.isTextual() || !"VND".equals(currency.textValue())) {
            throw new IllegalStateException("Invalid product in Catalog fixture");
        }
        return new Product(id.textValue(), name.textValue(), price.longValue(), currency.textValue());
    }
}
