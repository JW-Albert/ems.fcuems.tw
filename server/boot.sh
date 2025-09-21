#!/bin/bash
sudo apt update -y && sudo apt upgrade -y

sudo apt install -y python3-pip python3-venv python3-dev

mkdir -p /var/www/ems

cd /var/www/ems
python3 -m venv venv

source venv/bin/activate

cd web
pip3 install -r requirements.txt