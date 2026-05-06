# ZeroClaw Dockerfile
FROM rust:1.75-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Clone and build ZeroClaw
RUN git clone https://github.com/zeroclaw-labs/zeroclaw.git .
RUN cargo build --release

# Runtime image
FROM debian:bookworm-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Copy ZeroClaw binary
COPY --from=builder /app/target/release/zeroclaw /usr/local/bin/zeroclaw

# Create config directory
RUN mkdir -p /root/.zeroclaw

# Copy default config
COPY config.toml /root/.zeroclaw/config.toml

# Expose ZeroClaw ports (if needed for channels)
EXPOSE 8080

# Run ZeroClaw
CMD ["zeroclaw", "agent"]
