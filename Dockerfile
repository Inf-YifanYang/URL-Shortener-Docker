# Set base image (host OS)
FROM python:3.12

# By default, listen on port 5000
EXPOSE 8080/tcp

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any dependencies
RUN pip install -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY app ./app
COPY server_setup.sh .

# Specify the command to run on container start
CMD [ "uvicorn", "app.main:app", "--reload",  "--port", "8080", "--host", "0.0.0.0"]