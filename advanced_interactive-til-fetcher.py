import os
import time
import re
import logging
import smtplib
import praw
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Dict

class TILFetcher:
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        """Initialize Reddit API connection"""
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Hardcoded email configuration
        self.sender_email = "your_email@gmail.com"
        self.sender_password = "your_app_password"
        
        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            self.reddit.read_only = True
            self.reddit.subreddits.popular(limit=1)
        except Exception as e:
            self.logger.error(f"Reddit API Connection Failed: {e}")
            raise

    def clean_fact(self, title: str) -> str:
        """Advanced fact cleaning"""
        prefixes = [
            r'^TIL\s+', r'^TIL\s*that\s+', 
            r'^Today I Learned\s+', r'^Today I Learned\s*that\s+'
        ]
        for prefix in prefixes:
            title = re.sub(prefix, '', title, flags=re.IGNORECASE).strip()
        
        title = re.sub(r'\s+', ' ', title)
        
        if title:
            title = title[0].upper() + title[1:]
            if not title.endswith(('.', '!', '?')):
                title += '.'
        
        return title

    def fetch_facts(self, limit: int = 10) -> List[Dict[str, str]]:
        """Fetch and process new facts"""
        try:
            subreddit = self.reddit.subreddit('todayilearned')
            facts = []

            for post in subreddit.new(limit=limit):
                if (post.over_18 or len(post.title) > 300 or post.score < 10):
                    continue
                
                cleaned_fact = self.clean_fact(post.title)
                
                if cleaned_fact:
                    facts.append({
                        'fact': cleaned_fact,
                    })
            
            return facts

        except Exception as e:
            self.logger.error(f"Error fetching facts: {e}")
            return []

    def send_email(self, filename: str, recipient: str):
        """Send facts file via email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient
            msg['Subject'] = "Today's Interesting Facts"
            
            with open(filename, 'rb') as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(filename))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(filename)}"'
            msg.attach(part)
            
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print("Email sent successfully!")
        
        except Exception as e:
            print(f"Email sending failed: {e}")

    def generate_unique_filename(self, base_filename: str) -> str:
        """Generate a unique filename to avoid overwriting"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(script_dir, base_filename)
        
        if not os.path.exists(filename):
            return filename
        
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(f"{base}_{counter}{ext}"):
            counter += 1
        
        return f"{base}_{counter}{ext}"

    def save_facts(self, facts: List[Dict[str, str]]):
        """Save facts to a text file"""
        try:
            filename = self.generate_unique_filename('til_facts.txt')
            
            with open(filename, 'w', encoding='utf-8') as f:
                for i, fact in enumerate(facts, 1):
                    f.write(f"{i}. {fact['fact']}\n")
            
            print(f"Facts saved to {filename}")
            return filename
        
        except IOError as e:
            self.logger.error(f"File writing error: {e}")
            return None

    def interactive_fact_management(self, facts: List[Dict[str, str]]):
        """Interactive management of fetched facts"""
        while True:
            print("\nOptions:")
            print("1. Save facts to file")
            print("2. Email facts file")
            print("3. Exit")
            
            choice = input("Choose an action (1-3): ").strip()
            
            if choice == '1':
                filename = self.save_facts(facts)
                break
            elif choice == '2':
                filename = self.save_facts(facts)
                if filename:
                    recipient = input("Enter recipient email: ")
                    self.send_email(filename, recipient)
                break
            elif choice == '3':
                return False
            else:
                print("Invalid choice. Try again.")
        
        return True

def main():
    try:
        fetcher = TILFetcher(
            client_id='YOUR_CLIENT_ID',
            client_secret='YOUR_CLIENT_SECRET',
            user_agent='InteractiveTILFetcher/1.0'
        )

        while True:
            try:
                facts = fetcher.fetch_facts(limit=5)
                
                for fact in facts:
                    print(f"Fact: {fact['fact']}")
                
                # Interactive management
                continue_loop = fetcher.interactive_fact_management(facts)
                
                if not continue_loop:
                    break
                
                time.sleep(30)  # Respect API rate limits
            
            except Exception as loop_error:
                fetcher.logger.error(f"Loop error: {loop_error}")
                time.sleep(30)  # Prevent tight error loops
    
    except Exception as init_error:
        logging.error(f"Initialization error: {init_error}")

if __name__ == "__main__":
    main()
