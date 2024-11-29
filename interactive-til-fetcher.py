import time
import re
import logging
import smtplib
import praw
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict

class TILFetcher:
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        """Initialize Reddit API connection with robust error handling"""
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Hardcoded email configuration
        self.sender_email = "debarshi.putatunda.its2me@gmail.com"
        self.sender_password = "kgxe mhae ejbk pbfb"  # Use Gmail App Password
        
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
                        'url': post.url,
                        'score': post.score
                    })
            
            return facts

        except Exception as e:
            self.logger.error(f"Error fetching facts: {e}")
            return []

    def send_email(self, facts: List[Dict[str, str]], recipient: str):
        """Send facts via email"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient
            msg['Subject'] = "Today's Interesting Facts"
            
            # Compose email body
            body = "Today's Interesting Facts:\n\n"
            for i, fact in enumerate(facts, 1):
                body += f"{i}. {fact['fact']}\n   Source: {fact['url']}\n\n"
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print("Email sent successfully!")
        
        except Exception as e:
            print(f"Email sending failed: {e}")

    def interactive_fact_management(self, facts: List[Dict[str, str]]):
        """Interactive management of fetched facts"""
        saved_facts = []
        
        for i, fact in enumerate(facts, 1):
            while True:
                print(f"\nFact {i}: {fact['fact']}")
                print("Options:")
                print("1. Save to file")
                print("2. Email")
                print("3. Skip")
                print("4. Exit")
                
                choice = input("Choose an action (1-4): ").strip()
                
                if choice == '1':
                    saved_facts.append(fact)
                    print("Fact saved.")
                    break
                elif choice == '2':
                    recipient = input("Enter recipient email: ")
                    self.send_email([fact], recipient)
                    break
                elif choice == '3':
                    break
                elif choice == '4':
                    return saved_facts
                else:
                    print("Invalid choice. Try again.")
        
        return saved_facts

    def save_facts(self, facts: List[Dict[str, str]], filename: str = 'til_facts.txt'):
        """Save facts to a numbered, ordered text file"""
        try:
            with open(filename, 'a', encoding='utf-8') as f:
                current_count = sum(1 for _ in open(filename)) + 1
                
                for fact in facts:
                    f.write(f"{current_count}. {fact['fact']} "
                            f"(Source: {fact['url']}, Score: {fact['score']})\n")
                    current_count += 1
            
            self.logger.info(f"Saved {len(facts)} facts to {filename}")
        
        except IOError as e:
            self.logger.error(f"File writing error: {e}")

def main():
    try:
        fetcher = TILFetcher(
            client_id='uWW-iJ0ZMeKrA3OFRYlF4Q',
            client_secret='Q0pTrzOhhkcHZpmp6E4Or5ZvtzR8rw',
            user_agent='Admirable_Science735'
        )

        while True:
            try:
                facts = fetcher.fetch_facts(limit=5)
                
                for fact in facts:
                    print(f"Fact: {fact['fact']}")
                    print(f"Source: {fact['url']}\n")
                
                # Interactive management
                saved = fetcher.interactive_fact_management(facts)
                
                # Optional: save saved facts to file
                if saved:
                    fetcher.save_facts(saved)
                
                time.sleep(30)  # Respect API rate limits
            
            except Exception as loop_error:
                fetcher.logger.error(f"Loop error: {loop_error}")
                time.sleep(30)  # Prevent tight error loops
    
    except Exception as init_error:
        logging.error(f"Initialization error: {init_error}")

if __name__ == "__main__":
    main()
