variable "project_name" {
  description = "Name of the project, used in resource naming"
  type        = string
  default     = "ecommerce-pipeline"
}

variable "region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "account_id" {
  description = "AWS account ID, used in globally unique bucket naming"
  type        = string

}


