# Build stage
FROM python:3.10.10-slim AS builder

WORKDIR /usr/src/app

# Install build dependencies including GCC
RUN apt-get update && apt-get install -y gcc

COPY requirements.txt ./
RUN pip3 install --no-cache-dir --user -r requirements.txt

COPY . .

# Install any additional build dependencies and build your application
RUN python setup.py install --user

# Production stage
FROM python:3.10.10-slim AS production

WORKDIR /usr/src/app

# Copy only the necessary artifacts from the builder stage
COPY --from=builder /root/.local /root/.local
COPY --from=builder /usr/src/app/*.py .

# Add the user local bin directory to PATH
ENV PATH=/root/.local/bin:$PATH

# Set the user home directory
ENV HOME=/root

CMD [ "python", "./main.py" ]
