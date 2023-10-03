FROM python:3-slim as python
ENV PYTHONUNBUFFERED=true
WORKDIR /app
COPY . ./
RUN apt-get update && apt-get install -y gcc && pip install -r requirements.txt
EXPOSE 8000
CMD python jarvis.py