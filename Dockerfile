FROM python:3.12
WORKDIR /app

# Upgrade build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install dependencies - copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for prompt templates
RUN mkdir -p /app/bot_logic

# Note: Command is now specified in docker-compose.yml to avoid duplicate execution
# CMD ["python", "bot_logic/main.py"]