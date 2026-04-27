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

variable "lambda_zip_path" {
  description = "Path to the packaged Lambda zip file."
  type        = string
  default     = "../backend/dist/studybuddy-backend.zip"
}
