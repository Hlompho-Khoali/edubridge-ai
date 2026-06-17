# utils/email.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    """Email notification service"""
    
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    FROM_EMAIL = os.getenv('FROM_EMAIL', SMTP_USER)
    
    @staticmethod
    def send_email(to_email, subject, body, html_body=None):
        """Send an email"""
        if not EmailService.SMTP_USER:
            print("Email not configured. Skipping send.")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = EmailService.FROM_EMAIL
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Plain text version
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # HTML version if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(EmailService.SMTP_HOST, EmailService.SMTP_PORT)
            server.starttls()
            server.login(EmailService.SMTP_USER, EmailService.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            print(f"Email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"Email error: {e}")
            return False
    
    @staticmethod
    def send_game_completion_email(learner, game, score, passed):
        """Send email when learner completes a game"""
        subject = f"🎮 {learner.user.name} completed a game!"
        
        body = f"""
        Hello,
        
        {learner.user.name} just completed the game "{game.name}"!
        
        Results:
        - Score: {score}%
        - Status: {'✅ Passed' if passed else '❌ Needs Practice'}
        
        Check the dashboard for more details.
        
        Best regards,
        EduBridge Team
        """
        
        html_body = f"""
        <h2>🎮 Game Completed!</h2>
        <p><strong>{learner.user.name}</strong> just completed the game <strong>"{game.name}"</strong>!</p>
        
        <h3>Results:</h3>
        <ul>
            <li><strong>Score:</strong> {score}%</li>
            <li><strong>Status:</strong> {'✅ Passed' if passed else '❌ Needs Practice'}</li>
        </ul>
        
        <p><a href="https://edubridge.com/dashboard">View Dashboard</a></p>
        
        <p>Best regards,<br>EduBridge Team</p>
        """
        
        # Get parent email
        if learner.parent:
            parent_email = learner.parent.user.email
            return EmailService.send_email(parent_email, subject, body, html_body)
        
        return False
    
    @staticmethod
    def send_progress_report_email(parent, learner, progress_data):
        """Send weekly progress report email"""
        subject = f"📊 Weekly Progress Report for {learner.user.name}"
        
        body = f"""
        Hello {parent.user.name},
        
        Here's your child's weekly progress report:
        
        {progress_data}
        
        Best regards,
        EduBridge Team
        """
        
        return EmailService.send_email(parent.user.email, subject, body)