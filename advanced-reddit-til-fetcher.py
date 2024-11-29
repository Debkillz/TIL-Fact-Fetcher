import time
import re
import logging
import praw
from typing import List, Dict

class TILFetcher:
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        """
        Initialize Reddit API connection with robust error handling
        """
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)
        
        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            # Verify connection
            self.reddit.read_only = True
            self.reddit.subreddits.popular(limit=1)
        except Exception as e:
            self.logger.error(f"Reddit API Connection Failed: {e}")
            raise

    def clean_fact(self, title: str) -> str:
        """
        Advanced fact cleaning with comprehensive sanitization
        """
        # Remove TIL prefixes
        prefixes = [
            r'^TIL\s+', r'^TIL\s*that\s+', 
            r'^Today I Learned\s+', r'^Today I Learned\s*that\s+'
        ]
        for prefix in prefixes:
            title = re.sub(prefix, '', title, flags=re.IGNORECASE).strip()
        
        # Remove unnecessary whitespaces
        title = re.sub(r'\s+', ' ', title)
        
        # Capitalize first letter, ensure sentence ends with punctuation
        if title:
            title = title[0].upper() + title[1:]
            if not title.endswith(('.', '!', '?')):
                title += '.'
        
        return title

    def fetch_facts(self, subreddit_name: str = 'todayilearned', 
                    limit: int = 10) -> List[Dict[str, str]]:
        """
        Fetch and process new facts with comprehensive error handling
        """
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            facts = []

            for post in subreddit.new(limit=limit):
                # Skip potentially inappropriate or low-quality posts
                if (post.over_18 or len(post.title) > 300 or 
                    post.score < 10):  # Optional quality filter
                    continue
                
                cleaned_fact = self.clean_fact(post.title)
                
                if cleaned_fact:
                    facts.append({
                        'fact': cleaned_fact,
                        'url': post.url,
                        'score': post.score
                    })
            
            return facts

        except praw.exceptions.PRAWException as e:
            self.logger.error(f"Reddit API Error: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching facts: {e}")
            return []

    def save_facts(self, facts: List[Dict[str, str]], filename: str = 'til_facts.txt'):
        """
        Save facts to a numbered, ordered text file
        """
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
            client_id='YOUR_CLIENT_ID',
            client_secret='YOUR_CLIENT_SECRET',
            user_agent='AdvancedTILFetcher/1.0'
        )

        while True:
            try:
                facts = fetcher.fetch_facts()
                
                for fact in facts:
                    print(f"Fact: {fact['fact']}")
                    print(f"Source: {fact['url']}\n")
                
                fetcher.save_facts(facts)
                time.sleep(30)  # Respect API rate limits
            
            except Exception as loop_error:
                fetcher.logger.error(f"Loop error: {loop_error}")
                time.sleep(30)  # Prevent tight error loops
    
    except Exception as init_error:
        logging.error(f"Initialization error: {init_error}")

if __name__ == "__main__":
    main()
