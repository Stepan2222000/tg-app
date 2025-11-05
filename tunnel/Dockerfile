# Cloudflare Tunnel Dockerfile
# Named tunnel configuration for permanent domain
FROM cloudflare/cloudflared:latest

# Copy tunnel configuration files
COPY config.yml /etc/cloudflared/config.yml
COPY credentials.json /etc/cloudflared/credentials.json

# Run named tunnel with config file
CMD ["tunnel", "--config", "/etc/cloudflared/config.yml", "run"]
