provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

locals {
  lambda_name = "${var.project_name}-backend"
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
  effective_cors_allow_origins = length(var.cors_allow_origins) > 0 ? var.cors_allow_origins : [
    "https://${aws_cloudfront_distribution.frontend.domain_name}"
  ]
  lambda_environment = merge(
    {
      STUDYBUDDY_MEMORY_BUCKET = aws_s3_bucket.memory.bucket
      OPENAI_API_KEY           = var.openai_api_key
      VECTOR_DB                = var.vector_db
      CORS_ALLOW_ORIGINS       = join(",", local.effective_cors_allow_origins)
    },
    var.vector_db == "pinecone" ? {
      PINECONE_API_KEY    = var.pinecone_api_key
      PINECONE_INDEX_NAME = var.pinecone_index_name
    } : {}
  )
  backend_source_files = concat(
    [
      "Dockerfile.lambda",
      "requirements.txt",
      "server.py",
    ],
    tolist(fileset("${path.module}/../backend/app", "**"))
  )
  backend_source_hash = sha1(
    join(
      "",
      [
        for file in sort(local.backend_source_files) :
        filemd5(
          contains(["Dockerfile.lambda", "requirements.txt", "server.py"], file)
          ? "${path.module}/../backend/${file}"
          : "${path.module}/../backend/app/${file}"
        )
      ]
    )
  )
  frontend_source_files = concat(
    [
      "next.config.ts",
      "package.json",
      "package-lock.json",
      "tsconfig.json",
      "postcss.config.js",
      "tailwind.config.ts",
    ],
    tolist(fileset("${path.module}/../frontend/app", "**"))
  )
  frontend_source_hash = sha1(
    join(
      "",
      [
        for file in sort(local.frontend_source_files) :
        filemd5(
          contains(
            [
              "next.config.ts",
              "package.json",
              "package-lock.json",
              "tsconfig.json",
              "postcss.config.js",
              "tailwind.config.ts",
            ],
            file
          )
          ? "${path.module}/../frontend/${file}"
          : "${path.module}/../frontend/app/${file}"
        )
      ]
    )
  )
  lambda_image_uri = "${aws_ecr_repository.backend.repository_url}:${var.lambda_image_tag}"
}

resource "aws_ecr_repository" "backend" {
  name                 = var.ecr_repository_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

data "aws_ecr_image" "backend" {
  depends_on = [terraform_data.backend_image]

  repository_name = aws_ecr_repository.backend.name
  image_tag       = var.lambda_image_tag
}

resource "terraform_data" "backend_image" {
  triggers_replace = [
    local.backend_source_hash,
    var.lambda_image_tag,
    aws_ecr_repository.backend.repository_url,
  ]

  provisioner "local-exec" {
    command     = "python3 deploy.py --ecr-uri ${local.lambda_image_uri}"
    working_dir = "${path.module}/../backend"
  }
}

resource "aws_s3_bucket" "frontend" {
  bucket = var.frontend_bucket_name
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket     = aws_s3_bucket.frontend.id
  depends_on = [aws_s3_bucket_public_access_block.frontend]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = ["s3:GetObject"]
        Resource  = ["${aws_s3_bucket.frontend.arn}/*"]
      }
    ]
  })
}

resource "aws_s3_bucket" "memory" {
  bucket = var.memory_bucket_name
}

resource "aws_s3_bucket_versioning" "memory" {
  bucket = aws_s3_bucket.memory.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}-lambda-role"

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
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "memory_access" {
  name = "${var.project_name}-memory-access"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
        Resource = [
          aws_s3_bucket.memory.arn,
          "${aws_s3_bucket.memory.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_lambda_function" "backend" {
  depends_on    = [terraform_data.backend_image]
  function_name = local.lambda_name
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.backend.repository_url}@${data.aws_ecr_image.backend.image_digest}"
  role          = aws_iam_role.lambda_exec.arn
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  environment {
    variables = local.lambda_environment
  }
}

resource "aws_apigatewayv2_api" "http" {
  name          = "${var.project_name}-http-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = local.effective_cors_allow_origins
    allow_methods = var.cors_allow_methods
    allow_headers = var.cors_allow_headers
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.backend.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.backend.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  default_root_object = "index.html"

  origin {
    domain_name = aws_s3_bucket_website_configuration.frontend.website_endpoint
    origin_id   = "frontend-s3-website"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "frontend-s3-website"

    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

resource "terraform_data" "frontend_publish" {
  depends_on = [
    aws_s3_bucket.frontend,
    aws_apigatewayv2_stage.default,
    aws_cloudfront_distribution.frontend,
  ]

  triggers_replace = [
    local.frontend_source_hash,
    aws_s3_bucket.frontend.bucket,
    aws_apigatewayv2_stage.default.invoke_url,
    aws_cloudfront_distribution.frontend.id,
  ]

  provisioner "local-exec" {
    command     = "npm ci && NEXT_PUBLIC_API_BASE_URL=${aws_apigatewayv2_stage.default.invoke_url} npm run build && aws s3 sync out/ s3://${aws_s3_bucket.frontend.bucket} --delete && aws cloudfront create-invalidation --distribution-id ${aws_cloudfront_distribution.frontend.id} --paths '/*'"
    working_dir = "${path.module}/../frontend"
  }
}
