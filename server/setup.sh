#!/bin/bash

cp server ../

cd ..
./server/boot.sh

cp ems.service /etc/systemd/system/

systemctl daemon-reload
systemctl enable ems
systemctl start ems

rm -rf server