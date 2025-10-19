import asyncio
from scrape import Scraper
from utils import load_accounts_from_file
from decouple import config
from ast import literal_eval
from datetime import datetime, timedelta
import os
import csv


KEYWORDS=literal_eval(config("keyword"))


start_date = datetime(2023, 1, 12).date()
end_date = datetime(2025, 7, 4).date()

def setup_csv_file(filename):
    """Setup CSV file with headers"""
    headers = ["id", "username", "text", "date", "keyword", "scraped_at"]
    
    # Create file if it doesn't exist
    if not os.path.exists(filename):
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
    
    return headers

def save_tweet_to_csv(tweet_data, filename, headers):
    """Save single tweet to CSV file"""
    try:
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writerow(tweet_data)
        return True
    except Exception as e:
        print(f"[!] Error saving to CSV: {e}")
        return False

def generate_date_chunks(start_date, end_date, chunk_days=7):
    """Generate date chunks for processing"""
    chunks = []
    current = start_date
    delta = timedelta(days=chunk_days)
    
    while current < end_date:
        next_date = min(current + delta, end_date)
        chunks.append((current, next_date))
        current = next_date
    
    return chunks

async def run_scraper():
    scraper = Scraper()
    accounts = await load_accounts_from_file(scraper.api, "account_active.json")
    
    # Setup CSV file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"hasil_crawl/twitter_scraping_results_{timestamp}.csv"
    headers = setup_csv_file(csv_filename)
    
    print(f"[+] Using {len(accounts)} valid accounts")
    print(f"[+] Keywords to scrape: {KEYWORDS}")
    print(f"[+] Date range: {start_date} to {end_date}")
    print(f"[+] Results will be saved to: {csv_filename}")
    
    # Generate date chunks (7-day periods)
    date_chunks = generate_date_chunks(start_date, end_date, chunk_days=7)
    print(f"[+] Processing {len(date_chunks)} date chunks")
    
    total_tweets_scraped = 0
    
    for keyword in KEYWORDS:
        print(f"[+] Scraping keyword: {keyword}")
        keyword_tweet_count = 0
        
        for chunk_idx, (since_date, until_date) in enumerate(date_chunks, 1):
            # Format dates for query
            since = since_date.strftime("%Y-%m-%d")
            until = until_date.strftime("%Y-%m-%d")
            
            print(f"[>] Processing chunk {chunk_idx}/{len(date_chunks)}: {since} to {until}")
            
            try:
                # Build search query with date filter (same as your original)
                query = f"{keyword} since:{since} until:{until}"
                tweets = await scraper.search(query, limit=250)
                
                if not tweets:
                    print(f"[!] No tweets found for chunk: {since} to {until}")
                    continue
                
                print(f"[+] Found {len(tweets)} tweets for chunk: {since} to {until}")
                chunk_count = 0
                max_tweet_per_chunk=130
                
                for tweet in tweets:
                    if chunk_count >= max_tweet_per_chunk:
                        print(f"[!] Reached Maximum limit of {max_tweet_per_chunk} tweets for chunk:{since}to {until}")
                        break
                    try:
                        data = {
                            "id": tweet.id,
                            "username": tweet.user.username,
                            "text": tweet.rawContent.replace('\n', ' ').replace('\r', ' '),
                            "date": str(tweet.date),
                            "keyword": keyword,
                            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        if save_tweet_to_csv(data, csv_filename, headers):
                            keyword_tweet_count += 1
                            total_tweets_scraped += 1
                            chunk_count += 1
                            
                            if chunk_count % 50 == 0:  # Progress every 50 tweets
                                print(f"[+] Saved {chunk_count} tweets from current chunk")
                        
                        await asyncio.sleep(0.5)  # Respect rate limits
                        
                    except Exception as tweet_error:
                        print(f"[!] Error processing tweet: {tweet_error}")
                        continue
                
                print(f"[+] Completed chunk: {since} to {until} — {chunk_count} tweets saved")
                print(f"[+] Total for '{keyword}' so far: {keyword_tweet_count} tweets")
                
                # Small delay between chunks to avoid overwhelming the API
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"[!] Error scraping {keyword} from {since} to {until}: {e}")
                await asyncio.sleep(2)
        
        print(f"[✓] Completed keyword '{keyword}': {keyword_tweet_count} total tweets")
    
    print(f"[✓] Scraping completed!")
    print(f"[✓] Total tweets scraped: {total_tweets_scraped}")
    print(f"[✓] Results saved to: {csv_filename}")

if __name__ == "__main__":
    asyncio.run(run_scraper())