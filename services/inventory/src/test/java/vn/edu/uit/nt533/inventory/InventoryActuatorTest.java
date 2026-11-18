package vn.edu.uit.nt533.inventory;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.autoconfigure.actuate.observability.AutoConfigureObservability;
import org.springframework.boot.test.context.SpringBootTest;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT,
        properties = {"management.server.port=0", "inventory.instance-id=I2"})
@AutoConfigureObservability
class InventoryActuatorTest {
    @Value("${local.management.port}")
    private int managementPort;

    @Value("${local.server.port}")
    private int businessPort;

    private final HttpClient http = HttpClient.newHttpClient();

    @Test
    void exposesReadinessAndTaggedMetricsOnSeparateManagementPort() throws Exception {
        assertThat(managementPort).isNotEqualTo(businessPort);
        var readiness = get(managementPort, "/actuator/health/readiness");
        var metrics = get(managementPort, "/actuator/prometheus");
        assertThat(readiness.statusCode()).isEqualTo(200);
        assertThat(readiness.body()).contains("\"status\":\"UP\"");
        assertThat(metrics.statusCode()).isEqualTo(200);
        assertThat(metrics.body().lines().anyMatch(line -> line.startsWith("jvm_memory_used_bytes{")
                && line.contains("instance=\"I2\"") && line.contains("service=\"inventory\""))).isTrue();
        assertThat(get(businessPort, "/actuator/prometheus").statusCode()).isEqualTo(404);
    }

    private HttpResponse<String> get(int port, String route) throws Exception {
        var request = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + route)).GET().build();
        return http.send(request, HttpResponse.BodyHandlers.ofString());
    }
}
