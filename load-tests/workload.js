import http from 'k6/http';
import { SharedArray } from 'k6/data';
import { scenario } from 'k6/execution';

const plan = JSON.parse(__ENV.NT533_PLAN || '{}');
const trace = new SharedArray('trace', () => (
  __ENV.NT533_TRACE ? open(__ENV.NT533_TRACE).trimEnd().split('\n').slice(1).map(line => line.split(',')) : []
));

export const options = { scenarios: plan.scenarios || { smoke: { executor: 'shared-iterations', vus: 1, iterations: 1 } } };

function result(response, profile, delay) {
  if (response.status !== 200) return false;
  const data = response.json();
  if (data.requestId !== response.headers['X-Request-Id'] || data.instanceId !== response.headers['X-Instance-Id']) return false;
  if (profile === 'cpu-fixed') return data.profile === profile && data.iterations === plan.cpu_iterations && data.checksum === plan.cpu_checksum;
  if (profile === 'mixed-delay') return data.profile === profile && data.delayClass === delay
    && data.appliedDelayMs === (delay === 'fast' ? 20 : 200) + (data.instanceId === 'I3' ? plan.i3_extra_ms || 0 : 0);
  if (profile === 'mapping') return data.profile === profile && !('appliedDelayMs' in data);
  return profile === 'quote' && data.productId === 'P001' && data.quantity === 2
    && data.availableStock === 100 && data.unitPrice === 100000 && data.totalPrice === 200000 && data.currency === 'VND';
}

export default function () {
  const offset = plan.offsets[scenario.name] || 0;
  const row = trace[offset + scenario.iterationInTest];
  if (!row) throw new Error('trace exhausted at iteration index ' + (offset + scenario.iterationInTest));
  const [index, id, client, effectiveIp, profile, delay, product, quantity] = row;
  const headers = { 'X-Request-ID': id, 'X-Lab-Client-ID': client, 'Content-Type': 'application/json' };
  if (effectiveIp) headers['X-Lab-Source-IP'] = effectiveIp;
  const opts = { headers, timeout: '5s', redirects: 0, tags: { profile } };
  const started = Date.now();
  const response = profile === 'quote'
    ? http.post(plan.base_url + '/api/orders/quote', JSON.stringify({ productId: product, quantity: Number(quantity) }), opts)
    : http.get(plan.base_url + (profile === 'cpu-fixed' ? '/bench/catalog' : '/bench/inventory') + '?profile=' + profile
      + (profile === 'mixed-delay' ? '&delayClass=' + delay : ''), opts);
  const finished = Date.now();
  const returnedId = response.headers['X-Request-Id'];
  const effectiveId = plan.public_dry_run && typeof returnedId === 'string' && /^[0-9a-f]{32}$/.test(returnedId) ? returnedId : id;
  let ok = false;
  try { ok = returnedId === effectiveId && result(response, profile, delay); } catch (_) { /* Invalid bodies remain failed samples. */ }
  console.log('NT533_REQUEST ' + JSON.stringify({ request_index: Number(index), request_id: effectiveId,
    instance_id: response.headers['X-Instance-Id'] || null, status: response.status,
    contract_ok: ok, duration_ms: finished - started, phase: scenario.name,
    started_utc: new Date(started).toISOString(), completed_utc: new Date(finished).toISOString() }));
}
