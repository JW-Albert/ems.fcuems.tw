#!/bin/bash

echo "Installing dependencies set -e..."
set -e

echo "Booting server..."
./boot.sh

cd /var/www/ems/web/server

echo "Copying ems-flask.service..."
cp ems-flask.service /etc/systemd/system/

echo "Reloading systemctl..."
systemctl daemon-reload
systemctl enable ems-flask
systemctl start ems-flask