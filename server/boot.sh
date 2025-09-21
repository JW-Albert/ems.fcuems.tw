#!/bin/bash

echo "Installing dependencies set -e..."
set -e

echo "Updating system sudo apt update -y && sudo apt upgrade -y..."
sudo apt update -y && sudo apt upgrade -y

echo "Installing dependencies python3 python3-pip python3-venv python3-dev..."
sudo apt install -y python3 python3-pip python3-venv python3-dev

echo "Changing directory..."
cd /var/www/ems

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip setuptools wheel..."
pip3 install --upgrade pip setuptools wheel

echo "Installing dependencies..."
cd web

pip3 install -r requirements.txt