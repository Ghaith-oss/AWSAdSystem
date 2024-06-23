#!/bin/bash
echo "Running AfterInstall script..."

# Update the Lambda functions with the new code directly from the zip files
echo "Updating CRUDOrders Lambda function..."
aws lambda update-function-code --function-name CRUDOrdersLambdaFunction --zip-file fileb:///tmp/CRUDOrders.zip

echo "Updating CRUDWallet Lambda function..."
aws lambda update-function-code --function-name CRUDWalletLambdaFunction --zip-file fileb:///tmp/CRUDWallet.zip

echo "Updating CallBackLambda function..."
aws lambda update-function-code --function-name CallBackLambdaFunction --zip-file fileb:///tmp/CallBackLambda.zip
