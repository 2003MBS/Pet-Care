from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime
import os

class User:
    def __init__(self, email, name, password_hash=None, id=None, is_active=True):
        self.id = id or str(datetime.utcnow().timestamp())
        self.email = email
        self.name = name
        self.password_hash = password_hash
        self.is_active = is_active
        self.created_at = datetime.utcnow().isoformat()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.email

    @staticmethod
    def get_by_email(email):
        try:
            with open('data/users.json', 'r') as f:
                data = json.load(f)
                for user_data in data['users']:
                    if user_data['email'] == email:
                        return User.from_dict(user_data)
        except FileNotFoundError:
            return None
        return None

    @staticmethod
    def from_dict(data):
        user = User(
            email=data['email'],
            name=data['name'],
            password_hash=data.get('password_hash'),
            id=data.get('id'),
            is_active=data.get('is_active', True)
        )
        return user

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'password_hash': self.password_hash,
            'is_active': self.is_active,
            'created_at': self.created_at
        }

    @staticmethod
    def save_user(user):
        try:
            if not os.path.exists('data'):
                os.makedirs('data')
                
            try:
                with open('data/users.json', 'r') as f:
                    data = json.load(f)
            except FileNotFoundError:
                data = {'users': []}

            # Check if user already exists
            for i, existing_user in enumerate(data['users']):
                if existing_user['email'] == user.email:
                    # Update existing user
                    data['users'][i] = user.to_dict()
                    break
            else:
                # Add new user
                data['users'].append(user.to_dict())

            # Save to file
            with open('data/users.json', 'w') as f:
                json.dump(data, f, indent=4)
                
            return True
        except Exception as e:
            print(f"Error saving user: {str(e)}")
            return False 