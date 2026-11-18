package vn.edu.uit.nt533.catalog;

import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.HttpMediaTypeNotAcceptableException;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.servlet.NoHandlerFoundException;

@RestControllerAdvice
final class CatalogExceptionHandler {
    private static final Logger LOG = LoggerFactory.getLogger(CatalogExceptionHandler.class);

    @ExceptionHandler(CatalogException.class)
    ResponseEntity<ErrorResponse> catalogError(CatalogException error, HttpServletRequest request) {
        return response(error.status(), error.code(), error.getMessage(), request);
    }

    @ExceptionHandler(NoHandlerFoundException.class)
    ResponseEntity<ErrorResponse> routeNotFound(HttpServletRequest request) {
        return response(HttpStatus.NOT_FOUND, "ROUTE_NOT_FOUND", "Route not found", request);
    }

    @ExceptionHandler(HttpRequestMethodNotSupportedException.class)
    ResponseEntity<ErrorResponse> methodNotAllowed(HttpRequestMethodNotSupportedException error,
                                                   HttpServletRequest request) {
        return ResponseEntity.status(HttpStatus.METHOD_NOT_ALLOWED)
                .headers(error.getHeaders())
                .contentType(MediaType.APPLICATION_JSON)
                .body(body("METHOD_NOT_ALLOWED", "Method not allowed", request));
    }

    @ExceptionHandler(HttpMediaTypeNotAcceptableException.class)
    ResponseEntity<ErrorResponse> notAcceptable(HttpServletRequest request) {
        return response(HttpStatus.NOT_ACCEPTABLE, "NOT_ACCEPTABLE", "Not acceptable", request);
    }

    @ExceptionHandler(Exception.class)
    ResponseEntity<ErrorResponse> internalError(Exception error, HttpServletRequest request) {
        LOG.error("Catalog request failed", error);
        return response(HttpStatus.INTERNAL_SERVER_ERROR, "INTERNAL_ERROR", "Internal error", request);
    }

    private static ResponseEntity<ErrorResponse> response(HttpStatus status, String code, String message,
                                                          HttpServletRequest request) {
        return ResponseEntity.status(status)
                .contentType(MediaType.APPLICATION_JSON)
                .body(body(code, message, request));
    }

    private static ErrorResponse body(String code, String message, HttpServletRequest request) {
        RequestMetadata metadata = RequestMetadata.from(request);
        return new ErrorResponse(new ErrorDetail(code, message), metadata.requestId(), metadata.instanceId());
    }

    record ErrorResponse(ErrorDetail error, String requestId, String instanceId) {}

    record ErrorDetail(String code, String message) {}
}
