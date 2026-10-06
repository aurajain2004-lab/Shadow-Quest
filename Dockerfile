FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY README.md .

RUN python -m py_compile main.py

CMD ["python", "-m", "py_compile", "main.py"]