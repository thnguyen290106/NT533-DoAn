package vn.edu.uit.nt533.order;

import org.springframework.http.HttpStatus;

final class OrderException extends RuntimeException {
    private final HttpStatus status;
    private final String code;

    OrderException(HttpStatus status, String code, String message) {
        super(message);
        this.status = status;
        this.code = code;
    }

    HttpStatus status() {
        return status;
    }

    String code() {
        return code;
    }
}
