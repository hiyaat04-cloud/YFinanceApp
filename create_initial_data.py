# In create_initial_data.py

from flask_security import hash_password # Although not used anymore, keep for potential future use
from applications.models import Role # Ensure Role model is defined in models.py
import uuid # Import the uuid module (though not used in this version)

def create_data(app, db, datastore):
    """
    Creates the initial 'user' role if it doesn't already exist in the database.
    Uses the provided datastore object for interaction.
    """
    print("Checking/creating initial 'user' role...")
    with app.app_context(): # Ensure operations are within app context
        # --- Create 'user' Role ---
        user_role_name = "user"

        # Check if 'user' role exists
        if not datastore.find_role(user_role_name):
             print(f"Creating '{user_role_name}' role...")
             # Create the standard user role
             datastore.create_role(name=user_role_name, description="Standard user permissions")
             db.session.commit() # Commit after creating role
             print(f"'{user_role_name}' role created.")
        else:
            print(f"'{user_role_name}' role already exists.")

        # --- Removed Admin Role and Admin User Creation ---

        print("Initial role check complete.")

