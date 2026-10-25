# --- Infrastruttura ---

variable "aws_region" {
  description = "Regione AWS (eu-south-1 è opt-in: va abilitata nell'account)."
  type        = string
  default     = "eu-south-1"
}

variable "project_name" {
  description = "Prefisso per i nomi delle risorse e per il path dei parametri SSM."
  type        = string
  default     = "chatbot-rag"
}

variable "instance_type" {
  description = "Tipo di istanza EC2 (GPU NVIDIA T4 16 GB su g4dn.xlarge)."
  type        = string
  default     = "g4dn.xlarge"
}

variable "enable_gpu" {
  description = "Assegna la GPU al container Ollama. false per test su istanze senza GPU (es. t3.xlarge)."
  type        = bool
  default     = true
}

variable "root_volume_size_gb" {
  description = "Disco root gp3 in GB (la Deep Learning AMI occupa già ~75 GB)."
  type        = number
  default     = 150
}

variable "ssh_public_key" {
  description = "Contenuto della chiave pubblica SSH (es. il file ~/.ssh/id_ed25519.pub)."
  type        = string
}

variable "ssh_allowed_cidrs" {
  description = "CIDR autorizzati alla porta 22 (es. [\"1.2.3.4/32\"]). Lista vuota = SSH chiuso, si accede con SSM Session Manager."
  type        = list(string)
  default     = []
}

variable "app_allowed_cidrs" {
  description = "CIDR autorizzati alla UI sulla porta 7860."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# --- Applicazione ---

variable "git_repo_url" {
  description = "Repo Git da clonare in /opt/chatbot al primo avvio. Vuoto = codice copiato a mano (scp/rsync)."
  type        = string
  default     = ""
}

variable "git_branch" {
  description = "Branch da clonare."
  type        = string
  default     = "main"
}

variable "llm_provider" {
  description = "ollama | anthropic | openai"
  type        = string
  default     = "ollama"

  validation {
    condition     = contains(["ollama", "anthropic", "openai"], var.llm_provider)
    error_message = "llm_provider deve essere ollama, anthropic o openai."
  }
}

variable "ollama_model" {
  description = "Modello Ollama scaricato automaticamente all'avvio."
  type        = string
  default     = "llama3.1:8b"
}

# --- Segreti (salvati come SecureString in SSM Parameter Store) ---

variable "app_username" {
  description = "Username della pagina di login."
  type        = string
  sensitive   = true
}

variable "app_password" {
  description = "Password della pagina di login."
  type        = string
  sensitive   = true
}

variable "anthropic_api_key" {
  description = "API key Anthropic (solo con llm_provider = anthropic)."
  type        = string
  sensitive   = true
  default     = ""
}

variable "openai_api_key" {
  description = "API key OpenAI (solo con llm_provider = openai)."
  type        = string
  sensitive   = true
  default     = ""
}
