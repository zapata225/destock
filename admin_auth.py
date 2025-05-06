from werkzeug.security import generate_password_hash

# À REMPLACER IMMÉDIATEMENT APRÈS LES TESTS
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password_hash': generate_password_hash('010203')
}
