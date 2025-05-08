# from flask import Flask, jsonify, render_template
# import pandas as pd
# import pickle
# import os

# app = Flask(__name__)

# # Path to your pickle file
# MODEL_PATH = "google_sentiment_data.pkl"

# def load_data():
#     if os.path.exists(MODEL_PATH):
#         with open(MODEL_PATH, "rb") as f:
#             return pickle.load(f)
#     else:
#         return pd.DataFrame()

# @app.route('/')
# def home():
#     return render_template("show_dashboard.html")  # serve your HTML page

# @app.route('/dashboard')
# def dashboard():
#     df = load_data()
#     if df.empty:
#         return jsonify({"error": "No data found"}), 404

#     data = df[['date', 'text', 'sentiment', 'sentiment_category', 'engagement']].to_dict(orient='records')
#     return jsonify(data)

# if __name__ == '__main__':
#     app.run(debug=True)


# from fastapi import FastAPI, UploadFile, File, HTTPException
# from fastapi.responses import JSONResponse
# import pandas as pd
# import pickle
# import os
# import shutil

# app = FastAPI()

# UPLOAD_PATH = "uploaded_data.pkl"

# def load_data():
#     if os.path.exists(UPLOAD_PATH):
#         with open(UPLOAD_PATH, "rb") as f:
#             return pickle.load(f)
#     return pd.DataFrame()

# @app.post("/upload")
# async def upload_file(file: UploadFile = File(...)):
#     if not file.filename.endswith(".pkl"):
#         raise HTTPException(status_code=400, detail="Only .pkl files are allowed")
#     with open(UPLOAD_PATH, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)
#     return {"message": "File uploaded successfully"}

# @app.get("/dashboard")
# def get_dashboard_data():
#     df = load_data()
#     if df.empty:
#         raise HTTPException(status_code=404, detail="No data found")

#     df['date'] = df['date'].astype(str)
#     data = df[['date', 'text', 'sentiment', 'sentiment_category', 'engagement']].to_dict(orient="records")
#     return JSONResponse(content=data)



from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pandas as pd
import asyncpraw
import shutil
import os
import nltk
nltk.download('vader_lexicon')
# Initialize app and sentiment analyzer
app = FastAPI()
sia = SentimentIntensityAnalyzer()

# File path for upload
UPLOAD_PATH = "uploaded_data.pkl"

# Reddit API credentials
REDDIT_CREDS = {
    "client_id": "MKA7SfSGP23Oz2N1z7DK2A",
    "client_secret": "foWrfB9bhJd-WBK3g5Ag6J_uXpbZpg",
    "user_agent": "Athaxv"
}

