# Minimal Dockerfile for Cloud Run
FROM python:3.9-slim

WORKDIR /app

# Install streamlit only
RUN pip install --no-cache-dir streamlit

# Copy application
COPY . .

# Expose port
EXPOSE 8080

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true"]
