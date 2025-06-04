FROM python:3.11-slim

WORKDIR /app

# Préparation système + dépendances Playwright
RUN apt-get update && \
    apt-get install -y wget unzip gnupg curl && \
    apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libxcomposite1 \
    libxrandr2 libxdamage1 libxkbcommon0 libx11-xcb1 libgbm1 libxss1 libasound2 \
    libxfixes3 libglib2.0-0 libdrm2 libpango-1.0-0 libcairo2 fonts-liberation \
    libappindicator3-1 libu2f-udev libvulkan1 libxshmfence1 --no-install-recommends && \
    pip install --no-cache-dir flask playwright readability-lxml markdownify && \
    playwright install --with-deps

COPY app.py .

CMD ["python", "app.py"]
