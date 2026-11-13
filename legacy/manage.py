from flask.ext.script import (Manager, Server)
from app import app


manager = Manager(app)


#Run local server
manager.add_command("runserver", Server("localhost", port = 5000))


if __name__ == '__main__':
    manager.run()
