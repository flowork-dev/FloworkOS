########################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\app\yt_analytic\backend\logic\main_logic.py total lines 243 
##1. Dynamic Component Discovery (DCD): Hub wajib melakukan scanning file secara otomatis.
##2. Lazy Loading: Modul hanya di-import ke RAM saat dipanggil (On-Demand).
##3. Atomic Isolation: 1 File = 1 Fungsi dengan nama file yang identik dengan nama fungsi aslinya.
##4. Zero Logic Mutation: Dilarang merubah alur logika, nama variabel, atau struktur if/try/loop.
########################################################################

import re
from typing import Dict, Any, List, Optional
import googleapiclient.discovery
import googleapiclient.errors
from openai import OpenAI


    import sys, os
    try:
        global_lib_path = "/app/data/global_libs"
        if os.path.exists(global_lib_path):
            for lib_name in os.listdir(global_lib_path):
                lib_dir = os.path.join(global_lib_path, lib_name)
                if os.path.isdir(lib_dir):
                    for ver_hash in os.listdir(lib_dir):
                        sys.path.append(os.path.join(lib_dir, ver_hash))
    except: pass
    
def run(app_context, data, *args, **kwargs):
    """
    Main logic for Tube Insight (yt_analytic).
    Fetches YouTube video details and comments, then performs AI sentiment analysis.
    """
    url = data.get('url')
    if not url:
        return {
            "status": "error",
            "data": None,
            "message": "No URL provided in data."
        }
    
    video_id = extract_video_id(url)
    if not video_id:
        return {
            "status": "error",
            "data": None,
            "message": "Invalid YouTube URL. Could not extract Video ID."
        }
    
    variable_manager = app_context.get('variable_manager')
    if not variable_manager:
        return {
            "status": "error",
            "data": None,
            "message": "Could not access variable manager."
        }
    
    youtube_api_key = variable_manager.get_variable("YOUTUBE_API_KEY")
    openai_api_key = variable_manager.get_variable("OPENAI_API_KEY")
    
    if not youtube_api_key:
        return {
            "status": "error",
            "data": None,
            "message": "YouTube API Key not found. Please set 'YOUTUBE_API_KEY' variable."
        }
    if not openai_api_key:
        return {
            "status": "error",
            "data": None,
            "message": "OpenAI API Key not found. Please set 'OPENAI_API_KEY' variable."
        }
    
    try:
        video_details, top_comments = fetch_youtube_data(video_id, youtube_api_key)
    except Exception as e:
        return {
            "status": "error",
            "data": None,
            "message": f"YouTube API Error: {str(e)}"
        }
    
    if not video_details:
        return {
            "status": "error",
            "data": None,
            "message": "Could not fetch video details from YouTube API."
        }
    
    try:
        analysis_result = analyze_comments_with_ai(top_comments, openai_api_key)
    except Exception as e:
        return {
            "status": "error",
            "data": None,
            "message": f"AI Analysis Error: {str(e)}"
        }
    
    result_data = {
        "video_details": video_details,
        "comments": top_comments,
        "sentiment_analysis": analysis_result
    }
    
    return {
        "status": "success",
        "data": result_data,
        "message": "Video analysis completed successfully."
    }


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube Video ID from various URL formats.
    """
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([a-zA-Z0-9_-]{11})',
        r'(?:youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com\/v\/)([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def fetch_youtube_data(video_id: str, api_key: str) -> tuple:
    """
    Fetch video details and top comments using YouTube Data API v3.
    Returns (video_details_dict, list_of_comments).
    """
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)
    
    video_request = youtube.videos().list(
        part="snippet,statistics",
        id=video_id
    )
    video_response = video_request.execute()
    
    video_details = {}
    if video_response.get('items'):
        item = video_response['items'][0]
        snippet = item.get('snippet', {})
        stats = item.get('statistics', {})
        
        video_details = {
            "title": snippet.get('title', 'N/A'),
            "channel_title": snippet.get('channelTitle', 'N/A'),
            "published_at": snippet.get('publishedAt', 'N/A'),
            "description": snippet.get('description', '')[:200] + "..." if snippet.get('description') else '',
            "view_count": int(stats.get('viewCount', 0)),
            "like_count": int(stats.get('likeCount', 0)) if stats.get('likeCount') else 0,
            "comment_count": int(stats.get('commentCount', 0)) if stats.get('commentCount') else 0
        }
    
    comments = []
    try:
        comments_request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=10,
            order="relevance"
        )
        comments_response = comments_request.execute()
        
        for item in comments_response.get('items', []):
            snippet = item.get('snippet', {}).get('topLevelComment', {}).get('snippet', {})
            comment = {
                "author": snippet.get('authorDisplayName', 'Anonymous'),
                "text": snippet.get('textDisplay', ''),
                "like_count": snippet.get('likeCount', 0),
                "published_at": snippet.get('publishedAt', '')
            }
            comments.append(comment)
    except googleapiclient.errors.HttpError as e:
        if "commentsDisabled" in str(e):
            comments = [{"author": "System", "text": "Comments are disabled for this video.", "like_count": 0, "published_at": ""}]
        else:
            raise e
    
    return video_details, comments


def analyze_comments_with_ai(comments: List[Dict[str, Any]], openai_api_key: str) -> Dict[str, Any]:
    """
    Use OpenAI API to analyze sentiment and summarize viewer feedback.
    """
    if not comments:
        return {
            "overall_sentiment": "No comments available",
            "summary": "No comments to analyze.",
            "breakdown": {"positive": 0, "negative": 0, "neutral": 0}
        }
    
    comment_texts = [comment.get('text', '')[:500] for comment in comments[:10]]  # Limit to first 10 comments
    comments_blob = "\n---\n".join(comment_texts)
    
    client = OpenAI(api_key=openai_api_key)
    
    system_prompt = """You are a helpful assistant analyzing YouTube comments.
    Analyze the sentiment of the comments and provide:
    1. Overall sentiment (Positive/Negative/Neutral/Mixed).
    2. A concise summary (2-3 sentences) of what viewers are saying.
    3. Sentiment breakdown in percentages (positive, negative, neutral).
    
    Respond in this exact JSON format:
    {
        "overall_sentiment": "string",
        "summary": "string",
        "breakdown": {
            "positive": percentage,
            "negative": percentage,
            "neutral": percentage
        }
    }
    Ensure percentages add up to 100.
    """
    
    user_prompt = f"Analyze these YouTube comments:\n\n{comments_blob}"
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        ai_response_text = response.choices[0].message.content
        
        import json
        analysis_result = json.loads(ai_response_text)
        
        return analysis_result
        
    except Exception as e:
        return {
            "overall_sentiment": "Analysis Failed",
            "summary": f"Could not analyze comments due to error: {str(e)}",
            "breakdown": {"positive": 0, "negative": 0, "neutral": 0}
        }
