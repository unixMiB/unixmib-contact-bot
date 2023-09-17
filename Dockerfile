FROM python:3.11-alpine3.18
WORKDIR /app
RUN pip install --no-cache-dir --upgrade pip telethon sqlalchemy
COPY src .
CMD ["python", "-m", "unixmib_contact_bot"]