create table if not exists users (
    id integer primary key autoincrement,
    title text,
    name text not null,
    username text not null,
    password text not null,
    email text not null,
    type integer not null,
    reset text not null default ""
);

create table if not exists passphrase(
    id integer primary key,
        passphrase text
);

create table if not exists sessions (
    id integer primary key autoincrement,
    semester integer not null,
    years text not null,
    current integer not null default 0,
	FOREIGN KEY(semester) REFERENCES semester_types(id)
);

create table if not exists courses(
    id integer primary key autoincrement,
    course text not null,
    field text not null,
    students_number integer not null default 0
);

insert into users (title, name, username, password, email, type)
    values ('Ms', 'Tanja Breinig', 'admin', 'coco2015', 'admin@cs.uni-saarland.de', 0)
;
insert into passphrase (passphrase) values ('defaultpass');

insert into users (title, name, username, password, email, type)
    values ('Mr', 'John Doe', 'doe', 'default', 'john.doe@cs.uni-saarland.de', 1)
;

create table if not exists weekdays (
    weekday_id integer primary key autoincrement,
    name text not null
);

insert into weekdays (name) values ('Monday');
insert into weekdays (name) values ('Tuesday');
insert into weekdays (name) values ('Wednesday');
insert into weekdays (name) values ('Thursday');
insert into weekdays (name) values ('Friday');

create table if not exists timeslots (
    timeslot_id integer primary key autoincrement,
    time text not null
);

insert into timeslots (timeslot_id, time) values (1, '08.00 - 10.00');
insert into timeslots (timeslot_id, time) values (2, '10.00 - 12.00');
insert into timeslots (timeslot_id, time) values (3, '12.00 - 14.00');
insert into timeslots (timeslot_id, time) values (4, '14.00 - 16.00');
insert into timeslots (timeslot_id, time) values (5, '16.00 - 18.00');

create table if not exists preference_codes (
    preference_id integer primary key unique,
    comment text not null
);

insert into preference_codes (preference_id, comment) values (0, 'Does not fit');
insert into preference_codes (preference_id, comment) values (1, 'Neutral');
insert into preference_codes (preference_id, comment) values (2, 'Possible');
insert into preference_codes (preference_id, comment) values (3, 'Best fit');

create table if not exists preferences (
    entry_id integer primary key autoincrement,
    user_id integer not null,
    weekday_id integer not null,
    timeslot_id integer not null,
    preference_id integer not null,
    course_id integer not null,
    hours text,
    semester_id integer not null,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(weekday_id) REFERENCES weekdays(weekday_id),
    FOREIGN KEY(timeslot_id) REFERENCES timeslots(timeslot_id),
    FOREIGN KEY(preference_id) REFERENCES preference_codes(preference_id),
    FOREIGN KEY(semester_id) REFERENCES sessions(id)
);

create table if not exists busy_timeslots (
    entry_id integer primary key autoincrement,
    weekday_id integer not null,
    timeslot_id integer not null,
    reason_id integer not null,
    semester_id integer not null,
    FOREIGN KEY(weekday_id) REFERENCES weekdays(weekday_id),
    FOREIGN KEY(timeslot_id) REFERENCES timeslots(timeslot_id),
    FOREIGN KEY(reason_id) REFERENCES reasons(reason_id),
    FOREIGN KEY(semester_id) REFERENCES sessions(id)
);

create table if not exists reasons (
    reason_id integer primary key autoincrement,
    comment text not null
);
insert into reasons (comment) values ('Advanced VC course');

create table if not exists schedule (
    weekday_id integer not null,
    timeslot_id integer not null,
    course_id integer not null,
	room_id integer not null,
    semester_id integer not null,
    PRIMARY KEY(weekday_id, timeslot_id, course_id, room_id, semester_id),
    FOREIGN KEY(weekday_id) REFERENCES weekdays(weekday_id),
    FOREIGN KEY(timeslot_id) REFERENCES timeslots(timeslot_id),
    FOREIGN KEY(course_id) REFERENCES courses(id),
    FOREIGN KEY(semester_id) REFERENCES sessions(id),
    FOREIGN KEY(room_id) REFERENCES rooms(room_id)
);

create table if not exists basic_schedule (
    weekday_id integer not null,
    timeslot_id integer not null,
    bcourse_id integer not null,
	room_id integer not null,
    semester_id integer not null,
    PRIMARY KEY(weekday_id, timeslot_id, bcourse_id, room_id, semester_id),
    FOREIGN KEY(weekday_id) REFERENCES weekdays(weekday_id),
    FOREIGN KEY(timeslot_id) REFERENCES timeslots(timeslot_id),
    FOREIGN KEY(bcourse_id) REFERENCES basic_courses(id),
    FOREIGN KEY(semester_id) REFERENCES semester_types(id),
    FOREIGN KEY(room_id) REFERENCES rooms(room_id)
);
create table if not exists semester_types (
    id integer primary key,
    semester text not null
);
insert into semester_types (id, semester) values (1,'winter semester');
insert into semester_types (id, semester) values (2, 'summer semester');

create table if not exists rooms (
    room_id integer primary key autoincrement,
    name text not null,
    location text not null,
	max_capability integer not null
);
insert into rooms (room_id, name, location, max_capability) values (1,'Lecture Hall I', 'E 1.3', 99);
insert into rooms (room_id, name, location, max_capability) values (2,'Lecture Hall II', 'E 1.3', 170);
insert into rooms (room_id, name, location, max_capability) values (3,'Lecture Hall III', 'E 1.3', 99);
insert into rooms (room_id, name, location, max_capability) values (4,'Guenter Hotz Hall', 'E 2.2', 450);
insert into rooms (room_id, name, location, max_capability) values (5,'Lecture Hall I', 'E 2.5', 314);

--Winter semester
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(1,4,1,5,1);
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(2,4,2,4,1);
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(4,2,2,4,1);
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(3,4,3,4,1);
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(5,2,3,4,1);
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(4,3,4,4,1);
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(3,2,5,4,1);
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(5,2,5,4,1);
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(3,1,6,5,1);
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(5,3,6,5,1);

--Summer semester
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(2,4,7,4,2);
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(5,1,7,4,2);
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(1,1,8,4,2);
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(3,1,8,4,2);
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(1,4,9,2,2);
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(2,2,9,2,2);
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(2,3,10,4,2);
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(4,2,10,4,2);
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(3,2,11,4,2);
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(5,2,11,4,2);
insert into basic_schedule (weekday_id, timeslot_id, bcourse_id, room_id, semester_id)
values(2,3,12,2,2);

create table if not exists basic_courses(
    id integer primary key autoincrement,
    course text not null
);

insert into basic_courses (id,course) values (1,'Perspektiven der Informatik');
insert into basic_courses (id,course) values (2,'Programmierung 1');
insert into basic_courses (id,course) values (3,'Theoretische Informatik');
insert into basic_courses (id,course) values (4,'Algorithmen und Datenstrukturen');
insert into basic_courses (id,course) values (5,'MfI 1');
insert into basic_courses (id,course) values (6,'MfI 3');

insert into basic_courses (id,course) values (7,'Programmierung 2');
insert into basic_courses (id,course) values (8,'Systemarchitektur');
insert into basic_courses (id,course) values (9,'Nebenlaeufige Programmierung');
insert into basic_courses (id,course) values (10,'Informationssysteme');
insert into basic_courses (id,course) values (11,'MfI 2');
insert into basic_courses (id,course) values (12,'PfI');

create table if not exists constr(
    id integer primary key,
    active text
);

insert into constr (id, active) values (1, 'c1 c2 c3 c4 c5 c6 c7');
