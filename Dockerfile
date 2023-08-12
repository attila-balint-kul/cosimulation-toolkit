FROM python:3.10-slim-bullseye

RUN apt-get update && apt-get install -y gcc wget

RUN python -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip setuptools

ARG PYPI_VERSION=0.1.2
RUN pip install --no-cache-dir cosimtlk==${PYPI_VERSION}

RUN useradd --create-home cosimtlk
USER cosimtlk

RUN cp -r /opt/venv/lib/python3.10/site-packages/cosimtlk/app /home/cosimtlk/app
WORKDIR /home/cosimtlk

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]