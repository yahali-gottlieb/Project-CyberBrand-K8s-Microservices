# 1. Create VPC
resource "aws_vpc" "main_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "DevOps-Project-VPC"
  }
}

# 2. Create Internet Gateway
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main_vpc.id

  tags = {
    Name = "DevOps-IGW"
  }
}

# 3. Create Route Table for Public Subnets
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.main_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "DevOps-Public-RT"
  }
}

# 4. Create Public Subnet 1 (AZ a)
resource "aws_subnet" "public_subnet_1" {
  vpc_id                  = aws_vpc.main_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "${var.aws_region}a"

  tags = {
    Name = "DevOps-Public-Subnet-1"
  }
}

# 5. Create Public Subnet 2 (AZ b)
resource "aws_subnet" "public_subnet_2" {
  vpc_id                  = aws_vpc.main_vpc.id
  cidr_block              = "10.0.2.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "${var.aws_region}b"

  tags = {
    Name = "DevOps-Public-Subnet-2"
  }
}

# 6. Create Private Subnet 1 (AZ a) - For RDS
resource "aws_subnet" "private_subnet_1" {
  vpc_id                  = aws_vpc.main_vpc.id
  cidr_block              = "10.0.3.0/24"
  map_public_ip_on_launch = false
  availability_zone       = "${var.aws_region}a"

  tags = {
    Name = "DevOps-Private-Subnet-1"
  }
}

# 7. Create Private Subnet 2 (AZ b) - For RDS
resource "aws_subnet" "private_subnet_2" {
  vpc_id                  = aws_vpc.main_vpc.id
  cidr_block              = "10.0.4.0/24"
  map_public_ip_on_launch = false
  availability_zone       = "${var.aws_region}b"

  tags = {
    Name = "DevOps-Private-Subnet-2"
  }
}

# 8. Associate Route Tables
resource "aws_route_table_association" "public_assoc_1" {
  subnet_id      = aws_subnet.public_subnet_1.id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_route_table_association" "public_assoc_2" {
  subnet_id      = aws_subnet.public_subnet_2.id
  route_table_id = aws_route_table.public_rt.id
}

# 9. Security Group for RDS (Restricted to VPC internal traffic)
resource "aws_security_group" "rds_sg" {
  name        = "devops-rds-sg"
  description = "Allow inbound PostgreSQL traffic from VPC only"
  vpc_id      = aws_vpc.main_vpc.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main_vpc.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "DevOps-RDS-SG"
  }
}