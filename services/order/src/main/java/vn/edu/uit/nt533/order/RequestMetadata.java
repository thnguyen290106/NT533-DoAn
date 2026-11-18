package vn.edu.uit.nt533.order;

import jakarta.servlet.http.HttpServletRequest;

record RequestMetadata(String requestId, String instanceId) {
    private static final String ATTRIBUTE = RequestMetadata.class.getName();

    void attachTo(HttpServletRequest request) {
        request.setAttribute(ATTRIBUTE, this);
    }

    static RequestMetadata from(HttpServletRequest request) {
        return (RequestMetadata) request.getAttribute(ATTRIBUTE);
    }
}
