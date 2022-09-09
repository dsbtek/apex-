#!/bin/sh

rsync -vzrhe "ssh -o StrictHostKeyChecking=no" --exclude-from="exclude.txt" . ubuntu@63.32.36.18:/var/www/PYTHON/smarteye_api/temp
rsync -vzrhe "ssh -o StrictHostKeyChecking=no" ./.env.production ubuntu@63.32.36.18:/var/www/PYTHON/smarteye_api/temp

ssh -o StrictHostKeyChecking=no ubuntu@63.32.36.18 <<-EOF
    cd /var/www/PYTHON/smarteye_api
    sudo rm -rf ./backup # Delete previous backup
    sudo mv ./live ./backup # Create new backup
    sudo mv ./temp ./live
    sudo mkdir ./temp # create new temp directory for next deployment
    sudo chown -R ubuntu:ubuntu ./temp
    cd ./live
    sudo mv .env.production .env
    sudo cp -r ../backup/media . #copy uploaded media files to new deploy 


    # Install virtual env
    sudo python3 -m venv .virtualenv

    sudo chown -R ubuntu:ubuntu .virtualenv

    # Activate virtual environment
    source .virtualenv/bin/activate

    # upgrade pip
    pip install --upgrade pip

    # Install dependencies
    pip install -r requirements.txt

    #python post_deploy_script.py
    
    # Create migrations
    python manage.py makemigrations
    python manage.py migrate

    #python manage.py test
    coverage run
    coverage html
    # deactivate virtual environment
    deactivate

    # Restart gunicorn to create socket
    sudo systemctl restart gunicorn

    #Restart supervisor to reload celery workers
    sudo supervisorctl restart smarteye-api-celery-worker:*
    sudo supervisorctl restart smarteye-api-celery-beat:*
    
EOF
