# 1) 베이스 이미지
FROM python:3.10-slim

# 2) 환경 변수
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3) 시스템 패키지 설치 (SSL/FFI 헤더 등)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    gcc libssl-dev libffi-dev build-essential \
 && rm -rf /var/lib/apt/lists/*

# 4) 작업 디렉터리
WORKDIR /app

# 5) requirements 복사 & 설치
COPY requirements.txt ./
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# 6) 소스 전체 복사
COPY . ./

# 7) API 포트
EXPOSE 5050

# 8) Gunicorn 으로 실행 (factory 패턴)
CMD ["gunicorn", "--bind", "0.0.0.0:5050", "--factory", "app:create_app"]