# Upload .pkl file
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".pkl"):
        raise HTTPException(status_code=400, detail="Only .pkl files are allowed")
    with open(UPLOAD_PATH, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": "File uploaded successfully"}

# Load uploaded data
def load_data():
    if os.path.exists(UPLOAD_PATH):
        try:
            with open(UPLOAD_PATH, "rb") as f:
                return pd.read_pickle(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading file: {str(e)}")
    return pd.DataFrame()

# Dashboard data from uploaded file
@app.get("/dashboard")
def get_dashboard_data():
    df = load_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="No data found")

    required_columns = {'date', 'text', 'sentiment', 'sentiment_category', 'engagement'}
    if not required_columns.issubset(df.columns):
        raise HTTPException(status_code=400, detail="Missing required columns in data")

    df['date'] = df['date'].astype(str)
    data = df[['date', 'text', 'sentiment', 'sentiment_category', 'engagement']].to_dict(orient="records")
    return JSONResponse(content=data)

# Truncate long text for readability
def truncate_text(text, length=200):
    text = text.replace('\n', ' ').strip()
    return (text[:length] + '...') if len(text) > length else text

# Perform sentiment analysis
def enhanced_sentiment_analysis(df):
    df['sentiment'] = df['text'].apply(lambda x: sia.polarity_scores(str(x))['compound'])
    bins = [-1, -0.5, -0.1, 0.1, 0.5, 1]
    labels = ['strong_negative', 'negative', 'neutral', 'positive', 'strong_positive']
    df['sentiment_category'] = pd.cut(df['sentiment'], bins=bins, labels=labels)
    return df

# Find relevant subreddits
async def find_relevant_subreddits(company_name):
    reddit = asyncpraw.Reddit(**REDDIT_CREDS)
    business_subs = ['SmallBusiness', 'Entrepreneur', 'Startups', 'Business', 'Marketing', 'Sales']
    company_subs = []
    count = 0
    async for sub in reddit.subreddits.search_by_name(company_name):
        company_subs.append(sub.display_name)
        count += 1
        if count >= 5:
            break
    await reddit.close()
    combined_subs = list(set(business_subs + company_subs))
    return combined_subs[:10]

# Fetch Reddit data
# async def fetch_reddit_data(company_name):
#     reddit = asyncpraw.Reddit(**REDDIT_CREDS)
#     subreddits = await find_relevant_subreddits(company_name)
#     print(f"Searching in subreddits: {', '.join(subreddits)}")

#     data = []
#     for subreddit_name in subreddits:
#         try:
#             subreddit = await reddit.subreddit(subreddit_name)
#             async for submission in subreddit.search(company_name, limit=100):
#                 await submission.load()
#                 data.append({
#                     'company_name': company_name,
#                     'subreddit': subreddit_name,
#                     'date': datetime.fromtimestamp(submission.created_utc),
#                     'text': f"{submission.title} {submission.selftext}",
#                     'engagement': submission.score,
#                     'type': 'submission',
#                     'url': submission.url
#                 })
#                 await submission.comments.replace_more(limit=0)
#                 async for comment in submission.comments:
#                     data.append({
#                         'company_name': company_name,
#                         'subreddit': subreddit_name,
#                         'date': datetime.fromtimestamp(comment.created_utc),
#                         'text': comment.body,
#                         'engagement': comment.score,
#                         'type': 'comment',
#                         'url': submission.url
#                     })
#         except Exception as e:
#             print(f"Error with subreddit {subreddit_name}: {e}")
#             continue
#     await reddit.close()
#     df = pd.DataFrame(data)
#     if not df.empty:
#         df['date'] = pd.to_datetime(df['date'])
#     return df

async def fetch_reddit_data(company_name):
    reddit = asyncpraw.Reddit(**REDDIT_CREDS)
    subreddits = await find_relevant_subreddits(company_name)
    print(f"Searching in subreddits: {', '.join(subreddits)}")

    data = []
    submission_count = 0
    max_submissions = 30  # Limit total submissions across all subreddits

    for subreddit_name in subreddits:
        try:
            subreddit = await reddit.subreddit(subreddit_name)
            async for submission in subreddit.search(company_name, limit=10, sort="top"):
                if submission_count >= max_submissions:
                    break

                await submission.load()
                data.append({
                    'company_name': company_name,
                    'subreddit': subreddit_name,
                    'date': datetime.fromtimestamp(submission.created_utc),
                    'text': f"{submission.title} {submission.selftext}",
                    'engagement': submission.score,
                    'type': 'submission',
                    'url': submission.url
                })
                submission_count += 1

                # Top-level comments only, limit to 3 per post
                await submission.comments.replace_more(limit=0)
                top_comments = sorted(submission.comments, key=lambda x: x.score if hasattr(x, 'score') else 0, reverse=True)[:3]
                for comment in top_comments:
                    data.append({
                        'company_name': company_name,
                        'subreddit': subreddit_name,
                        'date': datetime.fromtimestamp(comment.created_utc),
                        'text': comment.body,
                        'engagement': comment.score,
                        'type': 'comment',
                        'url': submission.url
                    })
        except Exception as e:
            print(f"Error with subreddit {subreddit_name}: {e}")
            continue

        if submission_count >= max_submissions:
            break

    await reddit.close()
    df = pd.DataFrame(data)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df


# Main analysis endpoint
@app.get("/analyze/{company_name}")
async def analyze_company(company_name: str):
    try:
        df = await fetch_reddit_data(company_name)
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found for the given company")

        df = enhanced_sentiment_analysis(df)
        df['date'] = df['date'].astype(str)
        df['text'] = df['text'].apply(truncate_text)

        records = df[['date', 'text', 'sentiment', 'sentiment_category', 'engagement', 'type', 'url']].to_dict(orient="records")
        return JSONResponse(content={"company": company_name, "data": records})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
