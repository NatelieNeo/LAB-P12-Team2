FROM python:3.12-slim

WORKDIR /app

# Install the dependencies, including pytest.
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy the program modules and automated tests.
COPY *.py ./

# Start the program by default.
CMD ["python", "main.py"]