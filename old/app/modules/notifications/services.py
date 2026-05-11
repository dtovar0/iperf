import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.modules.notifications.models import SMTPConfig, NotificationTemplate, InAppNotification

def add_in_app_notification(type, title, message, user_id=None):
    """
    Creates a persistent in-app notification.
    type: success, error, warning, info
    user_id: ID of the user (NULL for global)
    """
    from app import db
    try:
        notif = InAppNotification(
            type=type,
            title=title,
            message=message,
            user_id=user_id
        )
        db.session.add(notif)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error adding notification: {e}")
        db.session.rollback()
        return False


def send_test_email(server, port, encryption, username, password, sender_name, target_email):
    """
    Sends a test email to verify SMTP configuration.
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = f"{sender_name} <{username}>"
        msg['To'] = target_email
        msg['Subject'] = "⚡ Nexus Premium - SMTP Verification"

        body = f"""
        <html>
            <body style="font-family: sans-serif; color: #1a1a1a;">
                <h2 style="color: #6366f1;">⚡ Nexus System Verification</h2>
                <p>Usted está recibiendo este mensaje porque se ha solicitado una prueba de conectividad desde el panel de administración.</p>
                <div style="background: #f8fafc; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0;">
                    <p><b>Status:</b> Conexión Exitosa</p>
                    <p><b>Servidor:</b> {server}:{port}</p>
                    <p><b>Cifrado:</b> {encryption.upper()}</p>
                </div>
            </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        if encryption == 'ssl':
            smtp = smtplib.SMTP_SSL(server, port, timeout=10)
        else:
            smtp = smtplib.SMTP(server, port, timeout=10)
            if encryption == 'starttls':
                smtp.starttls()
                
        import os
        if os.getenv('DEBUG_SMTP') == 'true':
            smtp.set_debuglevel(1)

        if username and password:
            smtp.login(username, password)

        smtp.send_message(msg)
        smtp.quit()
        return {"status": "success", "message": "Correo de prueba enviado correctamente"}
    except Exception as e:
        return {"status": "error", "message": "Error al enviar correo de prueba."}

def send_notification_by_slug(slug, target_email, context=None):
    """
    Sends a pre-defined notification template using the global SMTP configuration.
    """
    from app import db
    import os
    from dotenv import load_dotenv
    
    # Reload env to catch changes without restart
    load_dotenv(override=True)
    
    # Global Switch Check
    if os.getenv('ENABLE_NOTIFICATIONS', 'true').lower() != 'true':
        print(f"🔕 Notificaciones desactivadas globalmente (.env). Omitiendo slug: {slug}")
        return {"status": "success", "message": "Notifications disabled globally"}

    try:
        config = SMTPConfig.query.first()
        template = NotificationTemplate.query.filter_by(slug=slug).first()
        if not config or not template:
            return {"status": "error", "message": "Missing SMTP config or Template"}

        # Prepare content
        body = template.body
        subject = template.subject
        if context:
            for key, val in context.items():
                body = body.replace(f"{{{key}}}", str(val))
                subject = subject.replace(f"{{{key}}}", str(val))

        msg = MIMEMultipart()
        msg['From'] = f"{config.sender_name} <{config.username}>"
        msg['To'] = target_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html' if template.is_html else 'plain'))

        # Connection
        if config.encryption == 'ssl':
            smtp = smtplib.SMTP_SSL(config.server, config.port, timeout=10)
        else:
            smtp = smtplib.SMTP(config.server, config.port, timeout=10)
            if config.encryption == 'starttls':
                smtp.starttls()

        import os
        if os.getenv('DEBUG_SMTP') == 'true':
            smtp.set_debuglevel(1)

        if config.auth_enabled and config.username and config.password:
            smtp.login(config.username, config.password)

        smtp.send_message(msg)
        smtp.quit()
        return {"status": "success", "message": f"Notificación '{slug}' enviada"}

    except Exception as e:
        return {"status": "error", "message": "Error interno enviando notificación."}
