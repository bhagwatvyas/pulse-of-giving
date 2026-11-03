FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

COPY fixtures ./fixtures
ENTRYPOINT ["pulse-compile"]
CMD ["--snapshot", "fixtures/illustrative-pnw.json"]
