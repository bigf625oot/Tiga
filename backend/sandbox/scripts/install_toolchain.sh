#!/bin/bash
set -e

# Update and upgrade
apt-get update && apt-get upgrade -y

# Basic Utils
apt-get install -y \
    curl \
    wget \
    git \
    vim \
    nano \
    sudo \
    unzip \
    zip \
    software-properties-common \
    build-essential \
    pkg-config \
    libssl-dev \
    jq \
    htop \
    net-tools \
    iputils-ping \
    dnsutils

# C/C++ (GCC & Clang)
apt-get install -y gcc g++ clang cmake make

# Java (OpenJDK 17)
apt-get install -y openjdk-17-jdk

# Python
apt-get install -y python3 python3-pip python3-venv

# Node.js (Latest LTS)
curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
apt-get install -y nodejs
npm install -g yarn pnpm typescript ts-node

# Go (Latest stable)
GO_VERSION=$(curl -s https://go.dev/dl/?mode=json | jq -r '.[0].version')
wget https://go.dev/dl/${GO_VERSION}.linux-amd64.tar.gz
tar -C /usr/local -xzf ${GO_VERSION}.linux-amd64.tar.gz
rm ${GO_VERSION}.linux-amd64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> /etc/profile.d/go.sh

# Docker (Client only, daemon usually provided by host or dind service if enabled)
apt-get install -y docker.io

# Clean up
apt-get clean
rm -rf /var/lib/apt/lists/*
