FROM python:3.10-slim-bookworm

RUN apt-get update && apt-get install -y gcc wget libc6

RUN python -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip setuptools

ARG PYPI_VERSION=0.4.0
RUN pip install --no-cache-dir cosimtlk["server"]==${PYPI_VERSION}

RUN useradd --create-home cosimtlk
USER cosimtlk
WORKDIR /home/cosimtlk

EXPOSE 8000
CMD ["cosimtlk", "server", "--host", "0.0.0.0", "--port", "8000"]
