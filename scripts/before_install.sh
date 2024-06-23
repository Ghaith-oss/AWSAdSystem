#!/bin/bash
echo "Running BeforeInstall script..."
aws s3 cp s3://deployment-ad-system/AdSystemPipeLine/BuildArtif/CRUDOrders.zip /tmp/CRUDOrders.zip
aws s3 cp s3://deployment-ad-system/AdSystemPipeLine/BuildArtif/CRUDWallet.zip /tmp/CRUDWallet.zip
aws s3 cp s3://deployment-ad-system/AdSystemPipeLine/BuildArtif/CallBackLambda.zip /tmp/CallBackLambda.zip
