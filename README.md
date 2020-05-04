# Student Service
A small web service for students and professors written in Python using the Django framework with MySQL.

## Overview 
The service is a representation of what a real world student service used by universities might look like. It is intended to help students and professors by offering some basic role dependent functionalities, such as managing class schedules, exam schedules, bulletin posts, sending news to groups of students via Email (Gmail API), managing profiles etc.

## Functionalities

#### There are 4 types of users (roles):
* Administrators
* Secretaries
* Professors
* Students

Functionalities available for all users:
* Login (simulation - checking if a user exists in the database by the provided username)
* Preview of the class schedule of the current active semester
* Preview of the bulletin board and downloading attachments
* Logout

#### Administrators and secretaries:
* Upload the class schedule of the current active semester (CSV file)
* Upload the exam schedule (CSV file - invalid rows are shown with the appropriate error message, the user can edit them directly on the web page or upload another file)
* Post bulletins with or without attachments
* Send emails to a specific group of students with or without attachments (by class, by course, by department or to every student) - Gmail API
* Adding semesters
* Adding elective classes
* Preview of all the elective classes that were chosen by students (active elective classes)
* Preview of students and courses of an active elective class
* Preview of all the classes grouped by courses
* Preview of all the students grouped by classes
* Preview of any student profile

#### Professors:
* Preview of the class schedule for the courses he is teaching
* Preview of all the classes grouped by courses he is teaching
* Preview of all the students of a class he is teaching
* Send emails to a specific group of students with or without attachments (only students attending his lectures - by course or class) - Gmail API

#### Students:
* Preview of the class schedule for courses he is attending
* Upload profile picture
* Choose elective class

## Sidenote
This project was an assignment as part of the course - Script languages in the 3rd year at the Faculty of Computer Science in Belgrade. All service functionalities were defined in the assignment specifications.

## Contributors
- Stefan Ginic - <stefangwars@gmail.com>
