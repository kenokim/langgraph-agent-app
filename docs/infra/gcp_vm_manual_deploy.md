# GCP VM 수동 생성 및 Docker Compose 환경 구축 가이드

이 문서는 Google Cloud Platform (GCP)에서 가상 머신(VM)을 수동으로 생성하고, 해당 VM에 Docker와 Docker Compose를 설치한 후, `docker-compose.yml` 파일을 사용하여 애플리케이션 환경을 구축하는 과정을 단계별로 안내합니다.

## 목차

1.  [사전 준비 사항](#사전-준비-사항)
2.  [GCP VM 인스턴스 생성](#gcp-vm-인스턴스-생성)
    *   [GCP Console을 이용한 방법](#gcp-console을-이용한-방법)
    *   [gcloud CLI를 이용한 방법](#gcloud-cli를-이용한-방법)
3.  [VM에 SSH로 접속](#vm에-ssh로-접속)
4.  [VM에 Docker 및 Docker Compose 설치](#vm에-docker-및-docker-compose-설치)
    *   [Docker 설치](#docker-설치)
    *   [Docker Compose 설치](#docker-compose-설치)
5.  [애플리케이션 배포](#애플리케이션-배포)
    *   [`docker-compose.yml` 파일 준비 및 VM에 복사/클론](#docker-composeyml-파일-준비-및-vm에-복사클론)
    *   [Docker Compose 애플리케이션 실행](#docker-compose-애플리케이션-실행)
6.  [애플리케이션 확인](#애플리케이션-확인)
7.  [고정 IP 주소 할당 (선택 사항)](#고정-ip-주소-할당-선택-사항)
8.  [리소스 정리](#리소스-정리)

## 사전 준비 사항

*   **GCP 계정**: 유효한 GCP 계정과 프로젝트가 필요합니다.
*   **Google Cloud SDK (gcloud CLI)**: (선택 사항) `gcloud` 명령어를 사용하여 VM을 생성하고 관리할 경우 필요합니다. 설치 및 인증되어 있어야 합니다.
*   **SSH 클라이언트**: VM에 접속하기 위해 필요합니다. (Linux/macOS는 터미널, Windows는 PuTTY, WSL 또는 Windows Terminal 사용)
*   **`docker-compose.yml` 파일**: 배포하고자 하는 애플리케이션의 `docker-compose.yml` 파일이 로컬에 준비되어 있어야 합니다.

## GCP VM 인스턴스 생성

VM 인스턴스는 GCP Console 또는 `gcloud` CLI를 사용하여 생성할 수 있습니다.

### GCP Console을 이용한 방법

1.  **GCP Console 접속**: [Google Cloud Console](https://console.cloud.google.com/)에 로그인합니다.
2.  **프로젝트 선택**: VM을 생성할 GCP 프로젝트를 선택합니다.
3.  **Compute Engine으로 이동**: 탐색 메뉴(햄버거 아이콘)에서 "Compute Engine" > "VM 인스턴스"를 선택합니다.
4.  **인스턴스 만들기**: "인스턴스 만들기" 또는 "만들기" 버튼을 클릭합니다.
5.  **인스턴스 구성**:
    *   **이름**: VM 인스턴스의 이름을 입력합니다. (예: `my-app-vm`)
    *   **리전 및 영역**: 애플리케이션을 배포할 리전과 영역을 선택합니다. (예: `us-central1`, `us-central1-a`)
    *   **머신 구성**:
        *   **시리즈**: 원하는 시리즈 선택 (예: `E2`)
        *   **머신 유형**: 애플리케이션 사양에 맞는 머신 유형을 선택합니다. (예: `e2-medium` - vCPU 2개, 메모리 4GB)
    *   **부팅 디스크**:
        *   "변경"을 클릭합니다.
        *   **운영체제**: `Ubuntu` (또는 선호하는 Linux 배포판)
        *   **버전**: `Ubuntu 20.04 LTS` (또는 최신 LTS 버전) 와 같이 Docker를 지원하는 버전을 선택합니다.
        *   **크기**: 애플리케이션 및 데이터에 필요한 디스크 크기를 설정합니다.
        *   "선택"을 클릭합니다.
    *   **ID 및 API 액세스**: 기본값 또는 필요에 따라 서비스 계정 권한을 조정합니다.
    *   **방화벽**:
        *   `HTTP 트래픽 허용` 체크박스를 선택합니다. (애플리케이션이 웹 서비스인 경우)
        *   `HTTPS 트래픽 허용` 체크박스를 선택합니다. (애플리케이션이 HTTPS를 사용하는 경우)
        *   SSH 접속은 기본적으로 허용됩니다. 추가적인 포트가 필요하면 "네트워킹" > "방화벽 규칙"에서 설정할 수 있습니다.
6.  **만들기**: 구성 검토 후 "만들기" 버튼을 클릭하여 VM 생성을 시작합니다. 몇 분 정도 소요될 수 있습니다.

### gcloud CLI를 이용한 방법

로컬 터미널에서 다음 `gcloud` 명령어를 사용하여 VM을 생성할 수 있습니다.

```bash
# 변수 설정 (필요에 따라 수정)
export PROJECT_ID="YOUR_PROJECT_ID" # 실제 프로젝트 ID로 변경
export INSTANCE_NAME="my-app-vm"
export ZONE="us-central1-a" # 원하는 영역으로 변경
export MACHINE_TYPE="e2-medium"
export IMAGE_FAMILY="ubuntu-2004-lts"
export IMAGE_PROJECT="ubuntu-os-cloud"
export NETWORK_TAGS="http-server,https-server" # 방화벽 태그 (아래 방화벽 규칙 생성 시 사용)

# GCP 프로젝트 설정 (최초 실행 시 또는 프로젝트 변경 시)
gcloud config set project $PROJECT_ID

# VM 인스턴스 생성
gcloud compute instances create $INSTANCE_NAME \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --image-family=$IMAGE_FAMILY \
    --image-project=$IMAGE_PROJECT \
    --tags=$NETWORK_TAGS \
    --boot-disk-size=20GB # 필요에 따라 디스크 크기 조절

# 방화벽 규칙 생성 (이미 존재하거나 GCP Console에서 설정했다면 생략 가능)
# HTTP 허용
gcloud compute firewall-rules create "${INSTANCE_NAME}-allow-http" \
    --network=default \
    --allow tcp:80 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=http-server

# HTTPS 허용
gcloud compute firewall-rules create "${INSTANCE_NAME}-allow-https" \
    --network=default \
    --allow tcp:443 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=https-server

# SSH는 기본적으로 허용되지만, 특정 네트워크나 태그를 사용한다면 별도 규칙 필요
# gcloud compute firewall-rules create "${INSTANCE_NAME}-allow-ssh" \
#     --network=default \
#     --allow tcp:22 \
#     --source-ranges=0.0.0.0/0 # 보안을 위해 특정 IP로 제한 권장
```

VM이 생성되면 외부 IP 주소가 할당됩니다. GCP Console의 VM 인스턴스 목록 또는 `gcloud compute instances list` 명령어로 확인할 수 있습니다.

## VM에 SSH로 접속

### GCP Console 사용

1.  VM 인스턴스 목록에서 생성한 VM을 찾습니다.
2.  해당 VM 행의 "연결" 열 아래에 있는 "SSH" 버튼을 클릭합니다. 브라우저 창이나 별도의 터미널 창에서 SSH 세션이 열립니다.

### gcloud CLI 사용

로컬 터미널에서 다음 명령어를 실행합니다.

```bash
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE
```

## VM에 Docker 및 Docker Compose 설치

VM에 SSH로 접속한 후 다음 명령어를 실행하여 Docker와 Docker Compose를 설치합니다.

### Docker 설치

```bash
# 0. (선택 사항) 기존 Docker 관련 패키지 및 설정 정리 (새 VM이 아닐 경우)
# sudo apt-get remove docker docker-engine docker.io containerd runc docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
# sudo rm -rf /var/lib/docker
# sudo rm -rf /var/lib/containerd
# sudo rm -f /etc/apt/sources.list.d/docker.list
# sudo rm -f /etc/apt/keyrings/docker.asc

# 1. 패키지 목록 업데이트 및 필수 패키지 설치
sudo apt-get update
sudo apt-get install -y ca-certificates curl

# 2. Docker 공식 GPG 키 추가
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# 3. Docker APT 저장소 설정
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 4. 패키지 목록 다시 업데이트
sudo apt-get update
# 만약 "N: Some sources can be modernized. Run 'apt modernize-sources' to do so." 메시지가 나온다면,
# sudo apt modernize-sources
# 명령을 실행하고 다시 sudo apt-get update 를 시도해볼 수 있습니다.

# 5. Docker Engine, CLI, Containerd 및 Docker Compose 플러그인 설치
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 6. Docker 설치 확인 (테스트 실행)
sudo docker run hello-world

# 7. Docker 서비스 시작 및 부팅 시 자동 실행 설정
sudo systemctl start docker
sudo systemctl enable docker

# 8. (선택 사항) 현재 사용자를 docker 그룹에 추가하여 sudo 없이 docker 명령어 사용
# 변경 사항을 적용하려면 로그아웃 후 다시 로그인해야 합니다.
sudo usermod -aG docker ${USER}
# newgrp docker # 즉시 그룹 멤버십 적용 (또는 재로그인)
```
`sudo usermod -aG docker ${USER}` 실행 후, 터미널을 종료하고 다시 SSH 접속하거나 `newgrp docker` 명령을 실행해야 `sudo` 없이 `docker` 명령을 사용할 수 있습니다. 이후 명령어에서는 `sudo`를 붙여 안전하게 실행합니다.

### Docker Compose 설치

Docker Engine 설치 시 `docker-compose-plugin`이 함께 설치되었으므로 별도의 Docker Compose 설치 과정은 필요하지 않습니다. 다음 명령어로 설치를 확인할 수 있습니다.

```bash
# Docker Compose 플러그인 버전 확인 (하이픈이 아닌 공백 사용)
docker compose version
```
이전 `docker-compose` (하이픈 사용) 대신 `docker compose` (공백 사용) 명령을 사용해야 합니다.

## 애플리케이션 배포

### `docker-compose.yml` 파일 준비 및 VM에 복사/클론

배포할 애플리케이션의 `docker-compose.yml` 파일과 관련 소스 코드가 필요합니다. 로컬에서 VM으로 복사하거나, GitHub과 같은 버전 관리 시스템에서 직접 클론할 수 있습니다.

**방법 1: 로컬에서 `docker-compose.yml` 및 관련 파일 복사 (기존 방법)**

로컬 시스템에 준비된 `docker-compose.yml` 파일과 애플리케이션 빌드에 필요한 파일들(예: `Dockerfile`, 소스 코드 등)을 VM으로 복사합니다.

*   **`gcloud compute scp` 사용 (로컬 터미널에서 실행)**:
    단일 파일을 복사하는 경우:
    ```bash
    # 예: 현재 디렉토리의 docker-compose.yml 파일을 VM의 홈 디렉토리로 복사
    gcloud compute scp ./docker-compose.yml $INSTANCE_NAME:~ --zone=$ZONE
    ```
    디렉토리 전체를 복사하는 경우 (애플리케이션 소스 코드 포함 시):
    ```bash
    # 예: 로컬의 my-app 디렉토리를 VM의 홈 디렉토리 아래로 복사
    gcloud compute scp --recurse ./my-app $INSTANCE_NAME:~ --zone=$ZONE
    ```
    복사 후 VM에서 `cd ~/my-app` 등으로 해당 디렉토리로 이동합니다.

*   **SSH 접속 후 `nano` 또는 `vim`으로 직접 작성/붙여넣기 (VM 터미널에서 실행)**:
    `docker-compose.yml` 파일만 필요한 간단한 경우에 사용할 수 있습니다.
    ```bash
    # VM에 app 디렉토리 생성 (예시)
    mkdir ~/app
    cd ~/app
    # nano 편집기로 docker-compose.yml 파일 생성
    nano docker-compose.yml
    ```
    `nano` 편집기가 열리면 로컬의 `docker-compose.yml` 파일 내용을 복사하여 붙여넣고 저장합니다.

**방법 2: GitHub 저장소에서 소스 코드 및 `docker-compose.yml` 클론 (VM 터미널에서 실행)**

애플리케이션 소스 코드와 `docker-compose.yml` 파일이 GitHub 저장소에 있는 경우, VM에 직접 클론할 수 있습니다.

1.  **Git 설치 (VM에 설치되어 있지 않은 경우)**:
    ```bash
    sudo apt-get update
    sudo apt-get install -y git
    ```

2.  **GitHub 저장소 클론**:
    원하는 경로에 저장소를 클론합니다. 예를 들어, 홈 디렉토리 아래에 `app`이라는 이름으로 클론하려면:
    ```bash
    mkdir ~/app  # 이미 app 디렉토리가 있다면 생략하거나 다른 이름 사용
    cd ~
    git clone <YOUR_GITHUB_REPOSITORY_URL> app # 예: git clone https://github.com/username/my-repo.git app
    cd ~/app
    ```
    `<YOUR_GITHUB_REPOSITORY_URL>`을 실제 GitHub 저장소 URL로 변경하세요. 비공개 저장소의 경우 SSH 키 설정 또는 HTTPS 인증 정보가 필요할 수 있습니다.

3.  **(선택 사항) 특정 브랜치 또는 태그 체크아웃**:
    기본 브랜치(예: `main` 또는 `master`)가 아닌 다른 브랜치나 태그를 사용해야 한다면 클론 후 해당 브랜치로 이동합니다.
    ```bash
    # 예: develop 브랜치로 변경
    # git checkout develop
    # 예: v1.0 태그로 변경
    # git checkout v1.0
    ```

이제 `~/app` (또는 클론한 디렉토리) 내에 `docker-compose.yml` 파일과 애플리케이션 소스 코드가 준비됩니다.

**예시 `docker-compose.yml` (VM의 `~/app/docker-compose.yml` 경로에 위치)**:

```yaml
version: '3.8'
services:
  web:
    image: nginxdemos/hello:latest # 실제 애플리케이션 이미지로 변경
    ports:
      - "80:80" # VM의 80번 포트를 컨테이너의 80번 포트로 매핑
    # restart: always # 필요에 따라 재시작 정책 추가

  # 다른 서비스가 있다면 여기에 추가
  # 예를 들어, 데이터베이스 서비스:
  # db:
  #   image: postgres:13
  #   environment:
  #     POSTGRES_USER: example
  #     POSTGRES_PASSWORD: example
  #   volumes:
  #     - db_data:/var/lib/postgresql/data

# volumes:
#   db_data:
```

### Docker Compose 애플리케이션 실행

`docker-compose.yml` 파일이 있는 디렉토리로 이동하여 다음 명령어를 실행합니다. (VM 터미널에서)

```bash
# docker-compose.yml 파일이 있는 디렉토리로 이동 (예: ~/app)
cd ~/app

# Docker Compose 애플리케이션 백그라운드에서 실행 (docker compose 명령어 사용)
sudo docker compose up -d
```

실행 상태를 확인하려면 다음 명령어를 사용합니다:

```bash
# 실행 중인 컨테이너 확인
sudo docker compose ps

# 로그 확인 (예: web 서비스)
sudo docker compose logs web
# 모든 로그 확인
sudo docker compose logs
```

## 애플리케이션 확인

배포된 애플리케이션이 외부에서 공개적으로 접근 가능한지 확인합니다.

1.  **VM 외부 IP 주소 확인**:
    *   GCP Console의 "Compute Engine" > "VM 인스턴스" 페이지에서 생성한 VM 인스턴스를 찾아 "외부 IP" 열의 주소를 확인합니다.
    *   또는 `gcloud` CLI를 사용하여 확인합니다:
        ```bash
        gcloud compute instances list --filter="name=($INSTANCE_NAME)" --format="value(networkInterfaces[0].accessConfigs[0].natIP)"
        ```

2.  **웹 브라우저로 접속**:
    *   웹 브라우저를 열고 `http://<VM_외부_IP_주소>` 또는 `docker-compose.yml` 파일 내 `ports`에 설정한 외부 포트(예: `http://<VM_외부_IP_주소>:8080`)로 접속합니다.
    *   예를 들어, `docker-compose.yml`에 다음과 같이 포트가 매핑되어 있고 (`ports: - "80:8000"`), VM의 외부 IP가 `34.123.45.67`이라면, `http://34.123.45.67`로 접속합니다. 만약 `ports: - "8080:80"`으로 매핑했다면 `http://34.123.45.67:8080`으로 접속합니다.

3.  **방화벽 규칙 확인**:
    *   접속이 안 될 경우, GCP 방화벽 규칙이 올바르게 설정되어 해당 포트의 트래픽을 허용하는지 다시 한번 확인합니다. VM 생성 시 "HTTP 트래픽 허용" 또는 "HTTPS 트래픽 허용"을 선택했거나, `gcloud` 명령어로 해당 태그(`http-server`, `https-server`)에 대한 방화벽 규칙을 생성했다면 기본 포트(80, 443)는 열려 있습니다. `docker-compose.yml`에서 다른 외부 포트를 사용한다면 해당 포트에 대한 방화벽 규칙을 추가해야 합니다. (GCP Console > VPC 네트워크 > 방화벽)

성공적으로 접속되면 애플리케이션 화면이 나타납니다.

## 고정 IP 주소 할당 (선택 사항)

VM을 재시작하면 외부 IP 주소가 변경될 수 있습니다. 고정된 IP 주소를 사용하려면 GCP Console에서 "VPC 네트워크" > "외부 IP 주소"로 이동하여 임시 IP 주소를 고정 IP 주소로 승격할 수 있습니다.

`gcloud` CLI 사용:

```bash
# 기존 임시 IP 주소를 고정 IP로 승격
# 먼저 현재 VM의 외부 IP 주소와 리전을 확인해야 합니다.
export REGION=${ZONE%-*} # ZONE에서 리전 추출 (예: us-central1-a -> us-central1)
gcloud compute addresses create ${INSTANCE_NAME}-static-ip \
    --addresses $(gcloud compute instances describe ${INSTANCE_NAME} --zone=${ZONE} --format='get(networkInterfaces[0].accessConfigs[0].natIP)') \
    --region ${REGION}
```
고정 IP를 생성한 후에는 DNS 레코드를 설정하여 도메인 이름으로 접속할 수 있게 할 수 있습니다.

## 도메인 이름을 사용하여 공개적으로 액세스 (선택 사항)

외부 IP 주소는 기억하기 어렵고, VM이 재시작될 때 변경될 수 있는 임시 IP일 수 있습니다. 애플리케이션에 보다 안정적이고 사용자 친화적인 공개 액세스를 제공하려면 도메인 이름을 사용하는 것이 좋습니다.

1.  **고정 외부 IP 주소 확보**:
    *   위의 "고정 IP 주소 할당 (선택 사항)" 섹션을 참고하여 VM 인스턴스에 고정 외부 IP 주소를 할당합니다. 도메인 이름은 변경되지 않는 IP 주소를 가리켜야 합니다.

2.  **도메인 이름 등록**:
    *   Google Domains, GoDaddy, Namecheap 등과 같은 도메인 등록기관을 통해 원하는 도메인 이름(예: `myapp.example.com`)을 구매합니다. 이미 도메인을 소유하고 있다면 해당 도메인 또는 서브도메인을 사용할 수 있습니다.

3.  **DNS 레코드 설정**:
    *   도메인 등록기관 또는 사용 중인 DNS 호스팅 서비스의 관리 콘솔에 접속합니다.
    *   새로운 DNS 레코드를 추가합니다. 일반적으로 `A` 레코드를 사용합니다.
        *   **레코드 유형**: `A`
        *   **호스트 이름 (또는 이름)**: 사용할 도메인 또는 서브도메인 (예: `www` 또는 `app` 또는 `@`는 루트 도메인을 의미). `app.example.com`을 원한다면 `app`을 입력합니다.
        *   **값 (또는 IP 주소)**: 1단계에서 할당받은 VM의 고정 외부 IP 주소를 입력합니다.
        *   **TTL (Time To Live)**: 기본값을 사용하거나 필요에 따라 조정합니다. (예: 3600초 = 1시간)
    *   DNS 변경 사항이 전파되는 데는 몇 분에서 최대 48시간까지 소요될 수 있습니다.

4.  **애플리케이션 접속 확인**:
    *   DNS 전파가 완료된 후, 웹 브라우저에서 설정한 도메인 이름(예: `http://app.example.com` 또는 `docker-compose.yml`에 설정한 포트에 따라 `http://app.example.com:<포트번호>`)으로 접속하여 애플리케이션이 올바르게 표시되는지 확인합니다.

5.  **(권장) HTTPS 설정 (SSL/TLS 인증서)**:
    *   공개적으로 서비스를 제공한다면, 보안을 위해 HTTPS를 설정하는 것이 매우 중요합니다.
    *   Let's Encrypt와 같은 무료 인증 기관을 사용하여 SSL/TLS 인증서를 발급받고 웹 서버(예: Nginx, Apache 또는 Docker 컨테이너 내의 웹 서버)에 설정할 수 있습니다.
    *   일부 Docker 이미지는 Let's Encrypt를 자동으로 통합하는 기능을 제공하기도 합니다 (예: `nginx-proxy`와 `acme-companion` 컨테이너 조합).
    *   HTTPS를 설정하면 `https://app.example.com`과 같이 안전하게 접속할 수 있습니다.

## 리소스 정리

더 이상 VM이 필요하지 않으면 삭제하여 불필요한 비용 발생을 방지합니다.

**GCP Console 사용**:

1.  Compute Engine > VM 인스턴스 목록으로 이동합니다.
2.  삭제할 VM 인스턴스를 선택하고 상단의 "삭제" 버튼을 클릭합니다.

**gcloud CLI 사용**:

```bash
gcloud compute instances delete $INSTANCE_NAME --zone=$ZONE
```
생성한 방화벽 규칙이나 고정 IP 주소도 필요 없다면 함께 삭제합니다.

```bash
# 방화벽 규칙 삭제
gcloud compute firewall-rules delete "${INSTANCE_NAME}-allow-http" --quiet
gcloud compute firewall-rules delete "${INSTANCE_NAME}-allow-https" --quiet

# 고정 IP 주소 삭제 (생성했을 경우)
gcloud compute addresses delete ${INSTANCE_NAME}-static-ip --region=${REGION} --quiet
```

이 가이드를 통해 GCP VM에 수동으로 Docker Compose 환경을 성공적으로 구축할 수 있기를 바랍니다.
