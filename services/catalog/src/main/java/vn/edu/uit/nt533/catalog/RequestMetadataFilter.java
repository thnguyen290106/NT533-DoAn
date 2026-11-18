package vn.edu.uit.nt533.catalog;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.UUID;
import java.util.regex.Pattern;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
final class RequestMetadataFilter extends OncePerRequestFilter {
    private static final String REQUEST_ID = "X-Request-ID";
    private static final String INSTANCE_ID = "X-Instance-ID";
    private static final Pattern REQUEST_ID_PATTERN = Pattern.compile("[0-9a-f]{32}");

    private final String instanceId;

    RequestMetadataFilter(@Value("${catalog.instance-id}") String instanceId) {
        if (!instanceId.matches("C[1-3]")) {
            throw new IllegalArgumentException("Catalog INSTANCE_ID must be C1, C2 or C3");
        }
        this.instanceId = instanceId;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain chain) throws ServletException, IOException {
        String requestId = request.getHeader(REQUEST_ID);
        if (requestId == null || !REQUEST_ID_PATTERN.matcher(requestId).matches()) {
            requestId = UUID.randomUUID().toString().replace("-", "");
        }
        new RequestMetadata(requestId, instanceId).attachTo(request);
        response.setHeader(REQUEST_ID, requestId);
        response.setHeader(INSTANCE_ID, instanceId);
        chain.doFilter(request, response);
    }
}
