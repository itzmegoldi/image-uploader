# Image Uploader API

A serverless image management API built using **AWS Lambda, API Gateway, Amazon S3, DynamoDB, AWS SAM, and LocalStack**.

The API provides the following operations:

- Upload an image
- List images for a user
- Generate a presigned download URL
- Delete an image

The entire AWS infrastructure is defined using **AWS SAM / CloudFormation** and can be run locally using **LocalStack**.

---

## Architecture

```text
                         ┌─────────────────┐
                         │     Client      │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │  API Gateway    │
                         │   (LocalStack)   │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │     Lambda      │
                         │  ImageFunction  │
                         └───────┬─┬───────┘
                                 │ │
                    ┌────────────┘ └────────────┐
                    ▼                           ▼
             ┌──────────────┐           ┌──────────────┐
             │   DynamoDB   │           │      S3      │
             │    Metadata  │           │ Image Files  │
             └──────────────┘           └──────────────┘
```

### AWS Services

| Service        | Purpose                                       |
| -------------- | --------------------------------------------- |
| API Gateway    | Exposes HTTP APIs                             |
| Lambda         | Handles API requests                          |
| S3             | Stores image files                            |
| DynamoDB       | Stores image metadata                         |
| CloudFormation | Manages infrastructure                        |
| AWS SAM        | Builds and deploys the serverless application |
| LocalStack     | Runs AWS services locally                     |

---

# Prerequisites

Make sure the following are installed on your system:

- Docker
- LocalStack
- AWS CLI
- AWS SAM CLI

Verify the installations:

```bash
docker --version
localstack --version
aws --version
sam --version
```

---

# LocalStack

Make sure **LocalStack is running before deploying the application**.

For example:

```bash
localstack start
```

You should be able to access LocalStack at:

```text
http://localhost:4566
```

You can verify that LocalStack is running with:

```bash
awslocal --region ap-south-1 s3 ls
```

---

# Project Setup

Clone the repository and move into the project directory:

```bash
git clone <repository-url>
cd image-uploader
```

Make the development script executable:

```bash
chmod +x dev.sh
```

Run the development/deployment script:

```bash
bash dev.sh
```

The script builds the SAM application and deploys the infrastructure to LocalStack.

---

# Getting the API Gateway ID

After the deployment completes, the script prints the API Gateway information.

Example:

```json
{
  "items": [
    {
      "id": "3md7nmsgdi",
      "name": "my-api-ServerlessRestApi-d3a4c422",
      "createdDate": "2026-08-30T23:18:56+05:30",
      "version": "1.0",
      "apiKeySource": "HEADER",
      "endpointConfiguration": {
        "types": ["EDGE"],
        "ipAddressType": "ipv4"
      },
      "tags": {
        "aws:cloudformation:logical-id": "ServerlessRestApi",
        "aws:cloudformation:stack-name": "my-api",
        "aws:cloudformation:stack-id": "arn:aws:cloudformation:ap-south-1:000000000000:stack/my-api/651f14e9-037b-4618-99d2-92f7e68c8bf0"
      },
      "disableExecuteApiEndpoint": false,
      "rootResourceId": "qmpwpmswaw"
    }
  ]
}
```

Copy the value of:

```text
"id": "3md7nmsgdi"
```

In this example:

```text
api-id = 3md7nmsgdi
```

The API Gateway URL format is:

```text
http://localhost:4566/_aws/execute-api/<api-id>/Prod/<endpoint>
```

Replace `<api-id>` with the API Gateway ID returned by the deployment.

---

# API Endpoints

## 1. Upload Image

Uploads an image to S3 and stores its metadata in DynamoDB.

### Endpoint

```http
POST /upload-image
```

### cURL

Replace `<api-id>` with your API Gateway ID.

```bash
curl --location \
  'http://localhost:4566/_aws/execute-api/<api-id>/Prod/upload-image' \
  --form 'user_id="123"' \
  --form 'image=@"/Users/prashant/Documents/screenshot/Screenshot 2026-07-28 at 11.45.17 PM.png"'
```

### Request

The request uses `multipart/form-data`.

| Field     | Type   | Description                        |
| --------- | ------ | ---------------------------------- |
| `user_id` | string | ID of the user uploading the image |
| `image`   | file   | Image to upload                    |

### Example

```text
user_id = 123
image = screenshot.png
```

The image is stored in S3 using a key similar to:

```text
123/<image-id>/screenshot.png
```

Image metadata is stored in DynamoDB using:

```text
PK = USER#123
SK = IMAGE#<image-id>
```

---

# 2. List Images

Returns images belonging to a user.

### Endpoint

```http
GET /list-images
```

### cURL

```bash
curl --location \
  'http://localhost:4566/_aws/execute-api/<api-id>/Prod/list-images?user_id=123'
```

### Request Parameters

| Parameter    | Required | Description                              |
| ------------ | -------- | ---------------------------------------- |
| `user_id`    | Yes      | ID of the user                           |
| `page_size`  | No       | Number of records to return              |
| `next_token` | No       | Token returned from the previous request |

### Example

```bash
curl --location \
  'http://localhost:4566/_aws/execute-api/<api-id>/Prod/list-images?user_id=123&page_size=10'
```

### Pagination

The API uses DynamoDB's `LastEvaluatedKey` for pagination.

The response contains a `next_token` when more records are available.

Example:

```json
{
  "items": [
    {
      "image_id": "0239e41f-205a-4a37-ab6f-3075dbcdb3b1",
      "filename": "screenshot.png",
      "content_type": "image/png",
      "size": 32183,
      "created_at": 1788105015
    }
  ],
  "page_size": 10,
  "next_token": "<token>"
}
```

