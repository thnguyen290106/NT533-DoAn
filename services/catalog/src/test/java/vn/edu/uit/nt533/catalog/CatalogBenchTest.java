package vn.edu.uit.nt533.catalog;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@ActiveProfiles("lab")
@SpringBootTest(properties = {"nt533.bench.iterations=3", "catalog.instance-id=C2"})
@AutoConfigureMockMvc
class CatalogBenchTest {
    @Autowired private MockMvc mvc;

    @Test
    void computesTheExactDigestChain() throws Exception {
        mvc.perform(get("/internal/bench").queryParam("profile", "cpu-fixed"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.iterations").value(3))
                .andExpect(jsonPath("$.checksum").value("5a02beb2b26c6489389adcc9b1c657039374e5d9d778629c0c9972ecb02fbc5f"))
                .andExpect(jsonPath("$.instanceId").value("C2"));
    }

    @Test
    void rejectsClientSelectedWork() throws Exception {
        mvc.perform(get("/internal/bench").queryParam("profile", "cpu-fixed").queryParam("iterations", "1"))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.error.code").value("INVALID_INPUT"));
    }
}
