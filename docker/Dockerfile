FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy API and prototype library
COPY api/main.py /app/api/main.py
COPY prototype/ire_lib.py /app/prototype/ire_lib.py
COPY prototype/golden_records.csv /app/prototype/golden_records.csv
COPY prototype/incoming_records.csv /app/prototype/incoming_records.csv

# Point the API at the bundled sample CSV
ENV GOLDEN_CSV=/app/prototype/golden_records.csv

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
