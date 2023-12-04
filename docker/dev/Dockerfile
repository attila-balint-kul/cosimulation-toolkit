FROM python:3.10-slim-bookworm

RUN apt-get update && apt-get install -y gcc wget libc6

RUN python -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip setuptools

COPY pyproject.toml /tmp/cosimulation-toolkit/pyproject.toml
COPY README.md /tmp/cosimulation-toolkit/README.md
COPY src/ /tmp/cosimulation-toolkit/src/
RUN cd /tmp/cosimulation-toolkit && pip install --no-cache-dir -e ".[server]"

RUN useradd --create-home cosimtlk
WORKDIR /home/cosimtlk
USER cosimtlk

EXPOSE 8000
CMD ["cosimtlk", "server", "--host", "0.0.0.0", "--port", "8000"]