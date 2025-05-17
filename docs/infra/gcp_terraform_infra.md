# GCP VM에 Terraform과 Docker Compose로 애플리케이션 배포하기

이 문서는 Google Cloud Platform (GCP)에 Terraform을 사용하여 가상 머신(VM)을 프로비저닝하고, 해당 VM에서 Docker Compose를 사용하여 컨테이너화된 애플리케이션을 실행하는 방법을 안내합니다.

## 목차

1.  [개요](#개요)
2.  [사전 준비 사항](#사전-준비-사항)
3.  [Terraform 구성 파일](#terraform-구성-파일)
    *   [`providers.tf`](#providerstf)
    *   [`main.tf`](#maintf)
    *   [`variables.tf`](#variablestf)
    *   [`outputs.tf`](#outputstf)
4.  [Docker Compose 설정](#docker-compose-설정)
5.  [Terraform 실행](#terraform-실행)
6.  [리소스 삭제](#리소스-삭제)

## 개요

이 Terraform 구성은 다음 리소스를 GCP에 생성합니다:

*   **VPC 네트워크 및 서브넷**: VM을 위한 격리된 네트워크 환경
*   **방화벽 규칙**: SSH (포트 22) 및 HTTP/HTTPS (포트 80, 443) 트래픽 허용
*   **Compute Engine VM 인스턴스**: Docker 및 Docker Compose가 설치되고, 지정된 `docker-compose.yml` 파일을 기반으로 애플리케이션을 실행

## 사전 준비 사항

*   **GCP 계정**: 유효한 GCP 계정과 프로젝트가 필요합니다.
*   **Google Cloud SDK (gcloud CLI)**: 설치 및 인증되어 있어야 합니다.
    *   `gcloud auth application-default login`
*   **Terraform**: 버전 1.0.0 이상이 설치되어 있어야 합니다.
*   **Docker Compose 파일 (`docker-compose.yml`)**: 배포하고자 하는 애플리케이션의 `docker-compose.yml` 파일이 준비되어 있어야 합니다.

## Terraform 구성 파일

프로젝트 루트에 다음 Terraform 파일들을 생성합니다.

### `providers.tf`

GCP 프로바이더를 구성합니다.

```terraform
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}
```

### `main.tf`

주요 인프라 리소스를 정의합니다.

```terraform
# VPC 네트워크 생성
resource "google_compute_network" "vpc_network" {
  name                    = "${var.resource_prefix}-vpc"
  auto_create_subnetworks = false
}

# 서브넷 생성
resource "google_compute_subnetwork" "subnet" {
  name          = "${var.resource_prefix}-subnet"
  ip_cidr_range = "10.0.1.0/24"
  network       = google_compute_network.vpc_network.self_link
  region        = var.gcp_region
}

# 방화벽 규칙: SSH 허용
resource "google_compute_firewall" "allow_ssh" {
  name    = "${var.resource_prefix}-allow-ssh"
  network = google_compute_network.vpc_network.self_link
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  source_ranges = ["0.0.0.0/0"] # 보안을 위해 특정 IP로 제한하는 것이 좋습니다.
  target_tags   = ["ssh-enabled"]
}

# 방화벽 규칙: HTTP/HTTPS 허용 (필요에 따라 포트 조절)
resource "google_compute_firewall" "allow_http_https" {
  name    = "${var.resource_prefix}-allow-http-https"
  network = google_compute_network.vpc_network.self_link
  allow {
    protocol = "tcp"
    ports    = ["80", "443"] # Docker Compose 앱이 사용하는 포트에 맞게 수정
  }
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["http-https-enabled"]
}

# Compute Engine VM 인스턴스 생성
resource "google_compute_instance" "vm_instance" {
  name         = "${var.resource_prefix}-vm"
  machine_type = var.vm_machine_type
  zone         = var.gcp_zone
  tags         = ["ssh-enabled", "http-https-enabled"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2004-lts" # Docker 호환 이미지 선택
    }
  }

  network_interface {
    network    = google_compute_network.vpc_network.self_link
    subnetwork = google_compute_subnetwork.subnet.self_link
    access_config {
      // 외부 IP 할당
    }
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    # Docker 설치
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    sudo apt-get update
    sudo apt-get install -y docker-ce

    # Docker Compose 설치 (최신 버전 확인 필요)
    sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose

    # Docker 서비스 시작 및 활성화
    sudo systemctl start docker
    sudo systemctl enable docker

    # 현재 사용자를 docker 그룹에 추가 (재로그인 필요하나, 스크립트에서는 sudo 사용)
    # sudo usermod -aG docker \$(whoami)

    # docker-compose.yml 파일 생성
    sudo mkdir -p /app
    echo "${var.docker_compose_content}" | sudo tee /app/docker-compose.yml > /dev/null

    # Docker Compose 실행
    cd /app
    sudo docker-compose up -d
  EOT

  service_account {
    scopes = ["cloud-platform"]
  }

  allow_stopping_for_update = true
}
```

### `variables.tf`

Terraform 구성에 사용될 변수를 정의합니다.

```terraform
variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP Region (예: us-central1)"
  type        = string
  default     = "us-central1"
}

variable "gcp_zone" {
  description = "GCP Zone (예: us-central1-a)"
  type        = string
  default     = "us-central1-a"
}

variable "resource_prefix" {
  description = "생성될 리소스 이름의 접두사"
  type        = string
  default     = "dc-app"
}

variable "vm_machine_type" {
  description = "VM 머신 타입"
  type        = string
  default     = "e2-medium"
}

variable "docker_compose_content" {
  description = "배포할 docker-compose.yml 파일의 내용"
  type        = string
  sensitive   = true # 실제 파일 내용은 민감할 수 있으므로 터미널 출력에서 숨김
}
```

### `outputs.tf`

생성된 리소스의 정보를 출력합니다.

```terraform
output "vm_instance_name" {
  description = "생성된 VM 인스턴스의 이름"
  value       = google_compute_instance.vm_instance.name
}

output "vm_instance_external_ip" {
  description = "생성된 VM 인스턴스의 외부 IP 주소"
  value       = google_compute_instance.vm_instance.network_interface[0].access_config[0].nat_ip
}
```

## Docker Compose 설정

`docker-compose.yml` 파일의 내용을 Terraform 변수로 전달해야 합니다. 이를 위해 `terraform.tfvars` 파일을 생성하거나, `terraform apply` 실행 시 `-var` 플래그를 사용할 수 있습니다.

**예시: `terraform.tfvars` 파일 생성**

```
gcp_project_id         = "YOUR_GCP_PROJECT_ID"
docker_compose_content = <<EOT
version: '3.8'
services:
  web:
    image: nginxdemos/hello:latest # 예시 이미지, 실제 앱 이미지로 변경
    ports:
      - "80:80" # VM의 80번 포트를 컨테이너의 80번 포트로 매핑
  # 여기에 다른 서비스들을 추가할 수 있습니다.
EOT
```
**주의**: `docker_compose_content` 변수에 실제 `docker-compose.yml` 파일 내용을 정확히 복사하여 붙여넣거나, `file()` 함수를 사용하여 외부 파일을 읽어올 수 있습니다.
예시 (`variables.tf`의 `docker_compose_content` 기본값 수정 또는 `terraform.tfvars` 사용):
`docker_compose_content = file("path/to/your/docker-compose.yml")`

`startup_script` 내에서 `echo "${var.docker_compose_content}"` 부분이 `docker-compose.yml` 파일 내용을 VM에 기록합니다. 내용이 길거나 복잡한 경우, `filebase64()` 함수를 사용하여 인코딩된 내용을 전달하고 스크립트에서 디코딩하는 방법도 고려할 수 있습니다.

## Terraform 실행

1.  **Terraform 초기화**:
    ```bash
    terraform init
    ```

2.  **Terraform 실행 계획 검토**:
    ```bash
    terraform plan -var-file="terraform.tfvars" # tfvars 파일을 사용하는 경우
    # 또는 변수를 직접 전달
    # terraform plan -var="gcp_project_id=YOUR_ID" -var="docker_compose_content=$(cat path/to/docker-compose.yml)"
    ```

3.  **Terraform 인프라 적용**:
    ```bash
    terraform apply -var-file="terraform.tfvars" # 또는 -var 플래그 사용
    ```
    `yes`를 입력하여 적용을 확인합니다.

적용이 완료되면 `outputs.tf`에 정의된 VM 인스턴스 이름과 외부 IP 주소가 출력됩니다. 해당 IP 주소로 접속하여 애플리케이션이 정상적으로 실행되는지 확인할 수 있습니다.

## 리소스 삭제

생성된 모든 리소스를 삭제하려면 다음 명령을 실행합니다.

```bash
terraform destroy -var-file="terraform.tfvars" # 또는 -var 플래그 사용
```
`yes`를 입력하여 삭제를 확인합니다.

---

**보안 참고 사항**:

*   방화벽 규칙(`allow_ssh`, `allow_http_https`)의 `source_ranges`는 `0.0.0.0/0`으로 설정되어 있어 모든 IP에서의 접근을 허용합니다. 프로덕션 환경에서는 보안을 위해 특정 IP 대역으로 제한하는 것이 강력히 권장됩니다.
*   `docker_compose_content` 변수에 민감한 정보(예: API 키, 비밀번호)가 포함될 경우, GCP Secret Manager와 같은 서비스를 연동하여 안전하게 관리하는 것을 고려하십시오. Terraform에서는 `google_secret_manager_secret_version` 데이터 소스를 사용하여 이를 가져올 수 있습니다.
*   VM 인스턴스의 서비스 계정 권한(`scopes`)은 최소한의 필요한 권한만 부여하는 것이 좋습니다.

이 가이드라인을 바탕으로 실제 환경에 맞게 변수 값과 설정을 조정하여 사용하시기 바랍니다.
