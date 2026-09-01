# Pinned so a rebuild produces the same interpreter.
# To keep in sync with python-version in .github/workflows/tests.yml.
FROM python:3.14.7

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

CMD [ "python", "./run_api.py" ]
