from flask import Blueprint, render_template, request, redirect, url_for, flash
import os
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

about_bp = Blueprint('about', __name__)

@about_bp.route('/about')
def about():
    """About page with system information"""
    return render_template('about/index.html')

@about_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form page"""
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        # Validate form data
        if not all([name, email, subject, message]):
            flash('All fields are required.', 'error')
            return render_template('about/contact.html')
        
        # Try to send email if SMTP is configured
        if send_contact_email(name, email, subject, message):
            flash('Thank you for your message! We will get back to you soon.', 'success')
            return redirect(url_for('about.contact'))
        else:
            flash('Message received! We will respond as soon as possible.', 'info')
            # In a real application, you would save to database here
            return redirect(url_for('about.contact'))
    
    return render_template('about/contact.html')

def send_contact_email(name, email, subject, message):
    """Send contact form email if SMTP is configured"""
    try:
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@potholes.local')
        
        if not all([smtp_server, smtp_username, smtp_password]):
            return False
        
        # Create message
        msg = MimeMultipart()
        msg['From'] = smtp_username
        msg['To'] = admin_email
        msg['Subject'] = f"POTHOLES Contact Form: {subject}"
        
        body = f"""
        New contact form submission:
        
        Name: {name}
        Email: {email}
        Subject: {subject}
        
        Message:
        {message}
        
        ---
        Sent from POTHOLES Contact Form
        """
        
        msg.attach(MimeText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        return True
        
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False
