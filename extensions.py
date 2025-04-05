# יבוא המודול בשכדי שנוכל לעבוד עם דאטה בייס
from flask_sqlalchemy import SQLAlchemy
# 
from flask_login import LoginManager, current_user, login_user, logout_user

db = SQLAlchemy()
login_manager = LoginManager()