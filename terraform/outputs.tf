output "public_ip" {
  description = "IP pubblico (Elastic IP) dell'istanza."
  value       = aws_eip.chatbot.public_ip
}

output "app_url" {
  description = "URL della UI del chatbot."
  value       = "http://${aws_eip.chatbot.public_ip}:7860"
}

output "ssh_command" {
  description = "Comando SSH (richiede ssh_allowed_cidrs)."
  value       = "ssh ubuntu@${aws_eip.chatbot.public_ip}"
}

output "ssm_session_command" {
  description = "Accesso alla shell senza SSH, via Session Manager."
  value       = "aws ssm start-session --region ${var.aws_region} --target ${aws_instance.chatbot.id}"
}

output "instance_id" {
  value = aws_instance.chatbot.id
}

output "ami_name" {
  value = data.aws_ami.dlami.name
}
