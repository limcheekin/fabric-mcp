# Dockerfile (Security-Hardened & Production-Ready using pip install)

# Use an ARG to define the Python version for easy updates.
ARG PYTHON_VERSION=3.11

# --- Builder Stage ---
# This stage fetches the package and its dependencies from PyPI.
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

# Set essential environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Create a non-root user that will be copied to the final stage
RUN useradd --system --uid 1001 appuser

# Create a directory to install the packages into
WORKDIR /install

# Install the package and its dependencies into the current directory (/install).
# Using --target ensures all files are in one place for easy copying to the next stage.
# This assumes 'fabric-mcp' is available on a package index like PyPI.
RUN pip install --target=. fabric-mcp


# --- Final Stage ---
# This is the final, ultra-slim, and secure production image.
FROM gcr.io/distroless/python3-debian12 AS final

WORKDIR /app

# Copy the non-root user from the builder stage
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /etc/group /etc/group

# Copy the installed packages from the builder stage into a clean location
COPY --chown=1001:1001 --from=builder /install /opt/packages

# Set the PYTHONPATH so the Python interpreter can find the installed modules.
ENV PYTHONPATH="/opt/packages"

# Switch to the non-root user for added security
USER appuser

# Expose the server port
EXPOSE 8000

# Healthcheck to ensure the server is running correctly
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import http.client; conn = http.client.HTTPConnection('localhost', 8000); conn.request('GET', '/message'); exit(0 if conn.getresponse().status < 500 else 1)"]

# Use the default distroless entrypoint ("python3") and run the app as a module.
# This remains the most reliable method as it avoids all shebang/PATH issues.
CMD ["-m", "fabric_mcp.cli", "--transport", "http", "--host", "0.0.0.0", "--port", "8000"]