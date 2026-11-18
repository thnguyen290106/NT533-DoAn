package vn.edu.uit.nt533.inventory;

import org.springframework.http.HttpStatus;

final class InventoryException extends RuntimeException {
    private final HttpStatus status;
    private final String code;

    InventoryException(HttpStatus status, String code, String message) {
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
