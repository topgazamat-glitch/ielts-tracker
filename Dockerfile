# Plain Python, no dependencies to install - the image is tiny and builds fast.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY . .
ENV DATA_DIR=/data
ENV PORT=8080
EXPOSE 8080
CMD ["python", "app.py"]
