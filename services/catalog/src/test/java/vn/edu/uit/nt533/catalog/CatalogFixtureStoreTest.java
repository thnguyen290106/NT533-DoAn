package vn.edu.uit.nt533.catalog;

import static java.nio.charset.StandardCharsets.UTF_8;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.stream.Stream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import org.springframework.core.io.ClassPathResource;

class CatalogFixtureStoreTest {
    private static final ObjectMapper MAPPER = new ObjectMapper();

    @Test
    void fixtureBytesMatchTheReplicaContract() throws Exception {
        try (var input = new ClassPathResource("catalog-products.json").getInputStream()) {
            assertThat(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(input.readAllBytes())))
                    .isEqualTo("bd76926a87fd55258a567c248146ff215632ae323bd276fcc7a76eae227d850e");
        }
    }

    @Test
    void loadsThePackagedFixtureOnceAsImmutableProducts() throws IOException {
        var store = new CatalogFixtureStore(MAPPER);
        var products = store.products();

        assertThat(products).containsExactly(
                new Product("P001", "Ban phim", 100_000L, "VND"),
                new Product("P002", "Chuot", 250_000L, "VND"),
                new Product("P003", "Cap USB", 50_000L, "VND"));
        assertThat(store.products()).isSameAs(products);
        assertThat(store.find("P002")).containsSame(products.get(1));
        assertThat(store.find("P999")).isEmpty();
        assertThatThrownBy(products::clear).isInstanceOf(UnsupportedOperationException.class);
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("invalidFixtures")
    void rejectsInvalidFixture(String description, String json, Class<? extends Exception> errorType) {
        assertThatThrownBy(() -> load(json)).isInstanceOf(errorType);
    }

    private static Stream<Arguments> invalidFixtures() throws IOException {
        String fixture = new ClassPathResource("catalog-products.json").getContentAsString(UTF_8);
        return Stream.of(
                invalid("string price", fixture.replace("100000", "\"100000\"")),
                invalid("boolean price", fixture.replace("100000", "true")),
                invalid("decimal price", fixture.replace("100000", "100000.0")),
                invalid("scientific price", fixture.replace("100000", "1e5")),
                invalid("overflowing price", fixture.replace("100000", "9223372036854775808")),
                invalid("negative price", fixture.replace("100000", "-1")),
                invalid("null price", fixture.replace("100000", "null")),
                invalid("different integer price", fixture.replace("100000", "100001")),
                invalid("unknown product field", fixture.replace("\"price\": 100000", "\"stock\": 100")),
                invalid("missing product field", fixture.replace("\"price\": 100000, ", "")),
                invalid("duplicate ID", fixture.replace("P002", "P001")),
                invalid("unexpected ID", fixture.replace("P002", "P004")),
                invalid("out-of-order IDs", fixture.replace("P001", "P000").replace("P002", "P001")
                        .replace("P000", "P002")),
                invalid("different name", fixture.replace("Ban phim", "Keyboard")),
                invalid("different currency", fixture.replace("\"VND\"", "\"USD\"")),
                invalid("missing products", "{}"),
                invalid("empty products", "{\"products\": []}"),
                invalid("empty file", ""),
                Arguments.of("duplicate field", fixture.replace("\"id\": \"P001\"",
                        "\"id\": \"P001\", \"id\": \"P001\""), IOException.class),
                Arguments.of("trailing JSON", fixture + "{}", IOException.class));
    }

    private static Arguments invalid(String description, String json) {
        return Arguments.of(description, json, IllegalStateException.class);
    }

    private static List<Product> load(String json) throws IOException {
        return CatalogFixtureStore.load(MAPPER, new ByteArrayInputStream(json.getBytes(UTF_8)));
    }
}
