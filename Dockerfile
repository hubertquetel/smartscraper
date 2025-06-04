FROM python:3.11-slim

WORKDIR /app

# Install dependencies for Playwright and Python packages
RUN apt-get update && \
    apt-get install -y curl gnupg libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libxcomposite1 libxrandr2 libxdamage1 libxkbcommon0 libx11-xcb1 \
    libgbm1 libxss1 libasound2 wget unzip && \
    pip install --no-cache-dir flask playwright readability-lxml markdownify && \
    playwright install

COPY app.py .

CMD ["python", "app.py"]
