Elibrary Server Requirements

Minimum recommended specs:
- CPU: 4 vCPU
- RAM: 8 GB
- Disk: 100 GB SSD
- Network: Public IP, TLS certificate (Let's Encrypt)

Optional for media-heavy workloads:
- CPU: 8+ vCPU
- RAM: 16+ GB
- Storage: 500 GB+ with backup
- Transcoding: GPU (NVIDIA) for high-performance video processing

Software:
- OS: Ubuntu 22.04 LTS or equivalent
- Python 3.10+
- PostgreSQL 13+
- Redis for Celery
- Gunicorn + Nginx

Scaling:
- Use separate workers for Celery
- Use object storage (S3) for media in production

Note: Adjust specs based on concurrency and media size expectations.