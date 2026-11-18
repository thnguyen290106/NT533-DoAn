package vn.edu.uit.nt533.order;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest(properties = "management.server.port=0")
@AutoConfigureMockMvc
class OrderHttpTest {
    private static final String RID = "0123456789abcdef0123456789abcdef";
    private static final List<String> CALLS = Collections.synchronizedList(new ArrayList<>());
    private static final HttpServer UPSTREAM = upstream();
    @Autowired private MockMvc mvc;

    @DynamicPropertySource
    static void urls(DynamicPropertyRegistry registry) {
        String url = "http://127.0.0.1:" + UPSTREAM.getAddress().getPort();
        registry.add("order.catalog-url", () -> url);
        registry.add("order.inventory-url", () -> url);
    }

    @AfterAll
    static void closeServer() {
        UPSTREAM.stop(0);
    }

    @BeforeEach
    void clearCalls() {
        CALLS.clear();
    }

    @Test
    void quoteUsesBothServicesInOrder() throws Exception {
        mvc.perform(input("{\"productId\":\"P001\",\"quantity\":2}"))
                .andExpect(status().isOk()).andExpect(header().string("X-Request-ID", RID))
                .andExpect(header().string("X-Instance-ID", "O1"))
                .andExpect(jsonPath("$.totalPrice").value(200000))
                .andExpect(jsonPath("$.availableStock").value(100))
                .andExpect(jsonPath("$.requestId").value(RID));
        assertThat(CALLS).containsExactly(RID + "-catalog", RID + "-inventory");
    }

    @Test
    void inputAndCatalogErrorsStopBeforeInventory() throws Exception {
        for (String body : new String[]{
                "{\"productId\":\"P001\",\"quantity\":2.0}",
                "{\"productId\":\"P001\",\"quantity\":0}",
                "{\"productId\":\"P001\",\"quantity\":\"2\"}",
                "{\"productId\":\"P001\",\"quantity\":1,\"extra\":0}",
                "{\"productId\":\"P001\",\"quantity\":1,\"quantity\":2}"}) {
            mvc.perform(input(body)).andExpect(status().isBadRequest())
                    .andExpect(jsonPath("$.error.code").value("INVALID_INPUT"));
        }
        assertThat(CALLS).isEmpty();
        mvc.perform(input("{\"productId\":\"P999\",\"quantity\":2}"))
                .andExpect(status().isNotFound()).andExpect(jsonPath("$.error.code").value("PRODUCT_NOT_FOUND"));
        assertThat(CALLS).containsExactly(RID + "-catalog");
    }

    @Test
    void stockAndInvalidDownstreamBodyAreNotSuccesses() throws Exception {
        mvc.perform(input("{\"productId\":\"P003\",\"quantity\":1}"))
                .andExpect(status().isConflict()).andExpect(jsonPath("$.error.code").value("INSUFFICIENT_STOCK"));
        mvc.perform(input("{\"productId\":\"P002\",\"quantity\":1}"))
                .andExpect(status().isBadGateway()).andExpect(jsonPath("$.error.code").value("DOWNSTREAM_BAD_RESPONSE"));
        mvc.perform(post("/api/orders/quote").contentType(MediaType.TEXT_PLAIN).content("text"))
                .andExpect(status().isUnsupportedMediaType())
                .andExpect(jsonPath("$.error.code").value("UNSUPPORTED_MEDIA_TYPE"));
    }

    private static org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder input(String body) {
        return post("/api/orders/quote").header("X-Request-ID", RID)
                .contentType(MediaType.APPLICATION_JSON).content(body);
    }

    private static HttpServer upstream() {
        try {
            HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
            server.createContext("/", OrderHttpTest::respond);
            server.start();
            return server;
        } catch (IOException error) {
            throw new IllegalStateException(error);
        }
    }

    private static void respond(HttpExchange request) throws IOException {
        String path = request.getRequestURI().getPath();
        CALLS.add(request.getRequestHeaders().getFirst("X-Call-ID"));
        String id = path.substring(path.lastIndexOf('/') + 1);
        boolean catalog = path.startsWith("/api/catalog/");
        String body = catalog
                ? "\"id\":\"" + id + "\",\"currency\":\"VND\",\"price\":100000"
                : "\"productId\":\"" + id + "\",\"availableStock\":" + (id.equals("P003") ? "0" : "100");
        if (id.equals("P002") && catalog) {
            body = "\"id\":\"" + id + "\",\"price\":\"100000\",\"currency\":\"VND\"";
        }
        byte[] bytes = ("{" + body + ",\"requestId\":\"" + RID + "\"}").getBytes(StandardCharsets.UTF_8);
        try (request) {
            request.getResponseHeaders().set("Content-Type", "application/json");
            request.sendResponseHeaders(id.equals("P999") ? 404 : 200, bytes.length);
            request.getResponseBody().write(bytes);
        }
    }
}
