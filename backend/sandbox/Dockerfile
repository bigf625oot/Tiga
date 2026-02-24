# Use E2B's recommended base image or standard Ubuntu
FROM ubuntu:22.04

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Copy install scripts
COPY scripts/install_toolchain.sh /tmp/install_toolchain.sh
COPY scripts/healthcheck.py /usr/local/bin/healthcheck.py

# Run installation
RUN chmod +x /tmp/install_toolchain.sh && \
    /tmp/install_toolchain.sh && \
    rm /tmp/install_toolchain.sh && \
    chmod +x /usr/local/bin/healthcheck.py

# Setup user 'user' (standard for E2B)
RUN useradd -m -s /bin/bash user && \
    echo "user ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set working directory
WORKDIR /home/user

# Setup PATH for Go
ENV PATH=$PATH:/usr/local/go/bin

# Copy and setup entrypoint
COPY scripts/start_daemon.sh /usr/local/bin/start_daemon.sh
RUN chmod +x /usr/local/bin/start_daemon.sh

# Switch to user
USER user

# Entrypoint script to start background services
ENTRYPOINT ["/usr/local/bin/start_daemon.sh"]

# Default command (can be overridden by E2B)
CMD ["/bin/bash"]
