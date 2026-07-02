FROM python:3.11-slim

# Install system dependencies needed to build and run the MariaDB connector
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    libmariadb-dev \
    libmariadb-dev-compat \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install python packages
COPY backend/requirements.txt ./backend/requirements.txt
ENV CFLAGS="-Wno-error=incompatible-pointer-types"
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy source code
COPY backend/ ./backend/

# Expose port and run uvicorn
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
