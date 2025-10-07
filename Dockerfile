FROM python:3.14-slim AS python-base
WORKDIR /app
COPY ./requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py /app

EXPOSE 12345
ENV PYTHONUNBUFFERED=1
ENV CALENDAR_URL="https://example.com"
ENTRYPOINT ["python3", "/app/main.py"]
