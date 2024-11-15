"""
The flask application package.
"""

from flask import Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///2024_10_03.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'Fg++m5MJ1vBNbH0XSqhiCA==' #Sh5rl15ck!1'

from flask_login import LoginManager
from PrivyApp.models import  User
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

import PrivyApp.views
import PrivyApp.models
import PrivyApp.forms
import PrivyApp.constructionExpenses
import PrivyApp.main
import PrivyApp.Features.FilesBackupRun
