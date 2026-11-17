FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
RUN useradd --create-home --uid 10001 appuser
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY requirements.txt pyproject.toml README.md ./
COPY src ./src
COPY static ./static
USER appuser
EXPOSE 8765
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8765"]