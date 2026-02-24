#!/bin/bash

echo "Verifying Toolchain Installation..."

# Check GCC
gcc --version && echo "GCC OK" || echo "GCC FAILED"

# Check Clang
clang --version && echo "Clang OK" || echo "Clang FAILED"

# Check Java
java -version && echo "Java OK" || echo "Java FAILED"

# Check Node
node -v && echo "Node OK" || echo "Node FAILED"
npm -v && echo "NPM OK" || echo "NPM FAILED"

# Check Python
python3 --version && echo "Python OK" || echo "Python FAILED"

# Check Go
go version && echo "Go OK" || echo "Go FAILED"

# Check Docker
docker --version && echo "Docker OK" || echo "Docker FAILED"

echo "Verification Complete."
