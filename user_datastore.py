from flask_security import SQLAlchemySessionUserDatastore
# --- Import db instance ---
from .database import db
# --- Import BOTH User and Role models ---
from .models import User, Role

# --- Initialize the datastore with BOTH models ---
user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)

print("User datastore initialized with User and Role models.") # Optional confirmation