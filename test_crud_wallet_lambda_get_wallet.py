import pytest
import boto3
import time
import requests
import json

# Replace these with your actual API Gateway endpoints
CRUD_ORDERS_API_ENDPOINT = "https://l0gmn7llz8.execute-api.eu-north-1.amazonaws.com/dev/MyQueue"
CRUD_WALLET_API_ENDPOINT = "https://l0gmn7llz8.execute-api.eu-north-1.amazonaws.com/dev/CreditsQueue"
CALLBACK_QUEUE_URL = "https://sqs.eu-north-1.amazonaws.com/513585459204/CallBackQueue"



AUTH_TOKEN = "eyJraWQiOiJFd0xhRE45MDBYeWVyNjBxQlU4U3g3Mk9TcFVBeWd2OUx2NkpGUHRHaUljPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJkMDljMDk4Yy1mMGYxLTcwODItYzliNy1mMjA2NTMwNTIzMTMiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLmV1LW5vcnRoLTEuYW1hem9uYXdzLmNvbVwvZXUtbm9ydGgtMV9ibzRDOFlWNzIiLCJjb2duaXRvOnVzZXJuYW1lIjoidXNlcnRlc3QiLCJvcmlnaW5fanRpIjoiYjE2ZTYzNzktYjA2NC00MWE5LWI5YmEtNWU1MTQ2N2I4YTM2IiwiYXVkIjoiM3VlY2prbjY5YW4yaTdiZ3VyMjN0NXBtdTIiLCJldmVudF9pZCI6IjUwNTJhOTAwLWI2ZTMtNDNhMy04YmI4LTljZmUxNTM5MzViZSIsInRva2VuX3VzZSI6ImlkIiwiYXV0aF90aW1lIjoxNzE5NDAyMDA4LCJleHAiOjE3MTk1MTY1NTIsImlhdCI6MTcxOTUxMjk1MiwianRpIjoiNzY3Mjk2YmItZWViMi00ODgyLWJlNzUtYmI0NDA2Y2YxMTRjIiwiZW1haWwiOiJnaGFpdGhhbG5hamphcjRAZ21haWwuY29tIn0.W2rO-cJkWBUxPdpHlbAt-bqZNMn4q84d7CuirellJ-HJ8T2TwJ9o_3hdDIEswg5Pvrd47ZUqbkPgxbXPwq1_QR8-JH4cBPE4oWrdXpClMzD0HFE8skkGQMYQEWjpH9YC8fIeg3TzKIPDp7IcJF4SahAwcjJgfmRurl0foYUHNhn2Pesmp8sU3sPaFpnO16xrcjpMZw62bwz50TZCT0zKiL2imywnNMp4ml7lHRbB26pD03ZPSc3YeUbJYLC1bftqFEyXVAwORI71bPdW481KleyoDXsJ1t6pSJ8PqltLGK4soEE0aOit6SYkyrOasraIMdchzHycEtauRVw50Yuu6A"
HEADERS = {
    "auth-token": AUTH_TOKEN,
    "Content-Type": "application/json"
}

TEST_WALLET_GET_PAYLOAD = {
    "Message": json.dumps({
        "operationType": "getWallet",
        "data": {"owner_id": "Some_IID"},
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
            print(f"Message received: {messages[0]}")
            receipt_handle = messages[0]['ReceiptHandle']
             # Delete the message from the queue after processing
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            return messages[0]
        print("No messages received, retrying...")
        time.sleep(5)
    print("Failed to receive message after max attempts")
    return None

def fetch_most_recent_lambda_log(lambda_function_name):
    client = boto3.client('logs', region_name='eu-north-1')
    
    try:
        response = client.describe_log_streams(
            logGroupName=f'/aws/lambda/{lambda_function_name}',
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        log_stream_name = response['logStreams'][0]['logStreamName']
        
        log_events_response = client.get_log_events(
            logGroupName=f'/aws/lambda/{lambda_function_name}',
            logStreamName=log_stream_name,
            limit=1,
            startFromHead=True
        )
        
        if 'events' in log_events_response and len(log_events_response['events']) > 2:
            log_event = log_events_response['events'][2]
            print(f"Log Event retrieved:\n{log_event}")
            return log_events_response['events'][0]
        else:
            return None
    except ClientError as e:
        print(f"Error fetching logs: {e}")
        return None

def test_crud_wallet_lambda_get_wallet():
    response = send_message_to_api(CRUD_WALLET_API_ENDPOINT, TEST_WALLET_GET_PAYLOAD)
    assert response.status_code == 200

    log_event = fetch_most_recent_lambda_log('CallbackLambda') 
    assert log_event is not None
    assert "Wallet retrieved successfully" in log_event['message']
    

if __name__ == "__main__":
    pytest.main()