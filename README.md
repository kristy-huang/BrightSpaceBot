####Using the virtual environment (Pipenv):
`pipenv shell` - Launches a subshell in virtual environment, which contains all of the packages you need in the project as listed in the Pipfile

####Setting up config:
create a `config.py` file in the root folder.\
The config file should contain:\
`database_uri_dev = 'mysql://<username>:<password>@<host>/<db_name>'`\
`database_uri_prod = 'mysql://<username>:<password>@<host>/<db_name>'`\
`secret_key = '<put some secret key>'`\
`track_modifications = False`

####Setting up the database:
`pipenv shell` \
`python db_create.py` 

####Running the website backend:
Make sure you are in a pipenv shell, you don't need to run `pipenv shell` again if you are already in a shell\
Stay in the root folder containing 'webapp.py' and run:\
`flask run`

####Running the frontend website:
Open a separate terminal from the website backend and run:\
`cd web`\
`npm start`

####Troubleshoot:
If you are getting errors such as:
ModuleNotFoundError: No module named 'flask_marshmallow', make sure you are in a pipenv shell 