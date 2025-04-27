import streamlit as st
from pathlib import Path
from auth import check_password

# Page config
st.set_page_config(
    page_title="Your Map of Financial Services YouTube",
    page_icon="📊",
    layout="wide"
)

if not check_password():
    st.stop()

# Main content
st.title("Building a Financial Services Youtube Channel")

# Introduction
st.markdown("""
This service will empower your firm to develop sound, data-driven strategy for monetizing your YouTube presence. Yes, even in today's historically volatile markets and with
ever-shifting consumer preferences on where and how they consume financial information.
            
We provide you with actionable insights into content performance, audience engagement, and relevant market context. We benchmark your channel against your direct competitors
and the wider universe of financial services firms on Youtube.
""")

st.subheader("Example Client: [VettaFi](https://www.youtube.com/@VettaFi)")

st.header("Quick-hit insights")
st.markdown("""
    - **Frequency**: Your **7+ videos per month** ranks your channel **2nd** amongst peers
    - **Views**: Your channel averages the **fewest views** per video amongst peers
    - **Subscribers per view**: Your **7 subs per 1,000 views** is **4th** amongst peers
    """)

st.header("Next steps")
st.markdown("""
    - Pare down content output to focus on the most engaging videos
    - With your authorization, integrate with YouTube Analytics API for more granular engagement metrics like watch time and click-through rates
    - Monitor metrics over time to understand how market performance, sentiment, and/or volatility correlate with your channel's performance, if at all
    - Factor in the additional resources needed for research, disclosures, and legal review when determining content frequency
    """)

# Why This Matters Now
st.header("Why This Matters Now")
st.markdown("""
The financial services industry is at a critical inflection point. With historically volatile markets and a demographic shift toward investors who don't consume traditional media, firms must adapt their communication strategies. This platform provides the analytical foundation needed to:

1. **Break into younger demographics** who primarily consume financial information through digital channels
2. **Optimize resource allocation** between traditional and digital media
3. **Make data-driven decisions** about content strategy in a rapidly evolving landscape
4. **Generate comparative insights** quickly, to see how you stack up against direct competitors and the wider universe of financial services firms on Youtube
""")