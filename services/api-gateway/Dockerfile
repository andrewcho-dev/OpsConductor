FROM nginx:alpine

# Copy custom nginx configuration  
COPY nginx-microservices.conf /etc/nginx/nginx.conf

# Create log directory and install curl
RUN mkdir -p /var/log/nginx && apk add --no-cache curl

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]