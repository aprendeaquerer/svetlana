#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email configuration and sending functionality
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging

# Email configuration
EMAIL_CONFIG = {
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "smtp_username": os.getenv("SMTP_USERNAME"),
    "smtp_password": os.getenv("SMTP_PASSWORD"),
    "from_email": os.getenv("FROM_EMAIL", "noreply@eldric.com"),
    "from_name": os.getenv("FROM_NAME", "Eldric - Tu Coach Emocional")
}

def get_email_config():
    """Get email configuration from environment variables"""
    return EMAIL_CONFIG

def send_verification_email(to_email: str, verification_code: str, language: str = "es") -> bool:
    """
    Send verification code email
    """
    try:
        config = get_email_config()
        
        if not config["smtp_username"] or not config["smtp_password"]:
            print(f"[DEBUG] Email credentials not configured. Code for {to_email}: {verification_code}")
            return True  # Return True for development
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{config['from_name']} <{config['from_email']}>"
        msg['To'] = to_email
        msg['Subject'] = "Código de verificación - Eldric" if language == "es" else "Verification Code - Eldric"
        
        # Email body
        if language == "es":
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50;">¡Hola! 👋</h2>
                    
                    <p>Gracias por registrarte en <strong>Eldric</strong>, tu coach emocional personal.</p>
                    
                    <p>Para completar tu registro y acceder a todas las funciones, por favor verifica tu dirección de email usando el siguiente código:</p>
                    
                    <div style="background-color: #f8f9fa; border: 2px solid #e9ecef; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                        <h1 style="color: #2c3e50; font-size: 32px; margin: 0; letter-spacing: 4px;">{verification_code}</h1>
                    </div>
                    
                    <p><strong>Este código expira en 15 minutos.</strong></p>
                    
                    <p>Si no solicitaste este código, puedes ignorar este email.</p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="font-size: 14px; color: #666;">
                        Con cariño,<br>
                        El equipo de Eldric
                    </p>
                </div>
            </body>
            </html>
            """
        else:  # English
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50;">Hello! 👋</h2>
                    
                    <p>Thank you for signing up with <strong>Eldric</strong>, your personal emotional coach.</p>
                    
                    <p>To complete your registration and access all features, please verify your email address using the following code:</p>
                    
                    <div style="background-color: #f8f9fa; border: 2px solid #e9ecef; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                        <h1 style="color: #2c3e50; font-size: 32px; margin: 0; letter-spacing: 4px;">{verification_code}</h1>
                    </div>
                    
                    <p><strong>This code expires in 15 minutes.</strong></p>
                    
                    <p>If you didn't request this code, you can ignore this email.</p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="font-size: 14px; color: #666;">
                        With care,<br>
                        The Eldric Team
                    </p>
                </div>
            </body>
            </html>
            """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        if config["smtp_port"] == 465:
            # Use SSL for port 465 (Zoho alternative)
            server = smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"])
        else:
            # Use STARTTLS for port 587 (standard)
            server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
            server.starttls()
        
        server.login(config["smtp_username"], config["smtp_password"])
        text = msg.as_string()
        server.sendmail(config["from_email"], to_email, text)
        server.quit()
        
        print(f"[DEBUG] Verification email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to send verification email to {to_email}: {e}")
        return False

def send_pdf_email(to_email: str, pdf_path: str, user_name: str = None, language: str = "es") -> bool:
    """
    Send PDF report email
    """
    try:
        config = get_email_config()
        
        if not config["smtp_username"] or not config["smtp_password"]:
            print(f"[DEBUG] Email credentials not configured. PDF would be sent to {to_email}")
            return True  # Return True for development
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{config['from_name']} <{config['from_email']}>"
        msg['To'] = to_email
        
        if language == "es":
            msg['Subject'] = f"Tu reporte personalizado - Eldric{f' ({user_name})' if user_name else ''}"
        else:
            msg['Subject'] = f"Your personalized report - Eldric{f' ({user_name})' if user_name else ''}"
        
        # Email body
        if language == "es":
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50;">¡Tu reporte está listo! 📊</h2>
                    
                    <p>Hola{f' {user_name}' if user_name else ''},</p>
                    
                    <p>Como prometí, aquí tienes tu reporte personalizado con los resultados de tu test de estilos de apego y análisis de relación.</p>
                    
                    <p>Este reporte incluye:</p>
                    <ul>
                        <li>📋 Análisis detallado de tu estilo de apego</li>
                        <li>💑 Dinámicas de tu relación (si completaste el test de pareja)</li>
                        <li>💡 Consejos prácticos para mejorar tus relaciones</li>
                        <li>🎯 Pasos específicos para tu crecimiento personal</li>
                    </ul>
                    
                    <p>Puedes guardarlo, imprimirlo o compartirlo con tu pareja si lo deseas.</p>
                    
                    <p>Recuerda que estoy aquí para seguir apoyándote en tu viaje de crecimiento personal. ¡No dudes en contactarme cuando necesites!</p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="font-size: 14px; color: #666;">
                        Con cariño,<br>
                        Eldric - Tu Coach Emocional
                    </p>
                </div>
            </body>
            </html>
            """
        else:  # English
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50;">Your report is ready! 📊</h2>
                    
                    <p>Hello{f' {user_name}' if user_name else ''},</p>
                    
                    <p>As promised, here's your personalized report with your attachment style test results and relationship analysis.</p>
                    
                    <p>This report includes:</p>
                    <ul>
                        <li>📋 Detailed analysis of your attachment style</li>
                        <li>💑 Your relationship dynamics (if you completed the partner test)</li>
                        <li>💡 Practical tips to improve your relationships</li>
                        <li>🎯 Specific steps for your personal growth</li>
                    </ul>
                    
                    <p>You can save it, print it, or share it with your partner if you'd like.</p>
                    
                    <p>Remember that I'm here to continue supporting you on your personal growth journey. Don't hesitate to reach out when you need me!</p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="font-size: 14px; color: #666;">
                        With care,<br>
                        Eldric - Your Emotional Coach
                    </p>
                </div>
            </body>
            </html>
            """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Attach PDF if it exists
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(pdf_path)}'
                )
                msg.attach(part)
        
        # Send email
        if config["smtp_port"] == 465:
            # Use SSL for port 465 (Zoho alternative)
            server = smtplib.SMTP_SSL(config["smtp_server"], config["smtp_port"])
        else:
            # Use STARTTLS for port 587 (standard)
            server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
            server.starttls()
        
        server.login(config["smtp_username"], config["smtp_password"])
        text = msg.as_string()
        server.sendmail(config["from_email"], to_email, text)
        server.quit()
        
        print(f"[DEBUG] PDF email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to send PDF email to {to_email}: {e}")
        return False
