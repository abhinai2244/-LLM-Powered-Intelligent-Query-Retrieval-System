#!/bin/bash
apt-get update
apt-get install -y tesseract-ocr poppler-utils
pip install -r requirements.txt
