# cataloging-statistics

## Purpose

This is an application which allows cataloging staff to generate statistical reports from Alma data.
The data is exported from Alma weekly via an Analytics report, transformed to support flexible reporting,
and imported into a PostgreSQL database.

## Developer Information

### Overview of environment

The development environment requires:
* git
* docker (current version recommended: 27.0.3)
* docker compose (now part of docker itself)

#### PostgreSQL container

The development database is PostgreSQL 16, to match our central production database environment.

#### Django container

This uses Django 5.2 LTS, which requires Python 3.10 or later; the container uses Python 3.12.
It shouldn't matter what version of Python is used locally, as all code runs in the container.

The container runs via `docker_scripts/entrypoint.sh`, which
* Updates container with any new requirements, if the image hasn't been rebuilt (DEV environment only).
* Waits for the database to be completely available, which usually takes 5 seconds or less.
* Applies any pending migrations (DEV environment only).
* Creates a generic Django superuser, if one does not already exist (DEV environment only).
* Starts the Django application server.

### Setup
1. Clone the repository.

   `$ git clone git@github.com:UCLALibrary/cataloging-statistics.git`

2. Change directory into the project.

   `$ cd cataloging-statistics`

3. Build using docker-compose.

   `$ docker compose build`

4. Bring the system up, with containers running in the background.  *Note*: You'll need 
`.docker-compose_secrets.env`, which contains an Alma API key; ask a teammate for this file.

   `$ docker compose up -d`

5. Logs can be viewed, if needed (`-f` to tail logs).

   ```
   $ docker compose logs -f db
   $ docker compose logs -f django
   ```

6. Run commands in the containers, if needed.

   ```
   $ docker compose exec db psql -U cataloging_stats
   $ docker compose exec django bash
   # Django-aware Python shell
   $ docker compose exec django python manage.py shell
   # Apply new migrations without a restart
   $ docker compose exec django python manage.py migrate
   # Load current Analytics data into local database (replace YYYYMM with current year and month)
   $ docker compose exec django python manage.py refresh_analytics_data -m YYYYMM
   ```

7. Connect to the running application via browser

   [Application](http://127.0.0.1:8000) and [Admin](http://127.0.0.1:8000/admin)

8. Edit code locally.  All changes are immediately available in the running container, but if a restart is needed:

   `$ docker compose restart django`

9. Shut down the system when done.

   `$ docker compose down`
