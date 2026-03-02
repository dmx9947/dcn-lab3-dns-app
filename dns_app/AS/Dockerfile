FROM python:3.12-slim
WORKDIR /app
COPY as_server.py /app/as_server.py
EXPOSE 53533/udp
CMD ["python", "as_server.py"]