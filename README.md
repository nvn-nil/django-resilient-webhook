[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# Django Resilient Webhook

Implements a resilient webhooks receiver and sender architecture. Uses duplex (TBD) queues for increased resilience against receiver downtime.

### Set up

Open the project in vscode .devcontainer

Create a file `.devcontainer/docker-compose.developer.yml`. This allows you to customise extra services and volumes you make available to the container.
For example, you can map your own gcloud config folder into the container to use your own credentials. You can just leave the services key empty if you want.

Create a file `.env` for environment variables required by the app

```
MAXWELL_PROJECT_ID=project-name
```

App uses default google credentials, you can also specify your GCP credentials using `MAXWELL_SERVICE_ACCOUNT_INFO` environment variable with the content of your credential file.

```
MAXWELL_SERVICE_ACCOUNT_INFO='{"type": "service_account", ..., "universe_domain": "googleapis.com"}'
```

This is very useful when the Maxwell data platform is in a different project and cannot use the default application credentials.

### Use the example app

You can start the example app (which has django-maxwell setup).

Initially, do:

```
python manage.py migrate
python manage.py createsuperuser
# make yourself a user account at the prompt
```

Then to run the app, do:

```
python manage.py runserver
```

...and visit [http://localhost:8000/admin/](http://localhost:8000/admin/) to sign in.
