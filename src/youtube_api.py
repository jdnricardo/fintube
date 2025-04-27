from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Debug: Print the API key (first few characters only)
api_key = os.getenv('YOUTUBE_API_KEY')
if api_key:
    print(f"API key loaded: {api_key[:5]}...")
else:
    print("API key not found in environment variables")

class YouTubeAPI:
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        if not self.api_key:
            raise ValueError("YouTube API key not found in environment variables")
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)

    def get_channel_statistics(self, channel_id):
        """Fetch channel statistics."""
        try:
            print(f"Attempting to fetch statistics for channel: {channel_id}")
            request = self.youtube.channels().list(
                part="statistics,snippet",
                id=channel_id
            )
            print("API request created successfully")
            response = request.execute()
            print(f"API response received: {response}")
            if not response.get('items'):
                print(f"No items found in response for channel {channel_id}")
                return None
            return response['items'][0]
        except HttpError as e:
            print(f"An HTTP error occurred: {e}")
            print(f"Error details: {e.error_details if hasattr(e, 'error_details') else 'No details available'}")
            return None
        except Exception as e:
            print(f"Unexpected error occurred: {str(e)}")
            return None

    def get_video_statistics(self, video_id):
        """Fetch video statistics."""
        try:
            request = self.youtube.videos().list(
                part="statistics,snippet",
                id=video_id
            )
            response = request.execute()
            return response['items'][0] if response['items'] else None
        except HttpError as e:
            print(f"An HTTP error occurred: {e}")
            return None

    def search_videos(self, query, max_results=10):
        """Search for videos."""
        try:
            request = self.youtube.search().list(
                part="snippet",
                q=query,
                type="video",
                maxResults=max_results
            )
            response = request.execute()
            return response['items']
        except HttpError as e:
            print(f"An HTTP error occurred: {e}")
            return [] 