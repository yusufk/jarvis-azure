FROM python:3-slim as python
ENV PYTHONUNBUFFERED=true
WORKDIR /app
COPY . ./
COPY --from=poetry /app /app
RUN pip install -r requirements.txt
EXPOSE 8000
CMD python jarvis.py