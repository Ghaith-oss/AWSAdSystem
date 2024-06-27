import pytest
import boto3
import time
import requests
import json

# Replace these with your actual API Gateway endpoints
CRUD_ORDERS_API_ENDPOINT = "https://l0gmn7llz8.execute-api.eu-north-1.amazonaws.com/dev/MyQueue"
CRUD_WALLET_API_ENDPOINT = "https://l0gmn7llz8.execute-api.eu-north-1.amazonaws.com/dev/CreditsQueue"
CALLBACK_QUEUE_URL = "https://sqs.eu-north-1.amazonaws.com/513585459204/CallBackQueue"



AUTH_TOKEN = "eyJraWQiOiJFd0xhRE45MDBYeWVyNjBxQlU4U3g3Mk9TcFVBeWd2OUx2NkpGUHRHaUljPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJkMDljMDk4Yy1mMGYxLTcwODItYzliNy1mMjA2NTMwNTIzMTMiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLmV1LW5vcnRoLTEuYW1hem9uYXdzLmNvbVwvZXUtbm9ydGgtMV9ibzRDOFlWNzIiLCJjb2duaXRvOnVzZXJuYW1lIjoidXNlcnRlc3QiLCJvcmlnaW5fanRpIjoiYjE2ZTYzNzktYjA2NC00MWE5LWI5YmEtNWU1MTQ2N2I4YTM2IiwiYXVkIjoiM3VlY2prbjY5YW4yaTdiZ3VyMjN0NXBtdTIiLCJldmVudF9pZCI6IjUwNTJhOTAwLWI2ZTMtNDNhMy04YmI4LTljZmUxNTM5MzViZSIsInRva2VuX3VzZSI6ImlkIiwiYXV0aF90aW1lIjoxNzE5NDAyMDA4LCJleHAiOjE3MTk1MjkxMDAsImlhdCI6MTcxOTUyNTUwMCwianRpIjoiZGUyNzFhOTEtOGYwZC00NmMwLWFlNTctYTEyOTIwOWZkMTg5IiwiZW1haWwiOiJnaGFpdGhhbG5hamphcjRAZ21haWwuY29tIn0.W9hA65D_JVoFszPnsJh36jXgXIAlvWqCUCwSV7g8_VCGv4ziEGkagyjWKuRmuMyYyZYTGbkaccRa1g6gfFQx6jXKXlSrvVSOkoMWmYkt9IOTmVa3ARgm8PCqso5DFDyMA2MEHDPota3gXAZ2OKMNPUFtErkONLpaFxSgWlzMpqXiRD6dx2urR-95pPTtN7goDMLiTgxXTvwncZAPuLGnKxLtGF3SvZYfA0KlUrcMbArx3DG9mFmrr8_cHWHctHn7qMt-WX5OfRT3YOsJcWdgOv9pdwJCBxQMmq0iEoAoPhSFdP35CkU3F6sTaqLdkHMJw3WT8_abxXLT0gOekR-U0A"
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

# Initialize the Lambda client
LAMBDA_FUNCTION_NAME = 'CallbackLambda'
lambda_client = boto3.client('lambda', region_name='eu-north-1')
logs_client = boto3.client('logs', region_name='eu-north-1')

def invoke_lambda_function(payload):
    response = requests.post(CRUD_WALLET_API_ENDPOINT, headers=HEADERS, json=payload)
    return response

def get_most_recent_log_stream(log_group_name):
    try:
        response = logs_client.describe_log_streams(
            logGroupName=log_group_name,
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        if 'logStreams' in response and response['logStreams']:
            log_stream_name = response['logStreams'][0]['logStreamName']
            return log_stream_name
        else:
            print(f"No log streams found for {log_group_name}")
            return None
    except Exception as e:
        print(f"Error getting log streams: {e}")
        return None

def fetch_lambda_logs(log_group_name, log_stream_name):
    try:
        response = logs_client.get_log_events(
            logGroupName=log_group_name,
            logStreamName=log_stream_name,
            limit=65,  
            startFromHead=True  
        )

        if 'events' in response:
            return response['events']
        else:
            print("No log events found.")
            return []
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return []

@pytest.mark.parametrize("payload", [TEST_WALLET_GET_PAYLOAD])
def test_lambda_function_execution(payload):
    # Step 1: Invoke the Lambda function
    response = invoke_lambda_function(payload)
    assert response.status_code == 200

    # Step 2: Wait for the invocation to complete and fetch logs
    time.sleep(30)  

    # Get the log group name associated with the Lambda function
    log_group_name = f'/aws/lambda/{LAMBDA_FUNCTION_NAME}'

    # Fetch the most recent log stream
    log_stream_name = get_most_recent_log_stream(log_group_name)
    assert log_stream_name is not None, f"No log streams found for {log_group_name}"

    # Fetch logs from the retrieved log stream
    logs = fetch_lambda_logs(log_group_name, log_stream_name)
    assert logs, "No logs found for the latest invocation"

    # Check for expected log messages
    read_operation_completed = False
    for log in logs:
        print(f"LOGS: {log}")
        if "Wallet retrieved successfully" in log['message']:
            read_operation_completed = True
            break
    
    assert read_operation_completed, "Expected log message not found"
    

if __name__ == "__main__":
    pytest.main()