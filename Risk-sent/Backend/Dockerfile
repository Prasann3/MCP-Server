# Use Ubuntu 22.04 as the stable base
FROM ubuntu:22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# 1. Install system dependencies & Python 3.12
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    curl \
    redis-server \
    g++ \
    make \
    cmake \
    libpoppler-cpp-dev \
    libspdlog-dev \
    libfmt-dev \
    nlohmann-json3-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Set Python 3.12 as default and create 'python' alias
# This fixes the "FileNotFoundError: [Errno 2] No such file or directory: 'python'"
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 \
    && update-alternatives --set python3 /usr/bin/python3.12 \
    && ln -s /usr/bin/python3 /usr/bin/python

# 3. Install pip for Python 3.12
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3

WORKDIR /app

# 4. Handle Python dependencies
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# 5. Copy your project files
COPY . .

# 6. Compile the C++ worker
RUN g++ -O3 -o app/workers/worker app/workers/worker.cpp \
    -DSPDLOG_FMT_EXTERNAL \
    -lpoppler-cpp -lspdlog -lfmt -lpthread \
    -Wl,-rpath,/usr/local/lib:/usr/lib

# 7. Expose ports
EXPOSE 8000
EXPOSE 6379

# 8. Final Launch Command
CMD ["sh", "-c", "redis-server --daemonize yes && python3 -m app.workers.parsing_worker & python3 -m app.workers.upload_worker & python3 -m app.main"]