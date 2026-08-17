# Use the official Nginx unprivileged image, not latest
FROM nginxinc/nginx-unprivileged:1.25-alpine

# Copy the updated Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the static HTML file
# Assuming your index.html is in the same directory as this Dockerfile
COPY index.html /usr/share/nginx/html/

# Expose port 8080 (unprivileged port)
EXPOSE 8080

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
