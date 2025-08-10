# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install essential system dependencies
# git & ssh for repository access, ffmpeg for video processing (for yt-dlp)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ssh \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
COPY . .

# Expose the port the app runs on (as seen in the original run Dockerfile)
EXPOSE 80

# Define the command to run the web UI
CMD ["python", "run_ui.py"]
