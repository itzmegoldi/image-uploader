#!/bin/bash

set -e

STACK_NAME="my-api"
REGION="ap-south-1"
BUCKET_NAME="image-bucket"

# echo "======================================"
# if awslocal s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
#     echo "S3 bucket '$BUCKET_NAME' already exists. Skipping."
# else
#     echo "Creating S3 bucket '$BUCKET_NAME'..."
#     awslocal s3 mb "s3://$BUCKET_NAME"
# fi



echo "======================================"
echo " Building SAM application"
echo "======================================"

sam build \
  --template-file template.yaml

echo ""
echo "======================================"
echo " Deploying to LocalStack"
echo "======================================"

samlocal deploy \
  --template-file .aws-sam/build/template.yaml \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --capabilities CAPABILITY_IAM \
  --resolve-s3 \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset

echo ""
echo "======================================"
echo " Deployment completed"
echo "======================================"

echo ""
echo "CloudFormation:"
awslocal cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION"

echo ""
echo "Lambda functions:"
awslocal --region "$REGION" lambda list-functions

echo ""
echo "API Gateway:"
awslocal --region "$REGION" apigateway get-rest-apis




# awslocal --region ap-south-1 lambda invoke \
#   --function-name my-api-ImageFunction-56af14c3 \
#   --payload '{}' \
#   response.json


# awslocal cloudformation delete-stack \
#   --stack-name my-api \
#   --region ap-south-1


# awslocal logs describe-log-groups --region ap-south-1    

# awslocal --region ap-south-1 logs filter-log-events \    
#   --log-group-name "/aws/lambda/my-api-ImageFunction-56af14c3"


# awslocal --region ap-south-1 logs tail /aws/lambda/my-api-ImageFunction-56af14c3 --since 30m

# awslocal --region ap-south-1 cloudformation delete-stack \
#   --stack-name my-api