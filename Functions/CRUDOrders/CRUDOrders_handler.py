import json
import boto3
import logging
import decimal
import urllib.request

# Initialize a DynamoDB resource
dynamo = boto3.resource('dynamodb')

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
        # Handle SQS records
        for record in event['Records']:
            try:
                logger.info(f"Received record: {record}")
                message_body = json.loads(record['body'])
                logger.info(f"Parsed message body: {message_body}")

                http_method = message_body.get('httpMethod')
                operation_type = message_body.get('operationType')
                data = message_body.get('data', {})
                callback_url = message_body.get('callbackUrl', None)

                table_name = data.get('table_name', '')
                ids = data.get('ids', [])
                new_order_owner = data.get('new_order_owner', '')
                new_order_time = data.get('new_order_time', 0)
                new_order_Url = data.get('new_order_Url', '')

                operation_result = {}
                if operation_type == 'updateOrder':
                    if not table_name or not ids or not new_order_owner or new_order_time <= 0 or not new_order_Url:
                        logger.error(f"Missing required fields in the message: {data}")
                        continue
                    update_results = update_orders(table_name, ids, new_order_owner, new_order_time, new_order_Url)
                    operation_result['status'] = 'success'
                    operation_result['message'] = 'Order update operation completed successfully'
                    operation_result['data'] = update_results
                    operation_result['callback_url'] = callback_url
                    if callback_url:
                        send_callback(callback_url, operation_result)
                elif operation_type == 'readOrder':
                    if not table_name:
                        logger.error(f"Missing required table_name for read operation: {data}")
                        continue
                    items = get_all_items(table_name)
                    logger.info(f"Read items: {items}")
                    operation_result['status'] = 'success'
                    operation_result['message'] = 'Order read operation completed successfully'
                    operation_result['data'] = items
                    operation_result['callback_url'] = callback_url
                    if callback_url:
                        send_callback(callback_url, operation_result)
            except Exception as e:
                logger.error(f"Unhandled exception: {e}", exc_info=True)
                continue
    elif 'callbackUrl' in event:
        # Handle callback
        callback_url = event.get('callbackUrl')
        message = event.get('message', 'No message')
        send_callback(callback_url, message)
