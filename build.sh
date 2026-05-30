#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

cd theme/static_src
npm install
npm run build
cd ../..

python manage.py collectstatic --no-input

python manage.py migrate