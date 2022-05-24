

Welcome to MyChatApp

in this webapp, you can chat with your friends privately or create a group to chat with them

This app uses Django/Channels and websocket

To run The app you have two options:

1- Using Django:

first clone the repository. make sure you have installed redis and postgres database. you can change the postgres configuration in /MyChattApp/.env file

then run the following command:

  python manage.py makemigrations
  python manage.py migrate
  python runserver

2 - Using Docker:

checkout to the dockerized branch with following command:

git checkout dockerized

then run the following commands: `sudo docker-compose up --build
