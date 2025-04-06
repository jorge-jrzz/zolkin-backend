FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ghostscript \
    libreoffice \
    imagemagick \
    tesseract-ocr-spa \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --no-group calendar-toolkit

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-group calendar-toolkit

# Create directories and set permissions
RUN mkdir -p /app/uploads/originals /app/uploads/pdfs /app/tokens
COPY magick_policy.xml /etc/ImageMagick-6/policy.xml

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app

EXPOSE 5002

ENTRYPOINT []

CMD ["python", "main.py"]