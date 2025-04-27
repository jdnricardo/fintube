import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path
from auth import check_password

if not check_password():
    st.stop()

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from youtube_api import YouTubeAPI
from data_processor import DataProcessor
from market_data import MarketData
import plotly.express as px
import time

# Default channels for comparison
DEFAULT_CHANNELS = [
    "UCYmQgh9tvqhgEcVvI63l10A",  # Example channel
    "UCTNgTBKATr18Z7kR32rKOBw",
    "UCQxFhbPxp6VtAMGEF8OWG5g",
    "UCBRpqrzuuqE8TZcWw75JSdw",
    "UCRJplQ4Ynuph20iIzFP5tww"
]

# Initialize API and data processor
@st.cache_resource(ttl=0)  # Set TTL to 0 to disable caching
def init_resources():
    st.write("Initializing resources...")
    return YouTubeAPI(), DataProcessor(), MarketData()

youtube_api, data_processor, market_data = init_resources()

# Initialize session state for tracking channels
if 'current_channels' not in st.session_state:
    st.session_state.current_channels = set(DEFAULT_CHANNELS)

# After initializing session state
for channel_id in st.session_state.current_channels:
    if data_processor.get_channel_comparison([channel_id]).empty:
        with st.spinner(f"Fetching stats for channel: {channel_id}"):
            channel_stats = youtube_api.get_channel_statistics(channel_id)
            if channel_stats:
                data_processor.store_channel_stats(channel_stats)
                data_processor.store_channel_metadata(channel_id, {
                    'title': channel_stats['snippet']['title'],
                    'description': channel_stats['snippet'].get('description', ''),
                    'firm_type': None,  # Will be set by user
                    'target_audience': [],  # Will be set by user
                    'content_type': None,  # Will be set by user
                    'has_legacy_media': False  # Will be set by user
                })
            else:
                st.error(f"Failed to retrieve statistics for channel {channel_id}")
            time.sleep(1)

st.title("YouTube Channel Analytics")

# Sidebar for channel input
st.sidebar.header("Channel Analysis")
channel_ids = st.sidebar.text_area(
    "Enter Channel IDs (one per line)",
    value="\n".join(DEFAULT_CHANNELS),
    help="Enter YouTube channel IDs, one per line. You can find a channel ID in the channel URL."
)

# Process channel IDs
new_channels = set(channel_id.strip() for channel_id in channel_ids.split('\n') if channel_id.strip())
channels_to_add = new_channels - st.session_state.current_channels
channels_to_remove = st.session_state.current_channels - new_channels

if channels_to_add or channels_to_remove:
    with st.spinner("Updating channel statistics..."):
        # Remove channels that are no longer in the list
        if channels_to_remove:
            st.write(f"Removing channels: {channels_to_remove}")
            data_processor.remove_channels(list(channels_to_remove))
        
        # Add new channels
        for channel_id in channels_to_add:
            st.write(f"Processing channel: {channel_id}")
            channel_stats = youtube_api.get_channel_statistics(channel_id)
            st.write(f"Channel stats response: {channel_stats}")
            if channel_stats:
                st.write("Storing channel statistics...")
                data_processor.store_channel_stats(channel_stats)
                # Initialize empty metadata for new channels
                st.write("Storing channel metadata...")
                data_processor.store_channel_metadata(channel_id, {
                    'title': channel_stats['snippet']['title'],
                    'description': channel_stats['snippet'].get('description', ''),
                    'firm_type': None,  # Will be set by user
                    'target_audience': [],  # Will be set by user
                    'content_type': None,  # Will be set by user
                    'has_legacy_media': False  # Will be set by user
                })
            else:
                st.error(f"Failed to retrieve statistics for channel {channel_id}")
        
        # Update the current channels set
        st.session_state.current_channels = new_channels
        st.success("Channel data updated!")

# Display channel statistics
st.header("Channel Statistics")
channel_stats_df = data_processor.get_channel_comparison(list(st.session_state.current_channels))

