# FairMind sandbox runner. Build from the repository root so the engine code comes from the backend:
#   docker build --build-context engines=apps/backend/src/application/services/eval_engines \
#     -t fairmind-eval-runner apps/eval-runner
# Only the two engine modules EV-TST-01 needs are copied; the backend app, its settings and its
# dependencies never enter the image.

# Build stage: python 3.11 (the runtime's version) to install the hash-locked wheels.
FROM python:3.11-slim-bookworm@sha256:a83ba18aef0f865b1a4a611c2cf460fe446f2795673bbb9fe43be570439e3b39 AS build
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --disable-pip-version-check --require-hashes --no-deps --only-binary=:all: \
      --target /opt/site -r /tmp/requirements.txt \
 && find /opt/site -name '__pycache__' -prune -exec rm -rf {} + \
 && rm -rf /opt/site/bin
COPY --from=engines common.py model.py /opt/runner/fairmind_engines/
COPY runner.py /opt/runner/runner.py
RUN touch /opt/runner/fairmind_engines/__init__.py

# Runtime: distroless python (Debian 12, python 3.11): no shell, no package manager, no pip,
# no network tools. Its nonroot user is UID/GID 65532, the UID the launcher enforces.
FROM gcr.io/distroless/python3-debian12:nonroot@sha256:7d1042ce588ab97019fe95c24ffca7bc5a82ccdac572511d5e09bda4435c89c5
COPY --from=build /opt/site /opt/site
COPY --from=build /opt/runner /opt/runner
ENV PYTHONPATH=/opt/site \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/tmp \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1
USER 65532:65532
ENTRYPOINT ["/usr/bin/python3.11", "-B", "/opt/runner/runner.py"]
