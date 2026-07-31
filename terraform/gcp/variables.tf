variable "project_id" {
  description = "Google Cloud project ID for StudyBuddy resources."
  type        = string
}

variable "region" {
  description = "Google Cloud region for StudyBuddy resources."
  type        = string
  default     = "us-central1"
}

variable "project_name" {
  description = "Project name prefix for Google Cloud resources."
  type        = string
  default     = "studybuddy"
}

variable "environment" {
  description = "Environment name (dev, test, prod)."
  type        = string

  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "Environment must be one of: dev, test, prod."
  }
}

variable "frontend_bucket_name" {
  description = "Cloud Storage bucket name for frontend hosting."
  type        = string
}

variable "memory_bucket_name" {
  description = "Cloud Storage bucket name for chat memory."
  type        = string
}

variable "artifact_registry_repository_id" {
  description = "Artifact Registry repository ID for backend images."
  type        = string
  default     = "studybuddy-backend"
}

variable "cloud_run_service_name" {
  description = "Cloud Run service name for the backend."
  type        = string
  default     = "studybuddy-backend"
}

variable "backend_image_tag" {
  description = "Image tag to deploy to Cloud Run."
  type        = string
  default     = "latest"
}

variable "openai_api_key" {
  description = "OpenAI API key for the backend."
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
  description = "Pinecone API key for the backend."
  type        = string
  sensitive   = true
  default     = ""
}

variable "pinecone_index_name" {
  description = "Pinecone index name for the backend."
  type        = string
  default     = ""
}

variable "cors_allow_origins" {
  description = "Allowed CORS origins for the backend."
  type        = list(string)
  default     = ["*"]
}

variable "make_frontend_bucket_public" {
  description = "Whether to grant public object viewer access to the frontend bucket."
  type        = bool
  default     = true
}

variable "enable_frontend_load_balancer" {
  description = "Whether to expose the frontend bucket through a global HTTP load balancer."
  type        = bool
  default     = true
}

variable "container_port" {
  description = "Container port exposed by Cloud Run."
  type        = number
  default     = 8000
}

variable "cloud_run_timeout" {
  description = "Cloud Run request timeout in seconds."
  type        = number
  default     = 300
}

variable "cloud_run_memory" {
  description = "Cloud Run memory limit."
  type        = string
  default     = "1Gi"
}

variable "cloud_run_cpu" {
  description = "Cloud Run CPU limit."
  type        = string
  default     = "1"
}
