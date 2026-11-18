package vn.edu.uit.nt533.inventory;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@ActiveProfiles("lab")
@SpringBootTest(properties = {"inventory.instance-id=I3", "nt533.bench.extra-delay-ms=300"})
@AutoConfigureMockMvc
class InventoryBenchTest {
    @Autowired private MockMvc mvc;

    @ParameterizedTest
    @CsvSource({"fast,320", "slow,500"})
    void reportsAndAppliesBoundedDelay(String delay, int ms) throws Exception {
        long started = System.nanoTime();
        mvc.perform(get("/internal/bench").queryParam("profile", "mixed-delay").queryParam("delayClass", delay))
                .andExpect(status().isOk()).andExpect(jsonPath("$.appliedDelayMs").value(ms));
        assertThat(System.nanoTime() - started).isGreaterThanOrEqualTo((long) ms * 1_000_000);
    }

    @Test
    void mappingSkipsDelayAndCustomInputIsRejected() throws Exception {
        mvc.perform(get("/internal/bench").queryParam("profile", "mapping"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.appliedDelayMs").doesNotExist());
        mvc.perform(get("/internal/bench").queryParam("profile", "mixed-delay").queryParam("delayClass", "10"))
                .andExpect(status().isBadRequest());
    }
}
