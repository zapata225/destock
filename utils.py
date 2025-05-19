from flask import render_template
from flask_mail import Message
from datetime import datetime
import re
from weasyprint import HTML

def is_valid_email(email):
    """Valide le format d'email"""
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def format_address(address_raw):
    """
    Formate une adresse à partir d'un dict 'raw'.
    Si c'est None ou vide, renvoie 'Adresse non disponible'.
    """
    if not address_raw or not isinstance(address_raw, dict):
        return "Adresse non disponible"
    parts = [
        address_raw.get('name', '').strip(),
        address_raw.get('street', '').strip(),
        f"{address_raw.get('zip', '').strip()} {address_raw.get('city', '').strip()}".strip(),
        address_raw.get('country', 'France').strip()
    ]
    lines = [line for line in parts if line]  # Retire les lignes vides
    if not lines:
        return "Adresse non disponible"
    return "<br>".join(lines)

def clean_address_string(address_str):
    """
    Nettoie une chaîne d'adresse brute pour éviter affichage comme ',  , France'
    """
    if not address_str:
        return "Adresse non disponible"
    # Supprime les virgules multiples, espaces, etc.
    cleaned = ", ".join(part.strip() for part in address_str.split(",") if part.strip())
    return cleaned if cleaned else "Adresse non disponible"

def send_confirmation_email(app, mail, order_data, recipient_email, html_content=None):
    try:
        print("=== DEBUG order_data ===")
        print(order_data)
        print("========================")

        subject = f"Confirmation de commande #{order_data.get('reference', '')}"
        products_config = app.config.get('PRODUCTS', [])
        products_info = []

        for product in order_data.get('products', []):
            product_id = product.get('id')
            quantity = product.get('quantity')

            product_cfg = next((p for p in products_config if str(p['id']) == str(product_id)), None)

            # Déterminer le prix
            price = None
            if product_cfg:
                price = product_cfg.get('price')
            else:
                price = product.get('unit_price') or product.get('price')

            # Sécurité : si quantity ou price est manquant, mettre des valeurs par défaut
            try:
                total = float(price) * int(quantity)
            except (TypeError, ValueError):
                total = 0.0

            products_info.append({
                'name': product.get('name') or (product_cfg.get('name') if product_cfg else 'Produit inconnu'),
                'quantity': quantity or 0,
                'unit_price': price or 0.0,
                'total': total
            })

        # Formate les adresses en HTML propre
        if 'delivery_address_raw' in order_data and order_data['delivery_address_raw']:
            order_data['delivery_address'] = format_address(order_data['delivery_address_raw'])
        else:
            order_data['delivery_address'] = clean_address_string(order_data.get('delivery_address', ''))

        if 'billing_address_raw' in order_data and order_data['billing_address_raw']:
            order_data['billing_address'] = format_address(order_data['billing_address_raw'])
        else:
            order_data['billing_address'] = clean_address_string(order_data.get('billing_address', ''))

        # Nettoyage téléphone : si vide, afficher 'Non fourni'
        phone = order_data.get('phone', '').strip()
        if not phone:
            phone = 'Non fourni'

        # Fallback si aucun contenu HTML n'est fourni
        if html_content is None:
            html_content = render_template(
                'email_confirmation.html',
                order=order_data,
                order_reference=order_data.get('id', ''),
                order_date=order_data.get('date', ''),
                order_total=order_data.get('total', 0.0),
                payment_method=order_data.get('payment_method', '').replace('transfer', 'virement bancaire'),
                products=products_info,
                company_info={
                    'name': 'Destockage Alimentaire France',
                    'address': '123 Rue du Commerce, 75000 Paris',
                    'phone': '+33 1 23 45 67 89',
                    'email': 'contact@destockagealimentaire.fr'
                },
                phone=phone,
                email=order_data.get('email', 'N/A'),
                delivery_address=order_data['delivery_address'],
                billing_address=order_data['billing_address'],
            )

        # Créez le PDF avec les informations complètes
        pdf_data = generate_pdf(order_data, products_info, phone)

        # Préparer le message
        msg = Message(
            subject=subject,
            recipients=[recipient_email, 'contact@destockagealimentaire.fr'],
            html=html_content,
            sender=app.config['MAIL_DEFAULT_SENDER']
        )

        # Attacher le PDF
        msg.attach(
            f"facture_commande_{order_data.get('reference', 'inconnue')}.pdf",
            "application/pdf",
            pdf_data
        )

        # Envoi de l'email
        mail.send(msg)
        app.logger.info(f"Email de confirmation envoyé à {recipient_email}")
        return True
    except Exception as e:
        app.logger.error(f"Erreur lors de l'envoi de l'email de confirmation: {str(e)}")
        return False


def generate_pdf(order_data, products_info, phone):
    """
    Génère le PDF de la commande avec toutes les informations fournies.

    :param order_data: dict contenant les informations de la commande (référence, date, total, etc.)
    :param products_info: liste de dicts avec les produits commandés (name, unit_price, quantity)
    :param phone: numéro de téléphone formaté
    :return: bytes du fichier PDF généré
    """
    html = render_template(
        'order_invoice.html',
        order=order_data,
        reference=order_data.get('reference', ''),
        date=order_data.get('date', ''),
        total=order_data.get('total', 0.0),
        payment_method=order_data.get('payment_method', '').replace('transfer', 'virement bancaire'),
        products=products_info,
        email=order_data.get('email', 'N/A'),
        phone=phone,
        address=order_data.get('delivery_address', 'Adresse non disponible'),
        billing_address=order_data.get('billing_address', 'Adresse non disponible'),
        company_info={
            'name': 'Destockage Alimentaire France',
            'address': '123 Rue du Commerce, 75000 Paris',
            'phone': '+33 1 23 45 67 89',
            'email': 'contact@destockagealimentaire.fr',
            'siret': '123 456 789 00010',
            'tva': 'FR12345678901'
        }
    )

    # Convertit le HTML en PDF avec WeasyPrint
    pdf_data = HTML(string=html).write_pdf()
    return pdf_data
