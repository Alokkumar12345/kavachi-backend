#!/bin/bash
echo 'Installing Node Dependencies...'
npm install

echo 'Setting up Python Virtual Environment...'
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo 'Build Successful!'
