from flask import render_template
from flask_mail import Message
from flask import send_file
from datetime import datetime
import re
from io import BytesIO
from weasyprint import HTML
import os

def is_valid_email(email):
    """Valide le format d'email"""
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def send_confirmation_email(app, mail, order_data, recipient_email, html_content=None):
    try:
        subject = f"Confirmation de commande #{order_data.get('reference', '')}"

        # Fallback si aucun contenu HTML n'est fourni
        if html_content is None:
            html_content = render_template(
                'email_confirmation.html',
                order=order_data,
                order_reference=order_data.get('reference'),
                order_date=order_data.get('date'),
                order_total=order_data.get('total'),
                payment_method=order_data.get('payment_method', '').replace('transfer', 'virement bancaire')
            )

        # Créez le PDF à partir du template HTML
        pdf_data = generate_pdf(order_data)

        # Préparer le message
        msg = Message(
            subject=subject,
            recipients=[recipient_email, 'contact@destockagealimentaire.fr'],
            html=html_content,
            sender=app.config['MAIL_DEFAULT_SENDER']
        )

        # Attacher le PDF
        msg.attach(
            f"facture_commande_{order_data.get('reference')}.pdf",
            "application/pdf",
            pdf_data
        )

        # Envoi de l'email
        mail.send(msg)
        app.logger.info(f"Email de confirmation envoyé à {recipient_email} et en copie à contact@destockagealimentaire.fr")
        return True
    except Exception as e:
        app.logger.error(f"Erreur lors de l'envoi de l'email de confirmation: {str(e)}")
        return False

def generate_pdf(order_data):
    """Génère le PDF de la commande"""
    html = render_template(
        'order_invoice.html',
        order=order_data,
        reference=order_data.get('reference'),
        date=order_data.get('date'),
        total=order_data.get('total'),
        payment_method=order_data.get('payment_method'),
        products=order_data.get('products'),
        email=order_data.get('email'),   # Email du client
        phone=order_data.get('phone'),   # Numéro de téléphone du client
        address=order_data.get('address'),
        billing_address=order_data.get('billing_address')
    )

    # Utilisation de WeasyPrint pour convertir HTML en PDF
    pdf_data = HTML(string=html).write_pdf()
    return pdf_data
