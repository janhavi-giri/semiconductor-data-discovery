FROM python:3.12-slim
WORKDIR /app
COPY . .
# compose runs the container read-only, so unpack data/ at build time.
RUN python bootstrap.py
# server binds loopback by default; container use overrides it explicitly below.
EXPOSE 8501
CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8501"]
