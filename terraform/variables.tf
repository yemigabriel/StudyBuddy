variable "aws_region" {
  description = "AWS region for StudyBuddy infrastructure."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name prefix for AWS resources."
  type        = string
  default     = "studybuddy"
}

variable "frontend_bucket_name" {
  description = "S3 bucket name for frontend hosting."
  type        = string
}

variable "memory_bucket_name" {
  description = "S3 bucket name for chat memory."
  type        = string
}

variable "ecr_repository_name" {
  description = "ECR repository name for the backend Lambda image."
  type        = string
  default     = "studybuddy-backend"
}

variable "lambda_image_tag" {
  description = "Tag to publish and deploy for the backend Lambda image."
  type        = string
  default     = "latest"
}

variable "openai_api_key" {
  description = "OpenAI API key for Lambda"
  type        = string
  sensitive   = true
}

variable "vector_db" {
  description = "Vector database backend to use."
  type        = string
  default     = "chroma"

  validation {
    condition     = contains(["chroma", "pinecone"], var.vector_db)
    error_message = "vector_db must be one of: chroma, pinecone."
  }
}

variable "pinecone_api_key" {
  description = "Pinecone API key for Lambda."
  type        = string
  sensitive   = true
  default     = ""
}

variable "pinecone_index_name" {
  description = "Pinecone index name for Lambda."
  type        = string
  default     = ""
}

variable "cors_allow_origins" {
  description = "Allowed CORS origins for the HTTP API."
  type        = list(string)
  default     = []
}

variable "cors_allow_methods" {
  description = "Allowed CORS methods for the HTTP API."
  type        = list(string)
  default     = ["GET", "POST", "OPTIONS"]
}

variable "cors_allow_headers" {
  description = "Allowed CORS headers for the HTTP API."
  type        = list(string)
  default     = ["*"]
}

variable "environment" {
  description = "Environment name (dev, test, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "Environment must be one of: dev, test, prod."
  }
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 60
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 1024
}

variable "api_throttle_burst_limit" {
  description = "API Gateway throttle burst limit"
  type        = number
  default     = 10
}

variable "api_throttle_rate_limit" {
  description = "API Gateway throttle rate limit"
  type        = number
  default     = 5
}
