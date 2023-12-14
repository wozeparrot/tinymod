import sqlite3

with sqlite3.connect("tinymod.db") as connection:
  c = connection.cursor()

messages = c.execute("SELECT content FROM logging_messages WHERE content != 'NULL'").fetchall()

with open("messages.txt", "w") as f:
  for message in messages:
    message = " ".join(message[0].split("\n"))
    f.write(message + "\n")
