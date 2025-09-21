#!/bin/bash

echo "Installing dependencies set -e..."
set -e

echo "Copying server..."
cp server ../

echo "Changing directory..."
cd ..

echo "Booting server..."
./server/boot.sh

echo "Copying ems.service..."
cp ems.service /etc/systemd/system/

echo "Reloading systemctl..."
systemctl daemon-reload
systemctl enable ems
systemctl start ems

rm -rf server