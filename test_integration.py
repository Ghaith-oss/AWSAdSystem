import pytest
import boto3
import time
import requests
import json

# Replace these with your actual API Gateway endpoints
CRUD_ORDERS_API_ENDPOINT = "https://l0gmn7llz8.execute-api.eu-north-1.amazonaws.com/dev/MyQueue"
CRUD_WALLET_API_ENDPOINT = "https://l0gmn7llz8.execute-api.eu-north-1.amazonaws.com/dev/CreditsQueue"
CALLBACK_QUEUE_URL = "https://sqs.eu-north-1.amazonaws.com/513585459204/CallBackQueue"



AUTH_TOKEN = "eyJraWQiOiJFd0xhRE45MDBYeWVyNjBxQlU4U3g3Mk9TcFVBeWd2OUx2NkpGUHRHaUljPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJkMDljMDk4Yy1mMGYxLTcwODItYzliNy1mMjA2NTMwNTIzMTMiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLmV1LW5vcnRoLTEuYW1hem9uYXdzLmNvbVwvZXUtbm9ydGgtMV9ibzRDOFlWNzIiLCJjb2duaXRvOnVzZXJuYW1lIjoidXNlcnRlc3QiLCJvcmlnaW5fanRpIjoiNDU3ZDRmYmYtODdkZS00OGRhLWE2YTItZGU0ZjdkZDQ0M2FmIiwiYXVkIjoiM3VlY2prbjY5YW4yaTdiZ3VyMjN0NXBtdTIiLCJldmVudF9pZCI6IjJkZjRiNzk0LWU4NjctNGViMS04NWE3LTkwMWE2OTcyYTViYyIsInRva2VuX3VzZSI6ImlkIiwiYXV0aF90aW1lIjoxNzE4OTE5OTIzLCJleHAiOjE3MTk0MDE5MDQsImlhdCI6MTcxOTM5ODMwNCwianRpIjoiZWZiZDVkNDItMmYwNy00OGM4LTkyNDAtNTM0ZWQ5MGNlZmU2IiwiZW1haWwiOiJnaGFpdGhhbG5hamphcjRAZ21haWwuY29tIn0.Bq3iOMqw_MCZO1k7jeO0yKe1sQYBaqecjnD8uNa-1hPmPLkTNGnEdzJYtT0ZW4b1ZM1Ap66lVQ0Yy1dSQxgmZDXw0oxZre_cxjjWNHfqpLGb6dMMkVYQvCI4R0EVuTMFmBiNwQ8lQ7a8jo7ENjkp5KZe2hqmq1a6Wwm93vluZ2gtRCup36XbUPgvaAiKif0NhmuYFYaBnpjVKnKB3HDSZxq0jWMdNSXuzEMFRL3ey-G4CLKkJL_9aIVGDJfW3vdA22rNRi5aPlJcJnHncmKbmmTUOGcThP9AwNK5SvtqB2cCAiOwR3yQZDzQgoRL6gu41ak75CkR-NsaOK3-GTORJQ"
HEADERS = {
    "auth-token": AUTH_TOKEN,
    "Content-Type": "application/json"
}

# Replace with actual payloads
TEST_ORDER_READ_PAYLOAD = {
    "Message": json.dumps({
        "operationType": "readOrder",
        "data": {"table_name": "devices"},
        "callbackUrl": "https://webhook.site/ed326f03-7099-42f9-a591-403a18a1b510"
    }),
    "MessageGroupId": "default"
}

TEST_ORDER_UPDATE_PAYLOAD = {
    "Message": json.dumps({
        "operationType": "updateOrder",
        "data": {
            "table_name": "devices",
            "ids": ["1", "2"],
            "new_order_owner": "owner_name",
            "new_order_time": "2024-06-21T12:00:00Z",
            "new_order_Url": "http://example.com/order"
        },
        "callbackUrl": "https://webhook.site/ed326f03-7099-42f9-a591-403a18a1b510"
    }),
    "MessageGroupId": "default"
}

TEST_WALLET_ADD_FUNDS_PAYLOAD = {
    "Message": json.dumps({
        "operationType": "addFunds",
        "data": {"owner_id": "Some_IID", "wallet_number": 100},
        "callbackUrl": "https://webhook.site/ed326f03-7099-42f9-a591-403a18a1b510"
    }),
    "MessageGroupId": "default"
}

TEST_WALLET_GET_PAYLOAD = {
    "Message": json.dumps({
        "operationType": "getWallet",
        "data": {"owner_id": "Some_IID"},
        "callbackUrl": "https://webhook.site/ed326f03-7099-42f9-a591-403a18a1b510"
    }),
    "MessageGroupId": "default"
}

TEST_WALLET_DEDUCT_FUNDS_PAYLOAD = {
    "Message": json.dumps({
        "operationType": "deductFunds",
        "data": {"owner_id": "Some_IID", "wallet_number": 10},
        "callbackUrl": "https://webhook.site/ed326f03-7099-42f9-a591-403a18a1b510"
    }),
    "MessageGroupId": "default"
}

sqs = boto3.client('sqs')

def send_message_to_api(endpoint, payload):
    response = requests.post(endpoint, headers=HEADERS, json=payload)
    return response

def receive_message_from_queue(queue_url, wait_time=20, max_attempts=3):
    for attempt in range(max_attempts):
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=wait_time,
        )
        messages = response.get('Messages', [])
        if messages:
            return messages[0]
        time.sleep(5)
    return None

def test_crud_orders_lambda_read():
    response = send_message_to_api(CRUD_ORDERS_API_ENDPOINT, TEST_ORDER_READ_PAYLOAD)
    assert response.status_code == 200

    message = receive_message_from_queue(CALLBACK_QUEUE_URL)
    assert message is not None
    assert "Read operation completed successfully" in message["Body"]

def test_crud_orders_lambda_update():
    response = send_message_to_api(CRUD_ORDERS_API_ENDPOINT, TEST_ORDER_UPDATE_PAYLOAD)
    assert response.status_code == 200

    message = receive_message_from_queue(CALLBACK_QUEUE_URL)
    assert message is not None
    assert "Update operation completed successfully" in message["Body"]

def test_crud_wallet_lambda_add_funds():
    response = send_message_to_api(CRUD_WALLET_API_ENDPOINT, TEST_WALLET_ADD_FUNDS_PAYLOAD)
    assert response.status_code == 200

    message = receive_message_from_queue(CALLBACK_QUEUE_URL)
    assert message is not None
    assert "Funds added successfully" in message["Body"]

def test_crud_wallet_lambda_get_wallet():
    response = send_message_to_api(CRUD_WALLET_API_ENDPOINT, TEST_WALLET_GET_PAYLOAD)
    assert response.status_code == 200

    message = receive_message_from_queue(CALLBACK_QUEUE_URL)
    assert message is not None
    assert "Wallet retrieved successfully" in message["Body"]

def test_crud_wallet_lambda_deduct_funds():
    response = send_message_to_api(CRUD_WALLET_API_ENDPOINT, TEST_WALLET_DEDUCT_FUNDS_PAYLOAD)
    assert response.status_code == 200

    message = receive_message_from_queue(CALLBACK_QUEUE_URL)
    assert message is not None
    assert "Funds deducted successfully" in message["Body"]

if __name__ == "__main__":
    pytest.main()
