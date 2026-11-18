package vn.edu.uit.nt533.catalog;

import java.util.regex.Pattern;

record Product(String id, String name, long price, String currency) {
    private static final Pattern ID_PATTERN = Pattern.compile("P[0-9]{3}");

    static boolean hasValidId(String id) {
        return ID_PATTERN.matcher(id).matches();
    }
}
