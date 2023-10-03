FROM python:3-slim as python
ENV PYTHONUNBUFFERED=true
WORKDIR /app
RUN pip install poetry==1.4.2



FROM python as poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache
COPY . ./
RUN poetry install --no-interaction --no-ansi -vvv || poetry install --no-interaction --no-ansi -vvv || poetry install --no-interaction --no-ansi -vvv



FROM python as runtime
ENV PATH="/app/.venv/bin:$PATH"
COPY --from=poetry /app /app
EXPOSE 8000
CMD python jarvis.py