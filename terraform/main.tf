locals {
  ssm_prefix = "/${var.project_name}"

  # Configurazione non segreta -> parametri String
  app_config = {
    LLM_PROVIDER = var.llm_provider
    OLLAMA_MODEL = var.ollama_model
  }

  # Segreti -> parametri SecureString (quelli vuoti non vengono creati)
  app_secrets = {
    APP_USERNAME      = var.app_username
    APP_PASSWORD      = var.app_password
    ANTHROPIC_API_KEY = var.anthropic_api_key
    OPENAI_API_KEY    = var.openai_api_key
  }
}

# ---------------------------------------------------------------------------
# AMI: Deep Learning Base con driver NVIDIA, Docker e NVIDIA Container Toolkit
# ---------------------------------------------------------------------------

data "aws_ami" "dlami" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 22.04) *"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

# ---------------------------------------------------------------------------
# Rete: VPC di default, solo le AZ in cui g4dn.xlarge è disponibile
# ---------------------------------------------------------------------------

data "aws_vpc" "default" {
  default = true
}

data "aws_ec2_instance_type_offerings" "available" {
  location_type = "availability-zone"

  filter {
    name   = "instance-type"
    values = [var.instance_type]
  }
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }

  filter {
    name   = "availability-zone"
    values = data.aws_ec2_instance_type_offerings.available.locations
  }

  filter {
    name   = "default-for-az"
    values = ["true"]
  }
}

resource "aws_security_group" "chatbot" {
  name        = "${var.project_name}-sg"
  description = "Chatbot RAG: UI Gradio e SSH"
  vpc_id      = data.aws_vpc.default.id
}

resource "aws_vpc_security_group_ingress_rule" "app" {
  for_each = toset(var.app_allowed_cidrs)

  security_group_id = aws_security_group.chatbot.id
  description       = "UI Gradio"
  cidr_ipv4         = each.value
  ip_protocol       = "tcp"
  from_port         = 7860
  to_port           = 7860
}

resource "aws_vpc_security_group_ingress_rule" "ssh" {
  for_each = toset(var.ssh_allowed_cidrs)

  security_group_id = aws_security_group.chatbot.id
  description       = "SSH"
  cidr_ipv4         = each.value
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
}

resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.chatbot.id
  description       = "Uscita verso internet (immagini Docker, modelli, API LLM)"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# ---------------------------------------------------------------------------
# Configurazione e segreti in SSM Parameter Store
# ---------------------------------------------------------------------------

resource "aws_ssm_parameter" "config" {
  for_each = local.app_config

  name  = "${local.ssm_prefix}/${each.key}"
  type  = "String"
  value = each.value
}

resource "aws_ssm_parameter" "secret" {
  for_each = toset(nonsensitive([for k, v in local.app_secrets : k if v != ""]))

  name  = "${local.ssm_prefix}/${each.key}"
  type  = "SecureString"
  value = local.app_secrets[each.key]
}

# ---------------------------------------------------------------------------
# IAM: lettura dei parametri + Session Manager
# ---------------------------------------------------------------------------

data "aws_caller_identity" "current" {}

resource "aws_iam_role" "chatbot" {
  name = "${var.project_name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "ssm_params" {
  name = "read-app-parameters"
  role = aws_iam_role.chatbot.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["ssm:GetParametersByPath", "ssm:GetParameters", "ssm:GetParameter"]
      # GetParametersByPath è autorizzata sull'ARN del path stesso, non sui figli
      Resource = [
        "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${local.ssm_prefix}",
        "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${local.ssm_prefix}/*",
      ]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.chatbot.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "chatbot" {
  name = "${var.project_name}-ec2-profile"
  role = aws_iam_role.chatbot.name
}

# ---------------------------------------------------------------------------
# Istanza EC2
# ---------------------------------------------------------------------------

resource "aws_key_pair" "chatbot" {
  key_name   = "${var.project_name}-key"
  public_key = var.ssh_public_key
}

resource "aws_instance" "chatbot" {
  ami                    = data.aws_ami.dlami.id
  instance_type          = var.instance_type
  subnet_id              = data.aws_subnets.default.ids[0]
  vpc_security_group_ids = [aws_security_group.chatbot.id]
  key_name               = aws_key_pair.chatbot.key_name
  iam_instance_profile   = aws_iam_instance_profile.chatbot.name

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_size_gb
    encrypted             = true
    delete_on_termination = true
  }

  metadata_options {
    http_tokens   = "required" # IMDSv2
    http_endpoint = "enabled"
  }

  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    aws_region   = var.aws_region
    ssm_prefix   = local.ssm_prefix
    git_repo_url = var.git_repo_url
    git_branch   = var.git_branch
    enable_gpu   = var.enable_gpu
  })

  tags = {
    Name = var.project_name
  }

  # Una nuova AMI pubblicata da AWS non deve ricreare l'istanza
  lifecycle {
    ignore_changes = [ami]
  }

  depends_on = [aws_ssm_parameter.config, aws_ssm_parameter.secret]
}

resource "aws_eip" "chatbot" {
  instance = aws_instance.chatbot.id
  domain   = "vpc"

  tags = {
    Name = var.project_name
  }
}
