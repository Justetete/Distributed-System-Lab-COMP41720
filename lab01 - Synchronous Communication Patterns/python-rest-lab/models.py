class Users:
    user_lists = {}

    def __init__(self, name, id, email):
        self.name = name
        self.id = id
        self.email = email
        Users.user_lists[self.id] = self

    @staticmethod
    def show_users():
        """
        Return all users as a list of dictionaries
        """
        users = []
        for user_id, user_obj in Users.user_lists:
            users.append(
                {'id': user_id,
                 'name': user_obj.name,
                 'email': user_obj.email}
            ) # Create a JSON formate of user
            return users
    
    @staticmethod
    def get_user(user_id):
        """
        Return specific user by given id
        """
        user_obj = Users.user_lists.get(user_id)
        if user_obj:
            return {
                'id': user_obj.id,
                 'name': user_obj.name,
                 'email': user_obj.email
            }
        return None
    
    @staticmethod
    def user_exists(user_id):
        """Check if a user exists"""
        return user_id in Users.user_lists
    
    @staticmethod
    def update_user(user_id,data):
        """
        Update user info by given user id
        """
        if Users.user_exists(user_id):
            user_obj = Users.user_lists[user_id]
            # Update fields if provided in data
            if 'name' in data:
                user_obj.name = data['name']
            if 'email' in data:
                user_obj.email = data['email']
            
            return {
                'id': user_id,
                'name': user_obj.name,
                'email': user_obj.email
            }
        return None

    @staticmethod
    def delete_user(user_id):
        """Delete a user and return the deleted user data"""
        
        if Users.user_exists(user_id):
            user_obj = Users.user_lists.pop(user_id)

            return {
                'id': user_obj.id,
                'name': user_obj.name,
                'email': user_obj.email
            }
        return None
    
    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email
        }




