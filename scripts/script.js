import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 10 }, // Ramp up to 10 users over 2 minutes
    { duration: '3m', target: 10 }, // Stay at 10 users for 3 minutes
    { duration: '2m', target: 0 },  // Ramp down to 0 users over 2 minutes
  ],
};

const BASE_URL = 'https://l0gmn7llz8.execute-api.eu-north-1.amazonaws.com/dev';
const AUTH_TOKEN = 'your-auth-token'; // Replace with your actual auth token
const HEADERS = {
  headers: {
    'auth-token': AUTH_TOKEN,
    'Content-Type': 'application/json',
  },
};

function readOrder() {
  const url = `${BASE_URL}/MyQueue`;
  const payload = JSON.stringify({
    Message: "{\"operationType\":\"readOrder\",\"data\":{\"table_name\":\"devices\"},\"callbackUrl\":\"https://webhook.site/ed326f03-7099-42f9-a591-403a18a1b510\"}",
    MessageGroupId: "default"
  });

  let response = http.post(url, payload, HEADERS);
  check(response, { 'readOrder status was 200': (r) => r.status === 200 });
}

function updateOrder() {
  const url = `${BASE_URL}/MyQueue`;
  const payload = JSON.stringify({
    Message: "{\"operationType\":\"updateOrder\",\"data\":{\"table_name\":\"devices\",\"ids\":[\"1\", \"2\"],\"new_order_owner\":\"owner_name\",\"new_order_time\":\"2024-06-21T12:00:00Z\",\"new_order_Url\":\"http://example.com/order\"},\"callbackUrl\":\"https://webhook.site/ed326f03-7099-42f9-a591-403a18a1b510\"}",
    MessageGroupId: "default"
  });

  let response = http.post(url, payload, HEADERS);
  check(response, { 'updateOrder status was 200': (r) => r.status === 200 });
}

function addFunds() {
  const url = `${BASE_URL}/CreditsQueue`;
  const payload = JSON.stringify({
    Message: "{\"operationType\":\"addFunds\",\"data\":{\"owner_id\":\"Some_IID\",\"wallet_number\":100},\"callbackUrl\":\"https://webhook.site/ed326f03-7099-42f9-a591-403a18a1b510\"}",
    MessageGroupId: "default"
  });

  let response = http.post(url, payload, HEADERS);
  check(response, { 'addFunds status was 200': (r) => r.status === 200 });
}

function getWallet() {
  const url = `${BASE_URL}/CreditsQueue`;
  const payload = JSON.stringify({
    Message: "{\"operationType\":\"getWallet\",\"data\":{\"owner_id\":\"Some_IID\"},\"callbackUrl\":\"https://webhook.site/ed326f03-7099-42f9-a591-403a18a1b510\"}",
    MessageGroupId: "default"
  });

  let response = http.post(url, payload, HEADERS);
  check(response, { 'getWallet status was 200': (r) => r.status === 200 });
}

function deductFunds() {
  const url = `${BASE_URL}/CreditsQueue`;
  const payload = JSON.stringify({
    Message: "{\"operationType\":\"deductFunds\",\"data\":{\"owner_id\":\"Some_IID\",\"wallet_number\":10},\"callbackUrl\":\"https://webhook.site/ed326f03-7099-42f9-a591-403a18a1b510\"}",
    MessageGroupId: "default"
  });

  let response = http.post(url, payload, HEADERS);
  check(response, { 'deductFunds status was 200': (r) => r.status === 200 });
}

export default function () {
  readOrder();
  updateOrder();
  addFunds();
  getWallet();
  deductFunds();
}
