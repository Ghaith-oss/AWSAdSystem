import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 }, // Ramp up to 10 users over 2 minutes
    { duration: '2m', target: 500 }, // Stay at 10 users for 3 minutes
    { duration: '1m', target: 50 },  // Ramp down to 0 users over 2 minutes
  ],
};

const BASE_URL = 'https://l0gmn7llz8.execute-api.eu-north-1.amazonaws.com/dev';
const AUTH_TOKEN = 'eyJraWQiOiJFd0xhRE45MDBYeWVyNjBxQlU4U3g3Mk9TcFVBeWd2OUx2NkpGUHRHaUljPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJkMDljMDk4Yy1mMGYxLTcwODItYzliNy1mMjA2NTMwNTIzMTMiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLmV1LW5vcnRoLTEuYW1hem9uYXdzLmNvbVwvZXUtbm9ydGgtMV9ibzRDOFlWNzIiLCJjb2duaXRvOnVzZXJuYW1lIjoidXNlcnRlc3QiLCJvcmlnaW5fanRpIjoiYjE2ZTYzNzktYjA2NC00MWE5LWI5YmEtNWU1MTQ2N2I4YTM2IiwiYXVkIjoiM3VlY2prbjY5YW4yaTdiZ3VyMjN0NXBtdTIiLCJldmVudF9pZCI6IjUwNTJhOTAwLWI2ZTMtNDNhMy04YmI4LTljZmUxNTM5MzViZSIsInRva2VuX3VzZSI6ImlkIiwiYXV0aF90aW1lIjoxNzE5NDAyMDA4LCJleHAiOjE3MTk1NjUyMDAsImlhdCI6MTcxOTU2MTYwMCwianRpIjoiNGJkMzM3YTAtYzE5NC00YjBhLWJiNzgtMDE0MWZkN2FjYzRjIiwiZW1haWwiOiJnaGFpdGhhbG5hamphcjRAZ21haWwuY29tIn0.oRwqbjbhXYZO9id3HtgVkYbzfGnwwvuEZGT4UeMo1XXGI3V8n_MqRiTKwSAk8_hmaajLsb8f8xi9kMp35xsXL9N1QWDRdOU5m7sYZTwr-llrcReeOYOQQG6DzALAfO6EIenjuB7HaUtldHF1-nvQpX_U41Z5A3S-B_db9GVxsR-ObPeJCmRJWv-wyQBYjQWOcfE_fhg5kxuV1UzEKAfT4ZBXmP1Fkw5ecmapDAKNXO-0E_gab5R3JsWyjhgs6uEFqQTNmV0IhIK4rzMqQRJ0s7l4UHmVS0VzXurk0OV13Of2ID-sCdN4bhvAlzWqRkL8ipTAH2s0jINitST6LGIHoA'; // Replace with your actual auth token
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
