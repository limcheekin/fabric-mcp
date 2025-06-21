# Dockerfile (Security-Hardened & Production-Ready)

# Use an ARG to define the Python version for easy updates.
ARG PYTHON_VERSION=3.12

# --- Base Stage ---
# Minimal base image with only necessary tools for building.
FROM python:${PYTHON_VERSION}-slim-bookworm AS base

# Add metadata labels for better image management
LABEL org.opencontainers.image.source="https://github.com/ksylvan/fabric-mcp" \
      org.opencontainers.image.description="Fabric MCP Server" \
      org.opencontainers.image.licenses="MIT"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install uv in a separate layer for better caching
RUN pip install uv


# --- Builder Stage ---
# This stage builds the virtual environment with all dependencies.
FROM base AS builder

WORKDIR /app

# Create a non-root user that will own the files
RUN useradd --system --uid 1001 appuser

# Create the virtual environment
RUN uv venv /opt/venv

# Copy dependency definition files first to leverage Docker layer caching
COPY pyproject.toml uv.lock* ./

# Copy the application source code *before* installation.
# This allows the build backend (hatch) to access files it needs, like __about__.py,
# to determine the package version.
COPY src/ ./src/
COPY README.md README.md

# Install dependencies into the venv.
# --no-cache is used to keep layers small.
RUN . /opt/venv/bin/activate && uv pip install --no-cache .

# Set ownership of the installed packages
RUN chown -R appuser:appuser /opt/venv


# --- Final Stage ---
# This is the final, ultra-slim, and secure production image.
# It uses a distroless base image which contains only the app and its runtime dependencies.
# This minimizes the attack surface by removing shells, package managers, etc.
FROM gcr.io/distroless/python3-debian12 AS final

WORKDIR /app

# Copy the non-root user from the builder stage
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /etc/group /etc/group

# Copy the virtual environment with installed dependencies
COPY --chown=1001:1001 --from=builder /opt/venv /opt/venv

# Copy the application source code
COPY --chown=1001:1001 src/ ./src/

# Switch to the non-root user
USER appuser

# Set the PATH to include the venv
ENV PATH="/opt/venv/bin:$PATH"

# Expose the server port
EXPOSE 8000

# Healthcheck without needing curl/bash. It uses Python's built-in http.client.
# This is compatible with the distroless image.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import http.client; conn = http.client.HTTPConnection('localhost', 8000); conn.request('GET', '/'); exit(0 if conn.getresponse().status < 500 else 1)"]

# Set the default command to run the server
CMD ["fabric-mcp", "--http-streamable", "--host", "0.0.0.0", "--port", "8000"]


# --- Security Scanning Stage (Optional but Recommended) ---
# This stage uses Trivy to scan the final image for vulnerabilities.
# It doesn't affect the final image but can be used in CI/CD to gate deployments.
FROM aquasec/trivy:latest AS scan
ARG TRIVY_SEVERITY="HIGH,CRITICAL"
COPY --from=final / /rootfs/
# The --exit-code 1 will fail the build if vulnerabilities of the specified severity are found.
# Use --exit-code 0 to just see the report without failing the build.
RUN trivy rootfs /rootfs --severity=${TRIVY_SEVERITY} --exit-code 0
