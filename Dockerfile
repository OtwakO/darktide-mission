# Set the base image using Python 3.12 and Debian Bookworm
FROM python:3.12-alpine
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory to /app
WORKDIR /app

# Copy only the necessary files to the working directory
COPY . /app

# Install the requirements
# RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 80

# Run the app with the Litestar CLI
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "80", "--loop", "uvloop"]