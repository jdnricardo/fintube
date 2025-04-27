import duckdb
import pandas as pd
from pathlib import Path
import ast
import json

class DataProcessor:
    def __init__(self, db_path="data/youtube_stats.duckdb"):
        """Initialize the data processor with DuckDB connection."""
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(db_path)
        self._create_tables()
        self._load_metadata_from_csv()  # Load metadata from CSV on initialization

    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS video_stats (
                video_id VARCHAR,
                title VARCHAR,
                channel_id VARCHAR,
                view_count INTEGER,
                like_count INTEGER,
                comment_count INTEGER,
                published_at TIMESTAMP,
                duration_seconds INTEGER,
                like_ratio DOUBLE,
                comment_ratio DOUBLE,
                engagement_score DOUBLE,
                video_age_days INTEGER,
                views_per_day DOUBLE,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS channel_stats (
                channel_id VARCHAR,
                title VARCHAR,
                subscriber_count INTEGER,
                video_count INTEGER,
                view_count INTEGER,
                published_at TIMESTAMP,
                avg_views_per_video DOUBLE,
                subscriber_view_ratio DOUBLE,
                channel_age_days INTEGER,
                videos_per_month DOUBLE,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS channel_metadata (
                channel_id VARCHAR PRIMARY KEY,
                title VARCHAR,
                description TEXT,
                firm_type VARCHAR CHECK (firm_type IN ('wealth management', 'etf management', 'data & analytics', 'investor research', 'podcast')),
                target_audience JSON,  -- Will store array of ['institutional', 'accredited', 'general']
                content_type VARCHAR CHECK (content_type IN ('long-form', 'short-form', 'both')),
                has_legacy_media BOOLEAN,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def _load_metadata_from_csv(self, csv_path="data/channel_metadata.csv"):
        """Load channel metadata from CSV file."""
        try:
            # Read CSV file (comma-separated)
            df = pd.read_csv(csv_path)
            
            # Drop rows with missing channel_id
            df = df.dropna(subset=['channel_id']).reset_index(drop=True)
            
            # Convert target_audience from string representation to JSON array
            df['target_audience'] = df['target_audience'].apply(
                lambda x: json.loads(x) if isinstance(x, str) and x.startswith('[') else ([x] if x and x != 'None' else [])
            )
            
            # Convert has_legacy_media to boolean
            df['has_legacy_media'] = df['has_legacy_media'].astype(bool)
            
            print("Loaded channel_metadata.csv DataFrame:")
            print(df)
            
            # Insert or update metadata for each channel
            for _, row in df.iterrows():
                print(f"Inserting row: {row.to_dict()}")  # Debug print
                self.store_channel_metadata(row['channel_id'], {
                    'title': row.get('title', ''),  # Use empty string if title not in CSV
                    'firm_type': row['firm_type'],
                    'target_audience': row['target_audience'],
                    'content_type': row['content_type'],
                    'has_legacy_media': row['has_legacy_media']
                })
            
            print(f"Successfully loaded metadata from {csv_path}")
        except Exception as e:
            print(f"Error loading metadata from CSV: {str(e)}")

    def store_video_stats(self, video_data):
        """Store video statistics in DuckDB."""
        if not video_data:
            return

        df = pd.DataFrame([{
            'video_id': video_data['id'],
            'title': video_data['snippet']['title'],
            'channel_id': video_data['snippet']['channelId'],
            'view_count': int(video_data['statistics'].get('viewCount', 0)),
            'like_count': int(video_data['statistics'].get('likeCount', 0)),
            'comment_count': int(video_data['statistics'].get('commentCount', 0)),
            'published_at': video_data['snippet']['publishedAt']
        }])

        self.conn.execute("""
            INSERT INTO video_stats 
            SELECT * FROM df
        """)

    def store_channel_stats(self, channel_data):
        """Store channel statistics in DuckDB."""
        if not channel_data:
            return

        df = pd.DataFrame([{
            'channel_id': channel_data['id'],
            'title': channel_data['snippet']['title'],
            'subscriber_count': int(channel_data['statistics'].get('subscriberCount', 0)),
            'video_count': int(channel_data['statistics'].get('videoCount', 0)),
            'view_count': int(channel_data['statistics'].get('viewCount', 0)),
            'published_at': channel_data['snippet']['publishedAt']
        }])

        # Insert data and calculate views_per_video in SQL
        self.conn.execute("""
            INSERT INTO channel_stats (channel_id, title, subscriber_count, video_count, view_count, published_at, avg_views_per_video, subscriber_view_ratio, channel_age_days, videos_per_month)
            SELECT 
                channel_id, 
                title, 
                subscriber_count, 
                video_count, 
                view_count,
                CAST(published_at AS TIMESTAMP),
                CASE 
                    WHEN video_count > 0 THEN view_count / video_count 
                    ELSE 0 
                END AS avg_views_per_video,
                CASE 
                    WHEN view_count > 0 THEN subscriber_count / view_count 
                    ELSE 0 
                END AS subscriber_view_ratio,
                datediff('day', CAST(published_at AS TIMESTAMP), current_timestamp) AS channel_age_days,
                video_count / (datediff('day', CAST(published_at AS TIMESTAMP), current_timestamp) / 30.44) AS videos_per_month
            FROM df
        """)

    def store_channel_metadata(self, channel_id, metadata):
        """Store or update channel metadata."""
        self.conn.execute("""
            INSERT INTO channel_metadata (
                channel_id, title, description, firm_type, target_audience,
                content_type, has_legacy_media
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (channel_id) DO UPDATE SET
                title = excluded.title,
                description = excluded.description,
                firm_type = excluded.firm_type,
                target_audience = excluded.target_audience,
                content_type = excluded.content_type,
                has_legacy_media = excluded.has_legacy_media
        """, [
            channel_id,
            metadata.get('title'),
            metadata.get('description'),
            metadata.get('firm_type'),
            metadata.get('target_audience'),
            metadata.get('content_type'),
            metadata.get('has_legacy_media')
        ])

    def get_video_stats(self, limit=10):
        """Retrieve video statistics."""
        return self.conn.execute("""
            SELECT * FROM video_stats 
            ORDER BY fetched_at DESC 
            LIMIT ?
        """, [limit]).fetchdf()

    def get_channel_stats(self, limit=10):
        """Retrieve channel statistics."""
        return self.conn.execute("""
            SELECT * FROM channel_stats 
            ORDER BY fetched_at DESC 
            LIMIT ?
        """, [limit]).fetchdf()

    def get_channel_metadata(self, channel_id=None):
        """Retrieve channel metadata."""
        if channel_id:
            return self.conn.execute("""
                SELECT * FROM channel_metadata 
                WHERE channel_id = ?
            """, [channel_id]).fetchdf()
        return self.conn.execute("""
            SELECT * FROM channel_metadata
        """).fetchdf()

    def get_channel_comparison(self, channel_ids=None):
        """Get a combined view of channel stats and metadata."""
        query = """
            SELECT 
                cs.*,
                cm.firm_type,
                cm.target_audience,
                cm.content_type,
                cm.has_legacy_media
            FROM channel_stats cs
            LEFT JOIN channel_metadata cm ON cs.channel_id = cm.channel_id
        """
        
        if channel_ids:
            channel_ids_str = "','".join(channel_ids)
            query += f" WHERE cs.channel_id IN ('{channel_ids_str}')"
        
        result = self.conn.execute(query).fetchdf()
        if result.empty:
            print("Warning: Query returned empty dataframe")
        return result

    def close(self):
        """Close the DuckDB connection."""
        self.conn.close()

    def remove_channels(self, channel_ids):
        """Remove specified channels from the database."""
        if not channel_ids:
            return
        
        # Convert list to string for SQL IN clause
        channel_ids_str = "','".join(channel_ids)
        self.conn.execute(f"""
            DELETE FROM channel_stats 
            WHERE channel_id IN ('{channel_ids_str}')
        """)

    def calculate_derived_metrics(self):
        """Calculate derived metrics for video_stats."""
        self.conn.execute("""
            SELECT
                *,
                CASE WHEN view_count > 0 THEN like_count * 1.0 / view_count ELSE NULL END AS like_ratio,
                CASE WHEN view_count > 0 THEN comment_count * 1.0 / view_count ELSE NULL END AS comment_ratio,
                (like_count + comment_count) * 1.0 / NULLIF(view_count, 0) AS engagement_score,
                datediff('day', published_at, current_date) AS video_age_days,
                view_count * 1.0 / NULLIF(datediff('day', published_at, current_date), 0) AS views_per_day
            FROM video_stats
        """) 