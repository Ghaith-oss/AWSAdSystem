import json
import boto3
import logging
import decimal
import urllib.request

# Initialize a DynamoDB resource
dynamo = boto3.resource('dynamodb')
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

def get_all_items(table_name):
    logger.info(f"Getting all items from table: {table_name}")
    table = dynamo.Table(table_name)
    logger.info(f"boto3 version: {boto3.__version__}")  # Check boto3 version
    try:
        response = table.scan()
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting items: {e}")
        raise e

def update_orders(table_name, ids, new_order_owner, new_order_time, new_order_Url):
    logger.info(f"Updating orders for table: {table_name}, IDs: {ids}, New order owner: {new_order_owner}, "
                f"New order time: {new_order_time}, New order URL: {new_order_Url}")
    table = dynamo.Table(table_name)
    update_results = []
    for id in ids:
        try:
            response = table.update_item(
                Key={'ID': id},
                UpdateExpression="SET OrdersOwner = list_append(if_not_exists(OrdersOwner, :empty_list), :owner), "
                                 "OrdersTimespan = list_append(if_not_exists(OrdersTimespan, :empty_list), :timespan), "
                                 "OrdersUrl = list_append(if_not_exists(OrdersUrl, :empty_list), :url)",
                ExpressionAttributeValues={
                    ':owner': [new_order_owner],
                    ':timespan': [new_order_time],
                    ':url': [new_order_Url],
                    ':empty_list': []
                },
                ReturnValues='UPDATED_NEW'
            )
            update_results.append({'ID': id, 'status': 'success', 'response': response})
        except Exception as e:
            logger.error(f"Error updating order for ID {id}: {e}")
            update_results.append({'ID': id, 'status': 'error', 'error': str(e)})
    return update_results
    
def enqueue_operation(message, queue_url):
    try:
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message, cls=DecimalEncoder),  # Use DecimalEncoder here
        )
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Operation queued for processing'}, cls=DecimalEncoder)  # Use DecimalEncoder here
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
                table_name = data.get('table_name', '')
                ids = data.get('ids', [])
                new_order_owner = data.get('new_order_owner', '')  # Extract new_order_owner
                new_order_time = data.get('new_order_time', '')  # Extract new_order_time
                new_order_Url = data.get('new_order_Url', '')  # Extract new_order_Url
                operation_result = {}

                if operation_type == 'updateOrder':
                    if not table_name:
                        logger.error(f"Missing required table_name for update operation: {data}")
                        continue
                    
                    # Handle updateOrder logic
                    update_results = update_orders(table_name, ids, new_order_owner, new_order_time, new_order_Url)
                    operation_result['status'] = 'success'
                    operation_result['message'] = f"Update operation completed successfully"
                    operation_result['data'] = update_results
                    operation_result['callback_url'] = callback_url

                elif operation_type == 'readOrder':
                    if not table_name:
                        logger.error(f"Missing required table_name for read operation: {data}")
                        continue
                    
                    # Handle readOrder logic
                    items = get_all_items(table_name)
                    operation_result['status'] = 'success'
                    operation_result['message'] = f"Read operation completed successfully"
                    operation_result['data'] = items
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
