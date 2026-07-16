FROM python:3.12-slim

WORKDIR /app

# Create non-root user to own /app
RUN useradd --create-home appuser && chown appuser:appuser /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY --chown=appuser:appuser pyproject.toml .
COPY --chown=appuser:appuser uv.lock* .

# Switch to non-root before installing dependencies
USER appuser

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy code files
COPY --chown=appuser:appuser app/ app/

# Expose port
EXPOSE 8000

# Health Check
HEALTHCHECK --interval=30s --timeout=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with uvicorn
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

