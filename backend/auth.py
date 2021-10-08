import bcrypt


def get_hash_for_user(user):
    return user.password


def get_salt_for_user(user):
    return user.salt


def create_password_hash(password):
    salt = bcrypt.gensalt(16)
    hashed_pass = bcrypt.hashpw(password, salt)
    return hashed_pass, salt


def check_hash_for_user(password, user):
    stored_hash = get_hash_for_user(user)
    generated_hash = recreate_hash(password, get_salt_for_user(user))
    return stored_hash == generated_hash


def recreate_hash(password, salt):
    return bcrypt.hashpw(str(password), str(salt))


def validate(user, password):
    return check_hash_for_user(password, user)
