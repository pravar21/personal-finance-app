terraform {
  required_version = ">= 1.4.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "data" {
  bucket = var.s3_bucket_name

  tags = var.default_tags
}

resource "aws_iam_role" "lambda_exec" {
  name = "${var.resource_prefix}-lambda-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = var.default_tags
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "s3_writer" {
  name   = "${var.resource_prefix}-s3-writer"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:AbortMultipartUpload"
        ]
        Resource = [
          aws_s3_bucket.data.arn,
          "${aws_s3_bucket.data.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_s3_access" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.s3_writer.arn
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.lambda_function_name}"
  retention_in_days = var.log_retention_days

  tags = var.default_tags
}

resource "aws_lambda_function" "finance_ingest" {
  function_name = var.lambda_function_name
  role          = aws_iam_role.lambda_exec.arn
  handler       = "personal_finance_app.lambda_handler.handler"
  runtime       = "python3.11"
  timeout       = 900
  memory_size   = 512

  filename         = var.lambda_package_path
  source_code_hash = filebase64sha256(var.lambda_package_path)

  environment {
    variables = {
      PLAID_CLIENT_ID = var.plaid_client_id
      PLAID_SECRET    = var.plaid_secret
      PLAID_ENV       = var.plaid_env
      DATA_BUCKET     = aws_s3_bucket.data.bucket
      DATA_PREFIX     = var.data_prefix
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy_attachment.lambda_s3_access,
    aws_cloudwatch_log_group.lambda
  ]

  tags = var.default_tags
}

output "lambda_function_arn" {
  description = "ARN of the personal finance ingestion Lambda function"
  value       = aws_lambda_function.finance_ingest.arn
}

output "data_bucket_name" {
  description = "Name of the S3 bucket that stores exported CSV data"
  value       = aws_s3_bucket.data.bucket
}
