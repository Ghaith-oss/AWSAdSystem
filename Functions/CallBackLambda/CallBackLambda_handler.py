import json
import urllib.request
import boto3
import logging
import decimal

# Initialize SQS and DynamoDB resources
sqs = boto3.client('sqs')

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        elif isinstance(o, bytes):
            return o.decode('utf-8')  # Handle bytes objects
        return super().default(o)

def send_callback(callback_url, data):
    logger.info(f"Sending callback to URL: {callback_url} with data: {data}")
    try:
        req = urllib.request.Request(callback_url, method='POST', data=json.dumps(data, cls=DecimalEncoder).encode('utf-8'))
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req) as response:
            logger.info(f"Callback response: {response.status} - {response.read().decode('utf-8')}")
    except Exception as e:
        logger.error(f"Error sending callback: {e}")

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    if 'Records' in event:
        for record in event['Records']:
            try:
                # Parse SQS message
                message_body = json.loads(record['body'])
                
                # Extract required data directly from message_body
                callback_url = message_body.get('callback_url')
                data = message_body.get('data')

                # Send callback
                send_callback(callback_url, data)
            
            except Exception as e:
                logger.error(f"Error processing SQS record: {e}", exc_info=True)
                continue

    logger.info("CallbackLambda execution completed.")
