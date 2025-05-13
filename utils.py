from flask import render_template
from flask_mail import Message
from datetime import datetime
import re

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

        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            html=html_content,
            sender=app.config['MAIL_DEFAULT_SENDER']
        )

        mail.send(msg)
        app.logger.info(f"Email de confirmation envoyé à {recipient_email}")
        return True
    except Exception as e:
        app.logger.error(f"Erreur lors de l'envoi de l'email de confirmation: {str(e)}")
        return False
