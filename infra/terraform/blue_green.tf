# Blue/Green deployment stubs

variable "active_color" {
  type    = string
  default = "blue" # blue|green
}

resource "aws_lb_target_group" "api_blue" {
  name     = "api-blue-${var.environment}"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = var.vpc_id
  health_check {
    protocol = "HTTP"
    path     = "/healthz"
  }
}

resource "aws_lb_target_group" "api_green" {
  name     = "api-green-${var.environment}"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = var.vpc_id
  health_check {
    protocol = "HTTP"
    path     = "/healthz"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.app.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = var.active_color == "blue" ? aws_lb_target_group.api_blue.arn : aws_lb_target_group.api_green.arn
  }
}


