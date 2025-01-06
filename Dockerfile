FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    git \
    ghostscript \
    ocrmypdf \
    tesseract-ocr-spa \
    libreoffice \
    imagemagick \
    && pip install --upgrade pip

COPY magick_policy.xml /etc/ImageMagick-6/policy.xml
WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5002

CMD ["python", "app.py"]