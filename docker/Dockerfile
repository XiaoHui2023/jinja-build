FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV TEMPLATE_DIR=/data/template
ENV DOC_DIR=/data/doc
ENV LOG_DIR=/data/log
ENV MODELS_FILENAME=models.py
ENV DOC_INTERVAL=1.0

WORKDIR /app

COPY pyproject.toml /app/

RUN python -c "import tomllib; from pathlib import Path; project = tomllib.loads(Path('pyproject.toml').read_text(encoding='utf-8')); dependencies = project['project'].get('dependencies', []); Path('/tmp/requirements.txt').write_text('\n'.join(dependencies) + '\n', encoding='utf-8')" \
    && pip install --no-cache-dir -r /tmp/requirements.txt

COPY cli /app/cli
COPY server /app/server
COPY doc /app/doc
COPY docker/run_all.py /app/docker/run_all.py

EXPOSE 8000

CMD ["python", "docker/run_all.py"]
