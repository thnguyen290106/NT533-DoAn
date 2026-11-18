package vn.edu.uit.nt533.order;

import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.HttpMediaTypeNotAcceptableException;
import org.springframework.web.HttpMediaTypeNotSupportedException;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.servlet.NoHandlerFoundException;

@RestControllerAdvice
final class OrderExceptionHandler {
    private static final Logger LOG = LoggerFactory.getLogger(OrderExceptionHandler.class);

    @ExceptionHandler(OrderException.class)
    ResponseEntity<ErrorResponse> orderError(OrderException error, HttpServletRequest request) {
        return response(error.status(), error.code(), error.getMessage(), request);
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    ResponseEntity<ErrorResponse> invalidBody(HttpServletRequest request) {
        return response(HttpStatus.BAD_REQUEST, "INVALID_INPUT", "Invalid request", request);
    }

    @ExceptionHandler(HttpMediaTypeNotSupportedException.class)
    ResponseEntity<ErrorResponse> unsupportedType(HttpServletRequest request) {
        return response(HttpStatus.UNSUPPORTED_MEDIA_TYPE, "UNSUPPORTED_MEDIA_TYPE", "Unsupported media type", request);
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
        LOG.error("Order request failed", error);
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
