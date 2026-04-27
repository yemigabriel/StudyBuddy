output "frontend_bucket_name" {
  value = aws_s3_bucket.frontend.bucket
}

output "memory_bucket_name" {
  value = aws_s3_bucket.memory.bucket
}

output "ecr_repository_url" {
  value = aws_ecr_repository.backend.repository_url
}

output "api_base_url" {
  value = aws_apigatewayv2_stage.default.invoke_url
}

output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.frontend.domain_name
}
