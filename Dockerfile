# 1) 베이스 이미지
FROM python:3.10-slim

# 2) 환경 변수
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3) 시스템 패키지 설치: 빌드 툴 + SSL/FFI 헤더
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    gcc \
 && rm -rf /var/lib/apt/lists/*

# 4) 작업 디렉터리
WORKDIR /app

# 5) requirements 파일 복사
COPY requirements.txt .

# 6) 파이썬 의존성 설치
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# 7) 앱 소스 복사
COPY . .

# 8) 컨테이너 포트 노출
EXPOSE 5050

# 9) 실행 명령
CMD ["gunicorn", "--bind", "0.0.0.0:5050", "app:app"]
