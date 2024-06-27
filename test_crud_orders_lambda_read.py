import pytest
import boto3
import time
import requests
import json

# Replace these with your actual API Gateway endpoints
CRUD_ORDERS_API_ENDPOINT = "https://l0gmn7llz8.execute-api.eu-north-1.amazonaws.com/dev/MyQueue"
CRUD_WALLET_API_ENDPOINT = "https://l0gmn7llz8.execute-api.eu-north-1.amazonaws.com/dev/CreditsQueue"
CALLBACK_QUEUE_URL = "https://sqs.eu-north-1.amazonaws.com/513585459204/CallBackQueue"



AUTH_TOKEN = "eyJraWQiOiJFd0xhRE45MDBYeWVyNjBxQlU4U3g3Mk9TcFVBeWd2OUx2NkpGUHRHaUljPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJkMDljMDk4Yy1mMGYxLTcwODItYzliNy1mMjA2NTMwNTIzMTMiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLmV1LW5vcnRoLTEuYW1hem9uYXdzLmNvbVwvZXUtbm9ydGgtMV9ibzRDOFlWNzIiLCJjb2duaXRvOnVzZXJuYW1lIjoidXNlcnRlc3QiLCJvcmlnaW5fanRpIjoiYjE2ZTYzNzktYjA2NC00MWE5LWI5YmEtNWU1MTQ2N2I4YTM2IiwiYXVkIjoiM3VlY2prbjY5YW4yaTdiZ3VyMjN0NXBtdTIiLCJldmVudF9pZCI6IjUwNTJhOTAwLWI2ZTMtNDNhMy04YmI4LTljZmUxNTM5MzViZSIsInRva2VuX3VzZSI6ImlkIiwiYXV0aF90aW1lIjoxNzE5NDAyMDA4LCJleHAiOjE3MTk1MjA4MDMsImlhdCI6MTcxOTUxNzIwMywianRpIjoiMWQ5OGRlZTctNTI1MS00YmI2LThhNmQtMDRlY2RmMDU4ZDkxIiwiZW1haWwiOiJnaGFpdGhhbG5hamphcjRAZ21haWwuY29tIn0.OU6n2CM5TeRKHdJl7NB4e5pkTGNDPdOmFQ69s0ig77bW3bz9HP0QsGnszi2PoBqcs4utB440PlUqLbdo2klmkUjuv5yH2r3OOeLqs_WdIVYRkV7cjk6tovEFu5HQvxTwsHhdrMIsTMI_G-2QbHBqau39uOltvy0E7WFvO6I3HKvwqzP7fQr6pPde-4wYmecVNdv2SzRgxN8M4msxPJmYgcFSRDBFb4hNzNKWGXcFBqoHy8kXK4nO7jJpM-ltJ1KDC2f__k_0jMBGMOWOCOzRHwge2dWm6eUmrxEgvFD1lB_WbgWNsBO0_6yVHlthqmeefgTiOpcAgGQO6z7OVdI-aw"
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


sqs = boto3.client('sqs')

# Initialize the Lambda client
LAMBDA_FUNCTION_NAME = 'CallbackLambda'
lambda_client = boto3.client('lambda', region_name='eu-north-1')
logs_client = boto3.client('logs', region_name='eu-north-1')

def invoke_lambda_function(payload):
    response = requests.post(CRUD_ORDERS_API_ENDPOINT, headers=HEADERS, json=payload)
    return response

def get_latest_lambda_invocation(lambda_function_name):
    try:
        response = lambda_client.list_invocations(
            FunctionName=lambda_function_name,
            MaxItems=1,
            Qualifier='$LATEST',  # Or specify a version or alias if needed
            # You can add more parameters to filter by specific time or status
        )
        if 'Invocations' in response and response['Invocations']:
            latest_invocation = response['Invocations'][0]
            request_id = latest_invocation['RequestID']
            log_stream_name = latest_invocation['LogStreamName']
            return request_id, log_stream_name
        else:
            print(f"No invocations found for {lambda_function_name}")
            return None, None
    except Exception as e:
        print(f"Error getting latest invocation: {e}")
        return None, None

def fetch_lambda_logs(log_group_name, log_stream_name):
    try:
        response = logs_client.get_log_events(
            logGroupName=log_group_name,
            logStreamName=log_stream_name,
            limit=10,  # Adjust the limit as per your requirement
            startFromHead=True  # Retrieve logs in reverse chronological order
        )

        if 'events' in response:
            return response['events']
        else:
            print("No log events found.")
            return []
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return []

@pytest.mark.parametrize("payload", [TEST_ORDER_READ_PAYLOAD])
def test_lambda_function_execution(payload):
    # Step 1: Invoke the Lambda function
    response = invoke_lambda_function(payload)
    assert response.status_code == 200

    # Step 2: Wait for the invocation to complete and fetch logs
    time.sleep(10)  # Adjust this based on the expected duration of Lambda execution
    request_id, log_stream_name = get_latest_lambda_invocation(LAMBDA_FUNCTION_NAME)
    
    assert request_id is not None and log_stream_name is not None

    logs = fetch_lambda_logs(f'/aws/lambda/{LAMBDA_FUNCTION_NAME}', log_stream_name)
    assert logs, "No logs found for the latest invocation"

    # Step 3: Check for expected log messages
    read_operation_completed = False
    for log in logs:
        if "Read operation completed successfully" in log['message']:
            read_operation_completed = True
            break
    
    assert read_operation_completed, "Expected log message not found"

if __name__ == "__main__":
    pytest.main()