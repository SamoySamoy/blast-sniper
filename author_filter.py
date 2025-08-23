import math
from urllib.parse import urlparse
from Scweet.scweet import Scweet
import re

def rate_profile(profile_url, env_path='.env', min_followers=2300, min_engagement=50, crypto_keyword_pct=0.3):
    """
    Calculate a shill score (1-10) for an X account's crypto shilling ability
    Requires .env file with EMAIL, EMAIL_PASSWORD, USERNAME, PASSWORD.
    Returns: (score: int, reason: str)
    """
    # Extract username from URL
    username = urlparse(profile_url).path.strip('/').split('/')[-1]
    
    try:
        # Initialize Scweet (headless for speed, disable images)
        scweet = Scweet(
            proxy=None,
            cookies_path='cookies',
            disable_images=True,
            env_path=env_path,
            concurrency=1,  # Single tab to minimize overhead
            headless=True,
            scroll_ratio=50  # Reduced scroll for faster tweet fetching
        )
        
        # 1. Get user info (followers, verified, description)
        user_info = scweet.get_user_information(handles=[username], login=True)
        if not user_info or username not in user_info:
            return 1, "Error fetching user info"
        
        user_data = user_info[username]
        followers = int(user_data.get('followers', '0').replace(',', ''))
        if followers < min_followers:
            return 1, f"Too few followers: {followers:,}"
        follower_score = min(10, max(1, math.log10(followers / 1000) * 5)) * 4  # Max 40 pts
        
        verified = 'verified' in user_data.get('description', '').lower() or user_data.get('verified', False)
        verified_score = 10 if verified else 0  # 10 pts if verified
        
        # 2. Get recent tweets for engagement and crypto relevance
        tweets = scweet.scrape(
            from_account=username,
            since="2025-08-01",  # Recent tweets (adjust for your timeframe)
            until="2025-08-24",
            limit=10,  # Enough for engagement/relevance
            lang="en",
            display_type="Latest",
            filter_replies=True,
            headless=True
        )
        
        # 3. Engagement score (30% weight)
        total_interactions = sum(
            (t.get('Likes', 0) + t.get('Retweets', 0) + t.get('Comments', 0))
            for t in tweets
        )
        avg_engagement = total_interactions / len(tweets) if tweets else 0
        if avg_engagement < min_engagement:
            return 2, f"Low engagement: {avg_engagement:.1f}"
        engagement_score = min(10, max(1, avg_engagement / 100)) * 3  # Max 30 pts
        
        # 4. Crypto relevance score (20% weight)
        crypto_keywords = ['token', 'pump', 'shill', 'meme coin', 'blast', 'solana', 'defi', 'nft', 'crypto', 'ethereum', 'btc', 'bitcoin', 'altcoin', 'airdrops', 'airdrops', 'whale', 'hodl', 'moon', 'luna', 'rug pull', 'sui']
        crypto_count = sum(1 for t in tweets if any(re.search(rf'\b{k}\b', t.get('Text', '').lower()) for k in crypto_keywords))
        crypto_pct = crypto_count / len(tweets) if tweets else 0
        if crypto_pct < crypto_keyword_pct:
            return 3, f"Not crypto-focused: {crypto_pct*100:.1f}%"
        crypto_score = min(10, max(1, crypto_pct * 12.5)) * 2  # Max 20 pts
        
        # Total score: Sum and normalize to 1-10
        raw_score = follower_score + verified_score + engagement_score + crypto_score
        normalized_score = max(1, min(10, round(raw_score / 10)))
        
        # Clean up
        scweet.driver.stop() if scweet.driver else None
        
        return normalized_score, f"Score details: Followers={followers:,} ({follower_score:.1f}/40), Verified={'Yes' if verified else 'No'} ({verified_score}/10), Avg Engagement={avg_engagement:.1f} ({engagement_score:.1f}/30), Crypto %={crypto_pct*100:.1f}% ({crypto_score:.1f}/20)"
    
    except Exception as e:
        return 1, f"Error: {str(e)}"