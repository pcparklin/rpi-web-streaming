#!/bin/bash
FILE=/dev/shm/web.db

rm -f /dev/shm/web.db
sudo -u pi sqlite3 $FILE "create table if not exists OVERLAY(ID INTEGER PRIMARY KEY AUTOINCREMENT,X INT NOT NULL, Y INT NOT NULL, TEXT TEXT, COLOR CHAR(6) NOT NULL, PY INT NOT NULL, PU INT NOT NULL, PV INT NOT NULL, URL BLOB NOT NULL, MODIFIED CHAR(19) NOT NULL);"
sqlite3 $FILE "insert into OVERLAY (X, Y, TEXT, COLOR, PY, PU, PV, URL, MODIFIED) values (800, 100, 'Hello World', 'ffcf5e', 223, 56, 184, 'http://www.youtube.com/user/youraccount/live', '----/--/-- --:--:--');"