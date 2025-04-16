import tweepy
import configparser
import pandas as pd
import datetime
import time
import os
import json
import random

def load_config():
    config = configparser.ConfigParser(interpolation=None)
    config.read('config.ini')
    return config

def exponential_backoff(retry_count):
    wait_time = 2 ** retry_count * 30 + random.uniform(0, 5)
    return min(wait_time, 900)  # Cap at 15 minutes

def collect_tweets():
    # Load configuration
    config = load_config()
    bearer_token = config['twitter']['bearer_token']
    client = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=True)
    
    # List of influential AI/robotics accounts
    account_list = [
        # A sample list; add more as needed
        "sama", "gdb", "AndrewYNg", "drfeifei", "ylecun", "geoffreyhinton",
        "GaryMarcus", "lexfridman", "karpathy", "demishassabis"
    ]
    
    now = datetime.datetime.utcnow()
    time_threshold = now - datetime.timedelta(hours=12)
    print(f"Collecting tweets published since {time_threshold} UTC...")
    
    collected_tweets = []  # To hold tweet data
    os.makedirs("tweet_data", exist_ok=True)
    
    batch_size = 5
    for i in range(0, len(account_list), batch_size):
        batch = account_list[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(account_list) + batch_size - 1)//batch_size}")
        
        for username in batch:
            retry_count = 0
            max_retries = 5
            success = False
            
            while not success and retry_count < max_retries:
                try:
                    print(f"Looking up user: {username}")
                    user_response = client.get_user(username=username)
                    if user_response.data is None:
                        print(f"User '{username}' not found.")
                        success = True  # Skip if no data found
                        continue
                    
                    user_id = user_response.data.id
                    print(f"Getting tweets for: {username}")
                    tweets_response = client.get_users_tweets(
                        id=user_id,
                        max_results=10,
                        tweet_fields=["created_at", "public_metrics"],
                        exclude=["retweets", "replies"]
                    )
                    
                    if tweets_response.data is None:
                        print(f"No tweets found for user '{username}'.")
                        success = True
                        continue
                    
                    for tweet in tweets_response.data:
                        if tweet.created_at and tweet.created_at >= time_threshold:
                            metrics = tweet.public_metrics if hasattr(tweet, 'public_metrics') else {}
                            likes = metrics.get('like_count', 0)
                            retweets = metrics.get('retweet_count', 0)
                            
                            collected_tweets.append({
                                "username": username,
                                "text": tweet.text,
                                "created_at": tweet.created_at,
                                "likes": likes,
                                "retweets": retweets
                            })
                    success = True
                    
                except tweepy.TooManyRequests as e:
                    retry_count += 1
                    wait_time = exponential_backoff(retry_count)
                    print(f"Rate limit hit for '{username}'. Waiting {wait_time:.1f} seconds before retrying (attempt {retry_count}/{max_retries})...")
                    time.sleep(wait_time)
                except Exception as e:
                    print(f"Error retrieving tweets for '{username}': {e}")
                    success = True  # Skip account on other errors
            
            # Optional: a short delay between accounts to further ease the load
            time.sleep(2)
        # Delay between batches (increase this if necessary)
        print("Batch complete. Waiting 10 seconds before next batch...")
        time.sleep(10)
    
    if collected_tweets:
        df = pd.DataFrame(collected_tweets)
        # Optional: sort tweets by engagement or timestamp
        timestamp = now.strftime('%Y%m%d_%H%M%S')
        filename = f"tweet_data/tweets_{timestamp}.csv"
        df.to_csv(filename, index=False)
        print(f"Saved {len(df)} tweets to {filename}")
        return filename
    else:
        print("No new tweets found in the last 12 hours.")
        return None

def main():
    print("Starting Twitter AI/Robotics news collector...")
    result_file = collect_tweets()
    if result_file:
        print(f"Collection complete. Data saved to {result_file}")
    else:
        print("Collection complete but no tweets were found.")

if __name__ == "__main__":
    main()
