import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 1,
  iterations: 1,
  thresholds: { checks: ['rate==1.0'] },
};

const origin = (__ENV.NT533_BASE_URL || 'http://127.0.0.1:8080').replace(/\/$/, '');
const fixtures = [
  { id: 'P001', name: 'Ban phim', price: 100000, currency: 'VND' },
  { id: 'P002', name: 'Chuot', price: 250000, currency: 'VND' },
  { id: 'P003', name: 'Cap USB', price: 50000, currency: 'VND' },
];

function verify(name, response, status, instance, fields) {
  let body;
  try { body = response.json(); } catch (_) { body = null; }
  check(response, {
    [name + ' status ' + status]: (r) => r.status === status,
    [name + ' đúng body']: () => body !== null && fields(body),
    [name + ' đúng metadata']: (r) => body !== null
      && /^[0-9a-f]{32}$/.test(body.requestId)
      && body.requestId === r.headers['X-Request-Id']
      && body.instanceId === instance && body.instanceId === r.headers['X-Instance-Id'],
  });
}

function productMatches(product, expected) {
  return product !== null && typeof product === 'object'
    && Object.keys(expected).every((key) => product[key] === expected[key]);
}

export default function () {
  const params = { timeout: '5s', redirects: 0 };
  const get = (path) => http.get(origin + path, params);
  const quote = (productId, quantity) => http.post(origin + '/api/orders/quote',
    JSON.stringify({ productId, quantity }), { ...params, headers: { 'Content-Type': 'application/json' } });
  verify('catalog list', get('/api/catalog/products'), 200, 'C1', (b) => Array.isArray(b.products)
    && b.products.length === fixtures.length && b.products.every((p, i) => productMatches(p, fixtures[i])));
  verify('catalog detail', get('/api/catalog/products/P001'), 200, 'C1', (b) => productMatches(b, fixtures[0]));
  verify('inventory stock', get('/api/inventory/P001'), 200, 'I1',
    (b) => b.productId === 'P001' && b.availableStock === 100);
  verify('inventory zero', get('/api/inventory/P003'), 200, 'I1',
    (b) => b.productId === 'P003' && b.availableStock === 0);
  verify('quote', quote('P001', 2), 200, 'O1', (b) => b.productId === 'P001'
    && b.quantity === 2 && b.availableStock === 100 && b.unitPrice === 100000
    && b.totalPrice === 200000 && b.currency === 'VND');
  verify('insufficient stock', quote('P002', 4), 409, 'O1', (b) => b.error?.code === 'INSUFFICIENT_STOCK');
  verify('invalid catalog id', get('/api/catalog/products/p001'), 400, 'C1', (b) => b.error?.code === 'INVALID_INPUT');
  verify('absent inventory id', get('/api/inventory/P999'), 404, 'I1', (b) => b.error?.code === 'PRODUCT_NOT_FOUND');
}
