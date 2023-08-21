FROM python:3.11

# Select working directory
WORKDIR /app

# Copy requirements.txt to working directory
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy required files to working directory
COPY bot.py .
COPY config.py .
COPY __main__.py .
COPY modules/ ./modules/

# Compile Python 3 source code into bytecode
RUN python3 -m compileall .

# Create data directory
RUN mkdir -p /data/logs

# Run the bot
CMD ["python3", "__main__.py"]
