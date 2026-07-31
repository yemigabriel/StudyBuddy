provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  common_labels = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
  }
  backend_image_uri = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.backend.repository_id}/${var.cloud_run_service_name}:${var.backend_image_tag}"
}

resource "google_project_service" "required" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "compute.googleapis.com",
    "run.googleapis.com",
    "storage.googleapis.com",
  ])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "backend" {
  depends_on = [google_project_service.required]

  location      = var.region
  repository_id = var.artifact_registry_repository_id
  description   = "StudyBuddy backend container images"
  format        = "DOCKER"
}

resource "google_storage_bucket" "frontend" {
  name                        = var.frontend_bucket_name
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false
  labels                      = local.common_labels

  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html"
  }
}

resource "google_storage_bucket_iam_member" "frontend_public" {
  count  = var.make_frontend_bucket_public ? 1 : 0
  bucket = google_storage_bucket.frontend.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

resource "google_compute_backend_bucket" "frontend" {
  count = var.enable_frontend_load_balancer ? 1 : 0

  name        = "${var.project_name}-frontend-backend"
  description = "StudyBuddy static frontend bucket"
  bucket_name = google_storage_bucket.frontend.name
  enable_cdn  = false
}

resource "google_compute_global_address" "frontend" {
  count = var.enable_frontend_load_balancer ? 1 : 0

  name = "${var.project_name}-frontend-ip"
}

resource "google_compute_url_map" "frontend" {
  count = var.enable_frontend_load_balancer ? 1 : 0

  name            = "${var.project_name}-frontend-map"
  default_service = google_compute_backend_bucket.frontend[0].id
}

resource "google_compute_target_http_proxy" "frontend" {
  count = var.enable_frontend_load_balancer ? 1 : 0

  name    = "${var.project_name}-frontend-http-proxy"
  url_map = google_compute_url_map.frontend[0].id
}

resource "google_compute_global_forwarding_rule" "frontend" {
  count = var.enable_frontend_load_balancer ? 1 : 0

  name                  = "${var.project_name}-frontend-http"
  ip_protocol           = "TCP"
  load_balancing_scheme = "EXTERNAL"
  port_range            = "80"
  target                = google_compute_target_http_proxy.frontend[0].id
  ip_address            = google_compute_global_address.frontend[0].address
}

resource "google_storage_bucket" "memory" {
  name                        = var.memory_bucket_name
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false
  labels                      = local.common_labels

  versioning {
    enabled = true
  }
}

resource "google_service_account" "backend" {
  account_id   = replace(var.cloud_run_service_name, "_", "-")
  display_name = "StudyBuddy backend service account"
}

resource "google_storage_bucket_iam_member" "memory_access" {
  bucket = google_storage_bucket.memory.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_cloud_run_v2_service" "backend" {
  depends_on = [google_project_service.required]

  name     = var.cloud_run_service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.backend.email
    timeout         = "${var.cloud_run_timeout}s"

    containers {
      image = local.backend_image_uri

      resources {
        limits = {
          cpu    = var.cloud_run_cpu
          memory = var.cloud_run_memory
        }
      }

      ports {
        container_port = var.container_port
      }

      env {
        name  = "OPENAI_API_KEY"
        value = var.openai_api_key
      }

      env {
        name  = "VECTOR_DB"
        value = var.vector_db
      }

      env {
        name  = "MEMORY_BACKEND"
        value = "gcs"
      }

      env {
        name  = "STUDYBUDDY_MEMORY_BUCKET"
        value = google_storage_bucket.memory.name
      }

      env {
        name  = "CORS_ALLOW_ORIGINS"
        value = join(",", var.cors_allow_origins)
      }

      env {
        name  = "PINECONE_API_KEY"
        value = var.pinecone_api_key
      }

      env {
        name  = "PINECONE_INDEX_NAME"
        value = var.pinecone_index_name
      }
    }
  }
}

resource "google_cloud_run_service_iam_member" "public_invoker" {
  location = google_cloud_run_v2_service.backend.location
  service  = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "terraform_data" "frontend_publish" {
  depends_on = [
    google_storage_bucket.frontend,
    google_cloud_run_v2_service.backend,
  ]

  provisioner "local-exec" {
    command     = "NEXT_PUBLIC_API_BASE_URL=${google_cloud_run_v2_service.backend.uri} NEXT_PUBLIC_ASSET_PREFIX= npm run build && gcloud storage rsync --recursive --delete-unmatched-destination-objects out gs://${google_storage_bucket.frontend.name}"
    working_dir = "${path.module}/../../frontend"
  }
}
