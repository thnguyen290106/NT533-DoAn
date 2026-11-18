package vn.edu.uit.nt533.inventory;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest(properties = {"inventory.instance-id=I2", "management.server.port=0"})
@AutoConfigureMockMvc
class InventoryHttpTest {
    private static final String REQUEST_ID = "0123456789abcdef0123456789abcdef";
    @Autowired private MockMvc mvc;

    @ParameterizedTest
    @CsvSource({"P001,100", "P002,3", "P003,0"})
    void returnsStockAndMetadata(String id, int stock) throws Exception {
        mvc.perform(get("/api/inventory/" + id).header("X-Request-ID", REQUEST_ID))
                .andExpect(status().isOk()).andExpect(header().string("X-Request-ID", REQUEST_ID))
                .andExpect(header().string("X-Instance-ID", "I2")).andExpect(jsonPath("$.instanceId").value("I2"))
                .andExpect(jsonPath("$.requestId").value(REQUEST_ID))
                .andExpect(jsonPath("$.productId").value(id))
                .andExpect(jsonPath("$.availableStock").value(stock));
    }

    @Test
    void rejectsInvalidAndMissingProducts() throws Exception {
        for (String route : new String[]{"p001", "P001;extra=yes", "P001?extra=yes"}) {
            mvc.perform(get("/api/inventory/" + route))
                    .andExpect(status().isBadRequest()).andExpect(jsonPath("$.error.code").value("INVALID_INPUT"));
        }
        mvc.perform(get("/api/inventory/P999"))
                .andExpect(status().isNotFound()).andExpect(jsonPath("$.error.code").value("PRODUCT_NOT_FOUND"));
        mvc.perform(get("/api/inventory"))
                .andExpect(status().isNotFound()).andExpect(jsonPath("$.error.code").value("ROUTE_NOT_FOUND"));
        mvc.perform(post("/api/inventory/P001"))
                .andExpect(status().isMethodNotAllowed()).andExpect(header().exists("Allow"));
    }
}
