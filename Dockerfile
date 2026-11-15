FROM python:3.12-slim
WORKDIR /app
COPY . .
# server binds loopback by default; container use overrides it explicitly below.
EXPOSE 8501
CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8501"]
