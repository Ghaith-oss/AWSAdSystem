import json
import boto3
import logging
import decimal
import urllib.request

# Initialize DynamoDB resource
dynamo = boto3.resource('dynamodb')
table = dynamo.Table('Credits')

# Initialize an SQS client
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

def add_funds(owner_id, wallet_number):
    logger.info(f"Adding funds: {wallet_number} to owner: {owner_id}")
    response = table.get_item(Key={'Owner_id': owner_id})
    if 'Item' in response:
        current_wallet = response['Item'].get('Wallet', 0)
        new_wallet = current_wallet + wallet_number
        table.update_item(
            Key={'Owner_id': owner_id},
            UpdateExpression='SET Wallet = :val',
            ExpressionAttributeValues={':val': decimal.Decimal(new_wallet)}
        )
    else:
        # Add a new wallet with initial value if the user does not exist
        table.put_item(Item={'Owner_id': owner_id, 'Wallet': decimal.Decimal(wallet_number)})

def deduct_funds(owner_id, wallet_number):
    logger.info(f"Deducting funds: {wallet_number} from owner: {owner_id}")
    response = table.get_item(Key={'Owner_id': owner_id})
    if 'Item' in response:
        current_wallet = response['Item'].get('Wallet', 0)
        if current_wallet < wallet_number:
            raise ValueError("Insufficient funds")
        new_wallet = current_wallet - wallet_number
        table.update_item(
            Key={'Owner_id': owner_id},
            UpdateExpression='SET Wallet = :val',
            ExpressionAttributeValues={':val': decimal.Decimal(new_wallet)}
        )
    else:
        raise ValueError("Wallet not found")

def get_wallet(owner_id):
    logger.info(f"Retrieving wallet for owner: {owner_id}")
    response = table.get_item(Key={'Owner_id': owner_id})
    if 'Item' not in response:
        logger.warning(f"No wallet found for owner_id: {owner_id}. Creating new wallet with 0 value.")
        # Add a new wallet with 0 value if the user does not exist
        table.put_item(Item={'Owner_id': owner_id, 'Wallet': decimal.Decimal(0)})
        return {'Owner_id': owner_id, 'Wallet': decimal.Decimal(0)}
    return response['Item']

def enqueue_operation(message, queue_url):
    try:
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message, cls=DecimalEncoder),  # Use DecimalEncoder here
        )
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Operation queued for processing-V110'}, cls=DecimalEncoder)  # Use DecimalEncoder here
        }
    except Exception as e:
        logger.error(f"Error enqueuing message: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to enqueue operation'}, cls=DecimalEncoder)  # Use DecimalEncoder here
        }

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event, cls=DecimalEncoder)}")  # Use DecimalEncoder here

    if 'Records' in event:
        # Handle SQS records
        for record in event['Records']:
            try:
                logger.info(f"Received record: {record}")
                message_body = json.loads(record['body'])
                message = json.loads(message_body['Message'])  # Parse 'Message' JSON
                logger.info(f"Parsed message body: {message}")

                operation_type = message.get('operationType')
                data = message.get('data', {})
                callback_url = message.get('callbackUrl', None)
                owner_id = data.get('owner_id', '')
                wallet_number = decimal.Decimal(data.get('wallet_number', 0))
                operation_result = {}
              
                if operation_type == 'addFunds':
                    if not owner_id or wallet_number <= 0:
                        logger.error(f"Missing required fields for addFunds operation: {data}")
                        continue
                    add_funds(owner_id, wallet_number)
                    wallet = get_wallet(owner_id)
                    operation_result['status'] = 'success'
                    operation_result['message'] = 'Funds added successfully'
                    operation_result['data'] = wallet
                    operation_result['callback_url'] = callback_url
                elif operation_type == 'deductFunds':
                    if not owner_id or wallet_number <= 0:
                        logger.error(f"Missing required fields for deductFunds operation: {data}")
                        continue
                    try:
                        deduct_funds(owner_id, wallet_number)
                        wallet = get_wallet(owner_id)
                        operation_result['status'] = 'success'
                        operation_result['message'] = 'Funds deducted successfully'
                        operation_result['data'] = wallet
                        operation_result['callback_url'] = callback_url
                    except ValueError as e:
                        operation_result['status'] = 'error'
                        operation_result['message'] = str(e)
                       
                elif operation_type == 'getWallet':
                    if not owner_id:
                        logger.error(f"Missing required fields for getWallet operation: {data}")
                        continue
                    wallet = get_wallet(owner_id)
                    operation_result['status'] = 'success'
                    operation_result['message'] = 'Wallet retrieved successfully'
                    operation_result['data'] = wallet
                    operation_result['callback_url'] = callback_url
                else:
                    logger.error(f"Unknown operation type: {operation_type}")
                    continue

                if callback_url:
                    queue_url = 'https://sqs.eu-north-1.amazonaws.com/513585459204/CallBackQueue'
                    enqueue_operation(operation_result, queue_url)

            except Exception as e:
                logger.error(f"Unhandled exception: {e}", exc_info=True)
                continue

    logger.info("CallbackLambda execution completed.")
