# institute_time
LMS TO TASHKENT INSTITUTE OF MANAGEMENT AND ECONOMICS
Take all students from HEMIS. And create student oportunity 

-1. Create PostgreSql database in your system.For example:
```
sudo -u postgres psql
postgres=# create database mydb;
postgres=# create user myuser with encrypted password 'mypass';
postgres=# grant all privileges on database mydb to myuser;
postgres=# \c mydb
postgres=# grant all on schema public to myuser;
postgres=# grant usage on schema public to myuser;
```
-2.Create .env file in core/envs folder like .env.example file
-3.Migrate and run program
```
python manage.py migrate
python manage.py runserver
```