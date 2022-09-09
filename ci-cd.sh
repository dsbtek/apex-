#!/bin/sh

#Move staging .env file into temp folder
rsync -vzrh ./.env.staging root@185.130.207.215:/var/www/PYTHON/smarteye_api/temp

rsync -vzrh --exclude-from="exclude.txt" . root@185.130.207.215:/var/www/PYTHON/smarteye_api/temp

ssh root@185.130.207.215 <<-EOF
    cd /var/www/PYTHON/smarteye_api
    rm -rf ./backup # Delete previous backup
    mv ./live ./backup # Create new backup
    mv ./temp ./live
    mkdir ./temp # create new temp directory for next deployment
    cd ./live
    mv .env.staging .env #rename .env.staging to .env

    # cp ../config/dbconfig.py ./atg_web
    
    # Install virtual env
    python3.6 -m venv .virtualenv

    # Activate virtual environment
    source .virtualenv/bin/activate

    # upgrade pip
    pip install --upgrade pip

    # Install dependencies
    pip install -r requirements.txt

    #python post_deploy_script.py
    # Create migrations (DONT MIGRATE !!! CONNECTION ON STAGING IS TO PROD BB)

    #Run tests
    python manage.py test
    
    # deactivate virtual environment
    deactivate

    # Restart gunicorn to create socket
    systemctl restart gunicorn
EOF
