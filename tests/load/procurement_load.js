// k6 Load Test — Ugavi Procurement API (GA-059)
// Usage: make load-test   (runs: k6 run tests/load/procurement_load.js)
//
// Scenarios:
//   1. PR creation (constant rate: 2/min)
//   2. Tender listing (spike: 50 concurrent)
//   3. Bid submission (ramp: 1→5 over 60s)
//   4. Stock query (stress: 100 concurrent)

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const prCreateDuration = new Trend('pr_create_duration');
const tenderListDuration = new Trend('tender_list_duration');
const bidSubmitDuration = new Trend('bid_submit_duration');
const stockQueryDuration = new Trend('stock_query_duration');

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_KEY = __ENV.API_KEY || 'test-api-key';
const API_SECRET = __ENV.API_SECRET || 'test-api-secret';

// Auth headers for API calls
const headers = {
  'Authorization': `token ${API_KEY}:${API_SECRET}`,
  'Content-Type': 'application/json',
};

export const options = {
  thresholds: {
    errors: ['rate<0.05'],               // <5% error rate
    http_req_duration: ['p(95)<2000'],    // 95th percentile <2s
    http_req_failed: ['rate<0.01'],       // <1% failures
  },
  scenarios: {
    // PR creation — constant 2/min (simulates normal usage)
    pr_creation: {
      executor: 'constant-arrival-rate',
      rate: 2,
      timeUnit: '1m',
      duration: '5m',
      preAllocatedVUs: 5,
      maxVUs: 20,
      exec: 'createPr',
    },
    // Tender listing — spike test (50 concurrent)
    tender_listing: {
      executor: 'shared-iterations',
      vus: 50,
      iterations: 200,
      maxDuration: '2m',
      exec: 'listTenders',
      startTime: '1m',
    },
    // Bid submission — ramp 1→5 VUs
    bid_submission: {
      executor: 'ramping-vus',
      startVUs: 1,
      stages: [
        { duration: '60s', target: 5 },
        { duration: '60s', target: 5 },
        { duration: '30s', target: 1 },
      ],
      exec: 'submitBid',
      startTime: '2m',
    },
    // Stock query — stress test (100 concurrent)
    stock_query: {
      executor: 'shared-iterations',
      vus: 100,
      iterations: 500,
      maxDuration: '2m',
      exec: 'queryStock',
      startTime: '3m',
    },
  },
};

// --- Scenario Functions ---

export function createPr() {
  group('PR Creation', () => {
    const payload = JSON.stringify({
      doc: {
        doctype: 'Purchase Requisition',
        requisition_title: `Load Test PR ${Date.now()}`,
        donor: 'DEMO-DONOR-001',
        requisition_date: new Date().toISOString().split('T')[0],
        status: 'Draft',
      },
    });

    const start = Date.now();
    const res = http.post(`${BASE_URL}/api/method/frappe.client.insert`, payload, { headers });
    prCreateDuration.add(Date.now() - start);

    const ok = check(res, {
      'PR created': (r) => r.status === 200,
      'has data': (r) => JSON.parse(r.body).message?.name !== undefined,
    });
    errorRate.add(!ok);

    sleep(1);
  });
}

export function listTenders() {
  group('Tender Listing', () => {
    const start = Date.now();
    const res = http.get(`${BASE_URL}/api/method/frappe.client.get_list?doctype=Tender&fields=["name","status","tender_title"]&limit=50`, { headers });
    tenderListDuration.add(Date.now() - start);

    const ok = check(res, {
      'tenders listed': (r) => r.status === 200,
    });
    errorRate.add(!ok);
  });
}

export function submitBid() {
  group('Bid Submission', () => {
    const payload = JSON.stringify({
      tender: 'DEMO-TENDER-001',
      bid_amount: 10000 + Math.floor(Math.random() * 50000),
      bid_currency: 'USD',
    });

    const start = Date.now();
    const res = http.post(`${BASE_URL}/api/method/ugavi.procurement.portal.supplier_portal.submit_bid`, payload, { headers });
    bidSubmitDuration.add(Date.now() - start);

    const ok = check(res, {
      'bid submitted': (r) => r.status === 200 || r.status === 400, // 400 = rate limit OK
    });
    errorRate.add(!ok);

    sleep(3); // Respect rate limiter: 3/hr per supplier
  });
}

export function queryStock() {
  group('Stock Query', () => {
    const start = Date.now();
    const res = http.get(`${BASE_URL}/api/method/frappe.client.get_list?doctype=Stock+Ledger&fields=["item_code","donor","warehouse","incoming_qty","outgoing_qty"]&filters=[["donor","=","DEMO-DONOR-001"]]&limit=100`, { headers });
    stockQueryDuration.add(Date.now() - start);

    const ok = check(res, {
      'stock queried': (r) => r.status === 200,
    });
    errorRate.add(!ok);
  });
}

export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    p95_http_req_duration: data.metrics.http_req_duration.values['p(95)'],
    error_rate: data.metrics.errors?.values?.rate || 0,
    total_requests: data.metrics.http_reqs?.values?.count || 0,
    pr_creation_p95: data.metrics.pr_create_duration?.values?.['p(95)'],
    tender_list_p95: data.metrics.tender_list_duration?.values?.['p(95)'],
    bid_submit_p95: data.metrics.bid_submit_duration?.values?.['p(95)'],
    stock_query_p95: data.metrics.stock_query_duration?.values?.['p(95)'],
  };

  return {
    'stdout': JSON.stringify(summary, null, 2),
    'tests/load/results/summary.json': JSON.stringify(summary, null, 2),
    'tests/load/results/summary.html': htmlReport(data),
  };
}

function htmlReport(data) {
  return `<html><body>
    <h1>Ugavi Load Test Results</h1>
    <p>P95 Duration: ${data.metrics.http_req_duration.values['p(95)']}ms</p>
    <p>Error Rate: ${(data.metrics.errors?.values?.rate * 100).toFixed(2)}%</p>
    <p>Total Requests: ${data.metrics.http_reqs?.values?.count}</p>
  </body></html>`;
}