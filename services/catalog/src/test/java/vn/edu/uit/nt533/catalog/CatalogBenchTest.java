package vn.edu.uit.nt533.catalog;

import java.util.concurrent.Semaphore;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.test.web.servlet.MockMvc;

import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@ActiveProfiles("lab")
@SpringBootTest(properties = {"nt533.bench.iterations=3", "catalog.instance-id=C2"})
@AutoConfigureMockMvc
class CatalogBenchTest {
    @Autowired private MockMvc mvc;
    @Autowired private CatalogBenchController controller;

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

    @Test
    void rejectsOverloadAndAcceptsWorkAfterAWorkerFinishes() throws Exception {
        Semaphore slots = (Semaphore) ReflectionTestUtils.getField(controller, "cpuSlots");
        assertTrue(slots.tryAcquire(2));
        try {
            mvc.perform(get("/internal/bench").queryParam("profile", "cpu-fixed"))
                    .andExpect(status().isServiceUnavailable())
                    .andExpect(jsonPath("$.error.code").value("BENCH_OVERLOADED"))
                    .andExpect(jsonPath("$.instanceId").value("C2"));
        } finally {
            slots.release(2);
        }
        mvc.perform(get("/internal/bench").queryParam("profile", "cpu-fixed"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.checksum").value("5a02beb2b26c6489389adcc9b1c657039374e5d9d778629c0c9972ecb02fbc5f"));
    }
}
