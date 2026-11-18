package vn.edu.uit.nt533.catalog;

import jakarta.servlet.http.HttpServletRequest;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Profile;
import org.springframework.http.HttpStatus;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Profile("lab")
@RestController
final class CatalogBenchController {
    private final int iterations;

    CatalogBenchController(@Value("${nt533.bench.iterations:1000}") int iterations) {
        if (iterations < 1 || iterations > 1_024_000) {
            throw new IllegalArgumentException("nt533.bench.iterations must be between 1 and 1024000");
        }
        this.iterations = iterations;
    }

    @GetMapping("/internal/bench")
    Work bench(@RequestParam MultiValueMap<String, String> query, HttpServletRequest request)
            throws NoSuchAlgorithmException {
        if (query.size() != 1 || !List.of("cpu-fixed").equals(query.get("profile"))) {
            throw new CatalogException(HttpStatus.BAD_REQUEST, "INVALID_INPUT", "Invalid benchmark profile or query");
        }
        MessageDigest sha256 = MessageDigest.getInstance("SHA-256");
        byte[] value = "NT533-v1".getBytes(StandardCharsets.UTF_8);
        for (int round = 0; round < iterations; round++) {
            value = sha256.digest(value);
        }
        RequestMetadata metadata = RequestMetadata.from(request);
        return new Work("cpu-fixed", iterations, HexFormat.of().formatHex(value), metadata.requestId(), metadata.instanceId());
    }

    record Work(String profile, int iterations, String checksum, String requestId, String instanceId) {}
}
