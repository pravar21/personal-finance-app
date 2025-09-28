variable "aws_region" {
  description = "AWS region to deploy the personal finance backend"
  type        = string
  default     = "us-east-1"
}

variable "resource_prefix" {
  description = "Prefix used when naming AWS resources"
  type        = string
  default     = "personal-finance"
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket that stores exported CSV data. Must be globally unique."
  type        = string
}

variable "lambda_function_name" {
  description = "Name of the AWS Lambda function"
  type        = string
  default     = "personal-finance-export"
}

variable "lambda_package_path" {
  description = "Path to the packaged Lambda deployment ZIP"
  type        = string
  default     = "../dist/lambda.zip"
}

variable "plaid_client_id" {
  description = "Plaid client identifier"
  type        = string
}

variable "plaid_secret" {
  description = "Plaid client secret"
  type        = string
  sensitive   = true
}

variable "plaid_env" {
  description = "Plaid environment (sandbox, development, or production)"
  type        = string
  default     = "sandbox"
}

variable "data_prefix" {
  description = "Prefix for objects written into the S3 data bucket"
  type        = string
  default     = "personal-finance"
}

variable "log_retention_days" {
  description = "Number of days to keep Lambda execution logs"
  type        = number
  default     = 14
}

variable "default_tags" {
  description = "Tags applied to all managed AWS resources"
  type        = map(string)
  default     = {}
}