The returned token can be supplied in the next request:

```text
GET /list-images?user_id=123&page_size=10&next_token=<token>
```

---

# 3. Generate Download URL

Generates an S3 presigned URL for an image.

The API first verifies that the image belongs to the specified user and then generates a temporary download URL.

### Endpoint

```http
GET /get-download-url
```

### cURL

```bash
curl --location \
  'http://localhost:4566/_aws/execute-api/<api-id>/Prod/get-download-url?user_id=123&image_id=0239e41f-205a-4a37-ab6f-3075dbcdb3b1'
```

### Request Parameters

| Parameter  | Required | Description     |
| ---------- | -------- | --------------- |
| `user_id`  | Yes      | ID of the user  |
| `image_id` | Yes      | ID of the image |

### Example Response

```json
{
  "url": "http://localhost:4566/..."
}
```

The returned URL can be used to download the image directly from S3.

The presigned URL is temporary and expires after the configured expiration period.

---

# 4. Delete Image

Deletes an image and its associated metadata.

### Endpoint

```http
DELETE /delete-image
```

### cURL

```bash
curl --location \
  --request DELETE \
  'http://localhost:4566/_aws/execute-api/<api-id>/Prod/delete-image?user_id=123&image_id=0239e41f-205a-4a37-ab6f-3075dbcdb3b1'
```

### Request Parameters

| Parameter  | Required | Description     |
| ---------- | -------- | --------------- |
| `user_id`  | Yes      | ID of the user  |
| `image_id` | Yes      | ID of the image |

The delete operation removes:

1. The image from S3
2. The image metadata from DynamoDB

---

# API Summary

| Method   | Endpoint            | Description                       |
| -------- | ------------------- | --------------------------------- |
| `POST`   | `/upload-image`     | Upload an image                   |
| `GET`    | `/list-images`      | List user's images                |
| `GET`    | `/get-download-url` | Generate a presigned download URL |
| `DELETE` | `/delete-image`     | Delete an image                   |

---

# DynamoDB Data Model

Each image is stored using the following key structure:

```text
PK = USER#<user_id>
SK = IMAGE#<image_id>
```

Example:

```text
PK = USER#123
SK = IMAGE#0239e41f-205a-4a37-ab6f-3075dbcdb3b1
```

An image record contains metadata similar to:

```json
{
  "PK": "USER#123",
  "SK": "IMAGE#0239e41f-205a-4a37-ab6f-3075dbcdb3b1",
  "image_id": "0239e41f-205a-4a37-ab6f-3075dbcdb3b1",
  "user_id": "123",
  "filename": "screenshot.png",
  "content_type": "image/png",
  "size": 32183,
  "s3_key": "123/0239e41f-205a-4a37-ab6f-3075dbcdb3b1/screenshot.png",
  "created_at": 1788105015,
  "updated_at": 1788105015
}
```

---

# S3 Storage Structure

Images are stored using the following structure:

```text
<user_id>/<image_id>/<filename>
```

Example:

```text
123/
└── 0239e41f-205a-4a37-ab6f-3075dbcdb3b1/
    └── screenshot.png
```

DynamoDB stores the S3 key so that the application can locate the corresponding image when generating a presigned URL or deleting the image.

---

# Deployment

The `dev.sh` script handles the local deployment.

The general flow is:

```text
dev.sh
  │
  ├── SAM build
  │
  ├── Package Lambda
  │
  ├── Upload deployment artifacts
  │
  ├── CloudFormation deployment
  │
  ├── Create/Update Lambda
  │
  ├── Create/Update API Gateway
  │
  ├── Create/Update DynamoDB
  │
  └── Create/Update S3
```

To deploy changes:

```bash
bash dev.sh
```

---

# Troubleshooting

## LocalStack is not running

Verify:

```bash
awslocal --region ap-south-1 s3 ls
```

If the command cannot connect, start LocalStack:

```bash
localstack start
```

---

## Lambda import error

If you see:

```text
Unable to import module
```

make sure all Python dependencies are declared in your project dependency configuration and are included during:

```bash
sam build
```

Then redeploy:

```bash
bash dev.sh
```

---

## API Gateway returns 502

Check the Lambda logs:

```bash
awslocal --region ap-south-1 logs describe-log-groups
```

Then inspect the appropriate Lambda log group:

```bash
awslocal --region ap-south-1 logs filter-log-events \
  --log-group-name "/aws/lambda/<lambda-function-name>"
```

---

## Check CloudFormation stack

```bash
awslocal --region ap-south-1 cloudformation describe-stacks \
  --stack-name my-api
```

Check stack resources:

```bash
awslocal --region ap-south-1 cloudformation describe-stack-resources \
  --stack-name my-api
```

---

# Development Workflow

For normal development:

```bash
# 1. Start LocalStack
localstack start

# 2. Make the script executable
chmod +x dev.sh

# 3. Build and deploy
bash dev.sh

# 4. Copy the API Gateway ID from the output

# 5. Test the APIs using cURL
```

---

# Local AWS Endpoint

All AWS services used by this project are running through LocalStack.

The LocalStack endpoint is:

```text
http://localhost:4566
```

For AWS CLI operations, `awslocal` can be used instead of configuring the LocalStack endpoint manually:

```bash
awslocal --region ap-south-1 dynamodb list-tables
```

```bash
awslocal --region ap-south-1 s3 ls
```

```bash
awslocal --region ap-south-1 lambda list-functions
```

```bash
awslocal --region ap-south-1 apigateway get-rest-apis
```
