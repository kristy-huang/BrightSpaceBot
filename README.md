<p align="center">
  <img src="https://github.com/kristy-huang/BrightSpaceBot/blob/master/Brightspacebot%20cropped.png" />
</p>

# About BrightSpace Bot
Many college students utilize the online platform, BrightSpace, for accessing class content and managing assignments. Downloading lectures, documents, and checking due dates are frequently executed tasks that students spend too much time doing. For example, currently students must manually navigate to each class page and filter through all folders set up by their professor in order to download the appropriate resources to complete assignments. The BrightspaceBot aims to automate these redundant tasks, so that students are well prepared for their classes. 

# Setting up BrightSpace Bot
**To set up an account:** Visit our website https://brightspace-bot.herokuapp.com/ to register an account. You will need to create a username and password as well as provide your major, storage location and notification frequency preferences. Afterwards, you can add the bot to your discord server of choice. 

# Registering an Account Through Duo Mobile
To link your BrightSpace account with BrightSpace Bot, you must register a new Duo Mobile device. To register a device, please follow the steps here: https://www.purdue.edu/apps/account/BoilerKey/ and save the URL you get at the end of the process. 



# Using the virtual environment (Pipenv):\
`pipenv shell` - Launches a subshell in virtual environment, which contains all of the packages you need in the project as listed in the Pipfile

Setting up config:\
create a `config.py` file in the root folder.\
The config file should contain:\
`database_uri_dev = 'mysql://<username>:<password>@<host>/<db_name>'`\
`database_uri_prod = 'mysql://<username>:<password>@<host>/<db_name>'`\
`secret_key = '<put some secret key>'`\
`track_modifications = False`

Setting up the database:\
`pipenv shell` \
`python db_create.py` 

Running the website backend:\
Make sure you are in a pipenv shell, you don't need to run `pipenv shell` again if you are already in a shell\
Stay in the root folder containing 'webapp.py' and run:\
`flask run`

Running the frontend website:\
Open a separate terminal from the website backend and run:\
`cd web`\
`npm start`

Troubleshoot:\
If you are getting errors such as:
ModuleNotFoundError: No module named 'flask_marshmallow', make sure you are in a pipenv shell 
