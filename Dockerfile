FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Istanbul

EXPOSE 80

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy the application into the container.
COPY /app /app/app
COPY /pyproject.toml /app
COPY /uv.lock /app

WORKDIR /app
# install the non-dev dependencies and remove the uv binary
RUN uv sync --frozen --no-cache --no-dev && rm /bin/uv

ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint
ENTRYPOINT []

CMD ["fastapi", "run", "app/main.py", "--port", "80"]
