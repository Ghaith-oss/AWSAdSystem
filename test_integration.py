import pytest
import boto3
import time
import requests
import json

# Replace these with your actual API Gateway endpoints
CRUD_ORDERS_API_ENDPOINT = "https://l0gmn7llz8.execute-api.eu-north-1.amazonaws.com/dev/MyQueue"
CRUD_WALLET_API_ENDPOINT = "https://l0gmn7llz8.execute-api.eu-north-1.amazonaws.com/dev/CreditsQueue"
CALLBACK_QUEUE_URL = "https://sqs.eu-north-1.amazonaws.com/513585459204/CallBackQueue"



AUTH_TOKEN = "eyJraWQiOiJFd0xhRE45MDBYeWVyNjBxQlU4U3g3Mk9TcFVBeWd2OUx2NkpGUHRHaUljPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJkMDljMDk4Yy1mMGYxLTcwODItYzliNy1mMjA2NTMwNTIzMTMiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLmV1LW5vcnRoLTEuYW1hem9uYXdzLmNvbVwvZXUtbm9ydGgtMV9ibzRDOFlWNzIiLCJjb2duaXRvOnVzZXJuYW1lIjoidXNlcnRlc3QiLCJvcmlnaW5fanRpIjoiYjE2ZTYzNzktYjA2NC00MWE5LWI5YmEtNWU1MTQ2N2I4YTM2IiwiYXVkIjoiM3VlY2prbjY5YW4yaTdiZ3VyMjN0NXBtdTIiLCJldmVudF9pZCI6IjUwNTJhOTAwLWI2ZTMtNDNhMy04YmI4LTljZmUxNTM5MzViZSIsInRva2VuX3VzZSI6ImlkIiwiYXV0aF90aW1lIjoxNzE5NDAyMDA4LCJleHAiOjE3MTk1MDM3NjYsImlhdCI6MTcxOTUwMDE2NiwianRpIjoiNWIxM2Y1MjYtMWRlNS00M2Q1LTk5NTAtM2NhMDU2ZTBlYTY2IiwiZW1haWwiOiJnaGFpdGhhbG5hamphcjRAZ21haWwuY29tIn0.I_vCeko2yrX_uQ1AFjBSSopEtTgAYFwoBRVT_3gYA8EpUMXGLvGUQp_0uHQ8-KKFWgldhF9aZIxAJ4aClB8Ol1SWcWyjNDiKi4jXf9ib626S_-GdQFB0WIsEiG1B26L2t3g50x-GklBR4JYBhFA3eDQVzIzS69hGQ0ttrMzR9Fcsnv6KQhzeJNlT4yOewZauQHgEataqiGvPOgbicQilWWJB_6ssOTaVtYIh4RHQe-r_MG5QHG7k56MpcDjgeabupTTMPZA6IFxOFQVnjnu7VzIEVF5rmZlY30wa5riHQGGU1K39UCtlgA40qbErD0ul3XvJn9YsbNImhOQxGKaNKg"
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

def receive_message_from_queue(queue_url, wait_time=20, max_attempts=5):
    for attempt in range(max_attempts):
        print(f"Attempt {attempt + 1} to receive message from {queue_url}")
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=wait_time,
        )
        messages = response.get('Messages', [])
        if messages:
             message = messages[0]
            receipt_handle = message['ReceiptHandler']
            print(f"Message received: {message}")

            # Delete the message from the queue after processing
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandler=receipt_handle
            )
            print("Message deleted from the queue")
            return messages[0]
        print("No messages received, retrying...")
        time.sleep(5)
    print("Failed to receive message after max attempts")
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
