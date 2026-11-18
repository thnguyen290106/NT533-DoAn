package vn.edu.uit.nt533.catalog;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.containsString;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.net.URI;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.NullAndEmptySource;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.json.JsonCompareMode;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;
import org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder;

@SpringBootTest(properties = "catalog.instance-id=C2")
@AutoConfigureMockMvc
class CatalogHttpTest {
    private static final String PRODUCTS = "/api/catalog/products";
    private static final String REQUEST_ID = "0123456789abcdef0123456789abcdef";

    @Autowired
    private MockMvc mvc;

    @Autowired
    private ObjectMapper mapper;

    @Test
    void listsExactlyTheThreeProductsInIdOrder() throws Exception {
        assertMetadata(mvc.perform(get(PRODUCTS).header("X-Request-ID", REQUEST_ID)))
                .andExpect(status().isOk())
                .andExpect(content().json("""
                        {
                          "products": [
                            {"id":"P001","name":"Ban phim","price":100000,"currency":"VND"},
                            {"id":"P002","name":"Chuot","price":250000,"currency":"VND"},
                            {"id":"P003","name":"Cap USB","price":50000,"currency":"VND"}
                          ],
                          "requestId":"%s",
                          "instanceId":"C2"
                        }
                        """.formatted(REQUEST_ID), JsonCompareMode.STRICT));
    }

    @ParameterizedTest
    @CsvSource({"P001, Ban phim, 100000", "P002, Chuot, 250000", "P003, Cap USB, 50000"})
    void returnsExactFixtureDetails(String id, String name, long price) throws Exception {
        var result = assertMetadata(mvc.perform(get(PRODUCTS + "/{id}", id).header("X-Request-ID", REQUEST_ID)))
                .andExpect(status().isOk())
                .andExpect(content().json("""
                        {"id":"%s","name":"%s","price":%d,"currency":"VND","requestId":"%s","instanceId":"C2"}
                        """.formatted(id, name, price, REQUEST_ID), JsonCompareMode.STRICT))
                .andReturn();

        assertThat(mapper.readTree(result.getResponse().getContentAsString()).get("price").isIntegralNumber())
                .isTrue();
    }

    @ParameterizedTest
    @ValueSource(strings = {"p001", "P01", "P0001", "P0x1", "P００１", "P001 "})
    void rejectsIdOutsideTheContract(String id) throws Exception {
        expectError(get(PRODUCTS + "/{id}", id), 400, "INVALID_INPUT", "Invalid request");
    }

    @ParameterizedTest
    @ValueSource(strings = {"/P001;foo=bar", "/P001;", "/P999;foo=bar", "/P001%3Bfoo=bar", ";foo=bar/P001"})
    void rejectsMatrixParametersInDetailPath(String suffix) throws Exception {
        expectError(get(URI.create(PRODUCTS + suffix)), 400, "INVALID_INPUT", "Invalid request");
    }

    @Test
    void rejectsMatrixParametersInListPath() throws Exception {
        expectError(get(URI.create(PRODUCTS + ";view=compact")), 400, "INVALID_INPUT", "Invalid request");
    }

    @ParameterizedTest
    @ValueSource(strings = {PRODUCTS, PRODUCTS + "/P001"})
    void rejectsUnacceptableResponseMediaType(String path) throws Exception {
        expectError(get(path).accept(MediaType.TEXT_PLAIN), 406, "NOT_ACCEPTABLE", "Not acceptable");
    }

    @Test
    void distinguishesAbsentFixtureIdFromInvalidId() throws Exception {
        expectError(get(PRODUCTS + "/P999"), 404, "PRODUCT_NOT_FOUND", "Product not found");
    }

    @ParameterizedTest
    @ValueSource(strings = {PRODUCTS, PRODUCTS + "/P001"})
    void rejectsUndeclaredQuery(String path) throws Exception {
        expectError(get(path).queryParam("page", "1"), 400, "INVALID_INPUT", "Invalid request");
    }

    @Test
    void distinguishesUnknownRouteFromMissingProduct() throws Exception {
        expectError(get("/api/catalog/unknown"), 404, "ROUTE_NOT_FOUND", "Route not found");
    }

    @Test
    void rejectsUnsupportedMethodWithAllowHeader() throws Exception {
        expectError(post(PRODUCTS), 405, "METHOD_NOT_ALLOWED", "Method not allowed")
                .andExpect(header().string("Allow", containsString("GET")));
    }

    @ParameterizedTest
    @NullAndEmptySource
    @ValueSource(strings = {"not-a-request-id"})
    void generatesRequestIdForDirectRequestsWithoutUsableHeader(String supplied) throws Exception {
        var request = get(PRODUCTS + "/P001");
        if (supplied != null) {
            request.header("X-Request-ID", supplied);
        }

        var response = mvc.perform(request)
                .andExpect(status().isOk())
                .andExpect(header().string("X-Instance-ID", "C2"))
                .andReturn().getResponse();

        String generated = response.getHeader("X-Request-ID");
        assertThat(generated).matches("[0-9a-f]{32}");
        var body = mapper.readTree(response.getContentAsString());
        assertThat(body.get("requestId").asText()).isEqualTo(generated);
        assertThat(body.get("instanceId").asText()).isEqualTo("C2");
    }

    private ResultActions expectError(MockHttpServletRequestBuilder request, int statusCode, String code,
                                      String message) throws Exception {
        return assertMetadata(mvc.perform(request.header("X-Request-ID", REQUEST_ID)))
                .andExpect(status().is(statusCode))
                .andExpect(content().json("""
                        {"error":{"code":"%s","message":"%s"},"requestId":"%s","instanceId":"C2"}
                        """.formatted(code, message, REQUEST_ID), JsonCompareMode.STRICT));
    }

    private static ResultActions assertMetadata(ResultActions response) throws Exception {
        return response.andExpect(header().string("X-Request-ID", REQUEST_ID))
                .andExpect(header().string("X-Instance-ID", "C2"))
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON));
    }
}
