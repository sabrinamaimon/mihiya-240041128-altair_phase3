#!/usr/bin/env bash
set -e

echo "=========================================================="
echo " Starting Project Altair ROS 2 Desktop (Ubuntu 22.04)   "
echo "=========================================================="

cd "$(dirname "$0")"

# Start container via docker compose
docker compose up -d

echo ""
echo "=========================================================="
echo " ROS 2 Desktop is running!"
echo " Open your browser (Chrome or Safari) and go to:"
echo "   http://localhost:6080"
echo "=========================================================="
