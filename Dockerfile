FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DOWNLOAD_DIR=/downloads

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY immich_print_picker.py .

RUN mkdir -p /downloads

VOLUME ["/downloads"]

ENTRYPOINT ["python", "/app/immich_print_picker.py"]