if not channel_stats_df.empty:
    # Create a comparison view
    st.subheader("Channel Comparison")
    
    # Select metrics to compare
    metrics = [
        "subscriber_count",
        "view_count",
        "video_count",
        "channel_age_days",
        "avg_views_per_video",
        "subscriber_view_ratio",
        "videos_per_month"
    ]
    
    selected_metrics = st.multiselect(
        "Select metrics to compare",
        metrics,
        default=["subscriber_count", 
                 "subscriber_view_ratio", 
                 "videos_per_month", 
                 "avg_views_per_video"]
    )
    
    if selected_metrics:
        # Prepare data for comparison
        comparison_df = channel_stats_df[["channel_id", "title"] + selected_metrics].copy()
        
        # Create bar charts for each selected metric
        for metric in selected_metrics:
            # Prepare the dataframe
            sorted_df = comparison_df[["title", metric]].copy()
            sorted_df[metric] = pd.to_numeric(sorted_df[metric], errors='coerce')  # Ensure numeric for sorting
            sorted_df = sorted_df.sort_values(by=metric, ascending=True, ignore_index=True)

            industry_avg = sorted_df[metric].mean()

            fig = px.bar(
                sorted_df,
                y="title",
                x=metric,
                title=f"{metric.replace('_', ' ').title()}",
                labels={"title": "Channel", metric: metric.replace('_', ' ').title()},
                orientation='h',
                color_discrete_sequence=['#1f77b4']
            )
            fig.update_xaxes(showgrid=True)
            fig.update_layout(showlegend=False)

            # Add vertical line for industry average
            fig.add_vline(
                x=industry_avg,
                line_dash="dash",
                line_color="#ff7f0e",
                annotation_text="Industry Average",
                annotation_position="bottom right",
                annotation_font_color="#ff7f0e"
            )

            st.plotly_chart(fig, use_container_width=True)
        
        # Display metadata
        st.subheader("Channel Metadata")
        
        # Create a clean metadata dataframe for display
        metadata_df = channel_stats_df[["title", "firm_type", "target_audience", "content_type", "has_legacy_media"]].copy()
        
        # Format the target_audience column to display as comma-separated string
        metadata_df['target_audience'] = metadata_df['target_audience'].apply(
            lambda x: ', '.join(x) if isinstance(x, list) else x
        )
        
        # Rename columns for better display
        metadata_df.columns = [
            'Channel Name',
            'Firm Type',
            'Target Audience',
            'Content Type',
            'Has Legacy Media'
        ]
        
        # Display the table
        st.dataframe(
            metadata_df,
            use_container_width=True,
            hide_index=True
        )
else:
    st.warning("No channel statistics found. Please analyze some channels first.")

# Display market context
st.header("Market Context")
market_summary = market_data.get_market_summary()

# Create two columns for market data
col1, col2 = st.columns(2)

with col1:
    st.subheader("Equity Performance")
    
    # Create grouped bar chart for indices data
    indices_data = market_summary['indices']
    
    # Prepare data for the chart
    fig = go.Figure()
    
    # Add traces for each index
    for index in indices_data.index:
        fig.add_trace(go.Bar(
            name=index,
            x=indices_data.columns,
            y=indices_data.loc[index],
            text=indices_data.loc[index].round(2).astype(str) + '%',
            textposition='auto',
        ))
    
    # Update layout for relative barmode
    fig.update_layout(
        xaxis_title=None,
        yaxis_title="Performance (%)",
        barmode='group',
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Add a horizontal line at y=0 to separate positive and negative performance
    fig.add_shape(
        type="line",
        x0=-0.5,
        y0=0,
        x1=len(indices_data.columns) - 0.5,
        y1=0,
        line=dict(
            color="black",
            width=1,
            dash="dash",
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("VIX High-Low Range")
    
    # Create dumbbell chart for VIX data
    vix_data = market_summary['vix']
    
    # Prepare data for dumbbell chart
    periods = vix_data.columns.levels[1].tolist()
    
    fig = go.Figure()
    
    for period in periods:
        # Get high, low, and median values for this period
        high_values = vix_data[('high', period)].values
        low_values = vix_data[('low', period)].values
        median_values = vix_data[('median', period)].values
        
        # Add dumbbell for this period (vertical orientation)
        fig.add_trace(go.Scatter(
            x=[period, period],
            y=[low_values[0], high_values[0]],
            mode='markers+lines',
            name=period,
            line=dict(color='lightgray', width=2),
            marker=dict(
                color=['blue', 'red'],
                size=12,
                symbol=['circle', 'circle']
            ),
            showlegend=False
        ))
        
        # Add median line for this period
        fig.add_trace(go.Scatter(
            x=[period, period],
            y=[median_values[0], median_values[0]],
            mode='markers',
            name=f"{period} Median",
            marker=dict(
                color='green',
                size=8,
                symbol='diamond'
            ),
            showlegend=False
        ))
    
    fig.update_layout(
        yaxis_title="VIX Value",
        xaxis_title=None,
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Add a debug button in the sidebar
if st.sidebar.button("Debug API Connection"):
    st.sidebar.write("Testing API connection...")
    test_channel = DEFAULT_CHANNELS[0]
    st.sidebar.write(f"Testing with channel ID: {test_channel}")
    result = youtube_api.get_channel_statistics(test_channel)
    st.sidebar.write(f"API Test Result: {result}")

# Cleanup
if st.sidebar.button("Cleanup Resources"):
    data_processor.close()
    st.session_state.current_channels = set()
    st.success("Resources cleaned up!") 