resource "aws_ecs_cluster" "api" {
  name = "bertil-${var.environment}"
}

resource "aws_iam_role" "ecs_task_execution" {
  name = "bertil-ecs-exec-${var.environment}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_exec_attach" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

locals {
  api_container = jsonencode([
    {
      name      = "api",
      image     = var.api_image,
      essential = true,
      portMappings = [{ containerPort = 8000, hostPort = 8000 }],
      environment = [
        { name = "PORT", value = "8000" }
      ]
    }
  ])
  worker_container = jsonencode([
    {
      name      = "worker",
      image     = var.worker_image,
      essential = true
    }
  ])
}

resource "aws_ecs_task_definition" "api" {
  family                   = "bertil-api-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.ecs_task_cpu
  memory                   = var.ecs_task_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  container_definitions    = local.api_container
}

resource "aws_ecs_task_definition" "worker" {
  family                   = "bertil-worker-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.ecs_task_cpu
  memory                   = var.ecs_task_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  container_definitions    = local.worker_container
}

resource "aws_ecs_service" "api_blue" {
  name            = "api-blue-${var.environment}"
  cluster         = aws_ecs_cluster.api.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.ecs_desired_count
  launch_type     = "FARGATE"
  network_configuration {
    subnets         = var.ecs_subnet_ids
    security_groups = [var.ecs_security_group_id]
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.api_blue.arn
    container_name   = "api"
    container_port   = 8000
  }
}

resource "aws_ecs_service" "api_green" {
  name            = "api-green-${var.environment}"
  cluster         = aws_ecs_cluster.api.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 0
  launch_type     = "FARGATE"
  network_configuration {
    subnets         = var.ecs_subnet_ids
    security_groups = [var.ecs_security_group_id]
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.api_green.arn
    container_name   = "api"
    container_port   = 8000
  }
}


