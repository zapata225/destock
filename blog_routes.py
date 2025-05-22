from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from datetime import datetime
import os
import markdown
from werkzeug.utils import secure_filename
import uuid

# Configuration du Blueprint
blog_bp = Blueprint('blog', __name__, 
                   template_folder='templates/blog',
                   static_folder='static/blog')

# Configuration des uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
BLOG_UPLOAD_FOLDER = 'static/blog/uploads'
os.makedirs(BLOG_UPLOAD_FOLDER, exist_ok=True)

# Données des articles (à remplacer par une base de données en production)
blog_posts = {
    'premier-article': {
        'id': 'premier-article',
        'title': "Destockage Alimentaire : 7 Avantages Insoupçonnés pour Votre Business",
        'slug': 'premier-article',
        'author': "Équipe DestockPro",
        'date': "2023-10-15",
        'image': 'blog1.jpg',
        'excerpt': "Découvrez comment le destockage alimentaire peut transformer votre activité avec ces avantages méconnus.",
        'content': """## Introduction\n\nLe destockage alimentaire est une solution...""",
        'categories': ['professionnels', 'économie'],
        'seo': {
            'title': "Destockage Alimentaire : 7 Avantages pour Professionnels",
            'description': "Découvrez les 7 bénéfices méconnus du destockage alimentaire pour les professionnels. Réduisez vos coûts jusqu'à 70%.",
            'keywords': "destockage alimentaire avantages, économie restauration, réduire coûts alimentaires"
        }
    }
}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_slug(title):
    """Génère un slug à partir du titre"""
    return title.lower().replace(' ', '-').replace("'", "").replace('"', '')

@blog_bp.route('/blog')
def blog_home():
    """Page d'accueil du blog avec tous les articles"""
    # Convertir la date en datetime dans chaque post
    for post in blog_posts.values():
        if isinstance(post['date'], str):
            post['date'] = datetime.strptime(post['date'], "%Y-%m-%d")
    
    # Trier les articles par date (du plus récent au plus ancien)
    sorted_posts = sorted(blog_posts.values(), 
                          key=lambda x: x['date'], 
                          reverse=True)
    
    return render_template('blog_home.html',
                           posts=sorted_posts,
                           meta={
                               'title': 'Blog Destockage Alimentaire - Conseils pour professionnels',
                               'description': 'Tous nos articles sur le destockage alimentaire pour les professionnels de la restauration et de la grande distribution',
                               'keywords': 'blog destockage, conseils professionnels, actualité alimentaire'
                           })


@blog_bp.route('/blog/<slug>', endpoint='blog_post')
def blog_post(slug):
    """Page d'un article individuel"""
    post = blog_posts.get(slug)
    if not post:
        abort(404)
    
    # Convertir le markdown en HTML
    html_content = markdown.markdown(post['content'])
    
    # Articles similaires (même catégorie)
    related_posts = [
        p for p in blog_posts.values() 
        if slug != p['slug'] and 
        any(cat in p['categories'] for cat in post['categories'])
    ][:3]
    
    return render_template('blog_post1.html',
                         post=post,
                         content=html_content,
                         related_posts=related_posts,
                         meta=post.get('seo', {}))

@blog_bp.route('/blog/category/<category>')
def blog_category(category):
    """Page des articles par catégorie"""
    category_posts = [p for p in blog_posts.values() if category in p['categories']]
    
    if not category_posts:
        abort(404)
    
    return render_template('blog_category.html',
                         posts=category_posts,
                         category=category.capitalize(),
                         meta={
                             'title': f'Articles sur {category} - Blog Destockage',
                             'description': f'Tous nos articles sur le thème {category} pour les professionnels du destockage alimentaire'
                         })

# --- Section Admin ---

@blog_bp.route('/admin/blog/new', methods=['GET', 'POST'])
def admin_new_post():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        try:
            # Récupération des données du formulaire
            title = request.form['title']
            content = request.form['content']
            excerpt = request.form['excerpt']
            categories = request.form.getlist('categories')
            author = request.form['author']
            date = request.form['date'] or datetime.now().strftime("%Y-%m-%d")
            
            # Génération du slug
            slug = generate_slug(title)
            
            # Gestion de l'image
            image = None
            if 'image' in request.files:
                file = request.files['image']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file.save(os.path.join(BLOG_UPLOAD_FOLDER, unique_filename))
                    image = unique_filename
            
            # Création du nouvel article
            new_post = {
                'id': str(uuid.uuid4()),
                'title': title,
                'slug': slug,
                'author': author,
                'date': date,
                'image': image,
                'excerpt': excerpt,
                'content': content,
                'categories': categories,
                'seo': {
                    'title': request.form.get('seo_title', title),
                    'description': request.form.get('seo_description', excerpt),
                    'keywords': request.form.get('seo_keywords', '')
                }
            }
            
            blog_posts[slug] = new_post
            flash('Article publié avec succès!', 'success')
            return redirect(url_for('blog.blog_post', slug=slug))
            
        except Exception as e:
            flash(f"Erreur lors de la création de l'article: {str(e)}", 'error')
    
    return render_template('admin/blog_edit.html',
                         post=None,
                         categories=['professionnels', 'économie', 'logistique', 'qualité', 'tendances'])

@blog_bp.route('/admin/blog/edit/<slug>', methods=['GET', 'POST'])
def admin_edit_post(slug):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    post = blog_posts.get(slug)
    if not post:
        abort(404)
    
    if request.method == 'POST':
        try:
            # Mise à jour des données
            post['title'] = request.form['title']
            post['content'] = request.form['content']
            post['excerpt'] = request.form['excerpt']
            post['categories'] = request.form.getlist('categories')
            post['author'] = request.form['author']
            post['date'] = request.form['date']
            
            # Gestion de l'image
            if 'image' in request.files:
                file = request.files['image']
                if file and allowed_file(file.filename):
                    # Supprimer l'ancienne image si elle existe
                    if post['image'] and os.path.exists(os.path.join(BLOG_UPLOAD_FOLDER, post['image'])):
                        os.remove(os.path.join(BLOG_UPLOAD_FOLDER, post['image']))
                    
                    # Sauvegarder la nouvelle image
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    file.save(os.path.join(BLOG_UPLOAD_FOLDER, unique_filename))
                    post['image'] = unique_filename
            
            # Mise à jour SEO
            post['seo'] = {
                'title': request.form.get('seo_title', post['title']),
                'description': request.form.get('seo_description', post['excerpt']),
                'keywords': request.form.get('seo_keywords', '')
            }
            
            flash('Article mis à jour avec succès!', 'success')
            return redirect(url_for('blog.blog_post', slug=slug))
            
        except Exception as e:
            flash(f"Erreur lors de la mise à jour: {str(e)}", 'error')
    
    return render_template('admin/blog_edit.html',
                         post=post,
                         categories=['professionnels', 'économie', 'logistique', 'qualité', 'tendances'])

@blog_bp.route('/admin/blog/delete/<slug>', methods=['POST'])
def admin_delete_post(slug):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Non autorisé'}), 401
    
    post = blog_posts.get(slug)
    if not post:
        return jsonify({'success': False, 'message': 'Article non trouvé'}), 404
    
    try:
        # Supprimer l'image associée
        if post['image'] and os.path.exists(os.path.join(BLOG_UPLOAD_FOLDER, post['image'])):
            os.remove(os.path.join(BLOG_UPLOAD_FOLDER, post['image']))
        
        # Supprimer l'article
        del blog_posts[slug]
        
        return jsonify({'success': True, 'message': 'Article supprimé'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
