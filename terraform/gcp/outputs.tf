output "frontend_bucket_name" {
  value = google_storage_bucket.frontend.name
}

output "memory_bucket_name" {
  value = google_storage_bucket.memory.name
}

output "artifact_registry_repository_id" {
  value = google_artifact_registry_repository.backend.repository_id
}

output "cloud_run_service_name" {
  value = google_cloud_run_v2_service.backend.name
}

output "api_base_url" {
  value = google_cloud_run_v2_service.backend.uri
}

output "frontend_http_ip" {
  value = var.enable_frontend_load_balancer ? google_compute_global_address.frontend[0].address : null
}

output "frontend_url" {
  value = var.enable_frontend_load_balancer ? "http://${google_compute_global_address.frontend[0].address}" : null
}
