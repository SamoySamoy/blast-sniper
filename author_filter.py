import requests
from bs4 import BeautifulSoup
import re
import math
from urllib.parse import urlparse
from typing import Tuple

def get_shill_score_beautifulsoup(profile_url: str, min_followers: int = 2300, min_engagement: float = 50, crypto_keyword_pct: float = 0.3, proxy: str = None) -> Tuple[int, str]:
    """
    Calculate a shill score (1-10) for an X account's crypto shilling ability using BeautifulSoup and requests.
    Optional proxy support. Returns: (score: int, reason: str)
    """
    # Extract username
    username = urlparse(profile_url).path.strip('/').split('/')[-1]
    
    # Headers to mimic browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    proxies = {"http": proxy, "https": proxy} if proxy else None
    
    try:
        response = requests.get(f"https://x.com/{username}", headers=headers, proxies=proxies, timeout=3)
        if response.status_code != 200:
            return 1, f"Error fetching page: HTTP {response.status_code}"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Followers score (40% weight)
        followers_link = soup.find('a', {'href': f'/{username}/followers'})
        followers_text = followers_link.text if followers_link else ""
        followers = 0
        match = re.search(r'(\d+(?:\.\d+)?[KMB]?) Followers', followers_text, re.I)
        if match:
            followers_str = match.group(1).replace('K', '000').replace('M', '000000').replace('B', '000000000').replace('.', '')
            followers = int(followers_str)
        if followers < min_followers:
            return 1, f"Too few followers: {followers:,}"
        follower_score = min(10, max(1, math.log10(followers / 1000) * 5)) * 4  # Max 40 pts
        
        # 2. Verified score (10% weight)
        verified = bool(soup.find(attrs={"aria-label": re.compile("Verified account", re.I)}) or
                        soup.find("svg", class_=re.compile("r-.*verified", re.I)))
        verified_score = 10 if verified else 0  # 10 pts if verified
        
        # 3. Engagement score (30% weight)
        tweets = []
        script_tags = soup.find_all("script")
        for script in script_tags:
            if script.string and '"Tweet"' in script.string:
                tweet_matches = re.findall(r'"text":"(.*?)".*?"retweet_count":(\d+).*?"like_count":(\d+).*?"reply_count":(\d+)', script.string)
                tweets = [{"text": t[0], "retweet_count": int(t[1]), "like_count": int(t[2]), "reply_count": int(t[3])} for t in tweet_matches[:10]]
                break
        
        total_interactions = sum(t["retweet_count"] + t["like_count"] + t["reply_count"] for t in tweets)
        avg_engagement = total_interactions / len(tweets) if tweets else 0
        if avg_engagement < min_engagement:
            return 2, f"Low engagement: {avg_engagement:.1f}"
        engagement_score = min(10, max(1, avg_engagement / 100)) * 3  # Max 30 pts
        
        # 4. Crypto relevance score (20% weight)
        crypto_keywords = ['token', 'pump', 'shill', 'meme coin', 'blast', 'solana', 'defi', 'nft', 'crypto']
        crypto_count = sum(1 for t in tweets if any(re.search(rf'\b{k}\b', t["text"].lower()) for k in crypto_keywords))
        crypto_pct = crypto_count / len(tweets) if tweets else 0
        if crypto_pct < crypto_keyword_pct:
            return 3, f"Not crypto-focused: {crypto_pct*100:.1f}%"
        crypto_score = min(10, max(1, crypto_pct * 12.5)) * 2  # Max 20 pts
        
        # Total score
        raw_score = follower_score + verified_score + engagement_score + crypto_score
        normalized_score = max(1, min(10, round(raw_score / 10)))
        
        return normalized_score, f"Score details: Followers={followers:,} ({follower_score:.1f}/40), Verified={'Yes' if verified else 'No'} ({verified_score}/10), Avg Engagement={avg_engagement:.1f} ({engagement_score:.1f}/30), Crypto %={crypto_pct*100:.1f}% ({crypto_score:.1f}/20)"
    
    except Exception as e:
        return 1, f"Error: {str(e)}"
