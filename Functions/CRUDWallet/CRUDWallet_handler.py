import json
import boto3
import logging
import decimal
import urllib.request

# Initialize DynamoDB resource
dynamo = boto3.resource('dynamodb')
table = dynamo.Table('Credits')

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

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    try:
        if 'Records' in event:
            for record in event['Records']:
                try:
                    logger.info(f"Received record: {record}")
                    message_body = json.loads(record['body'])
                    logger.info(f"Parsed message body: {message_body}")

                    http_method = message_body.get('httpMethod')
                    operation_type = message_body.get('operationType')
                    data = message_body.get('data', {})
                    callback_url = message_body.get('callbackUrl', None)

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
                    else:
                        logger.error(f"Unsupported operation type: {operation_type}")
                        continue

                    if callback_url:
                        send_callback(callback_url, operation_result)
                except Exception as e:
                    logger.error(f"Unhandled exception: {e}", exc_info=True)
                    continue
        elif 'callbackUrl' in event:
            callback_url = event.get('callbackUrl')
            message = event.get('message', 'No message')
            send_callback(callback_url, message)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
