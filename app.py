import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(page_title="PricePulse AI", page_icon="📉", layout="wide")
st.title("PricePulse AI — Self-Healing Price Tracker & RAG Assistant")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Track a Product URL")
    product_url = st.text_input("Product URL", placeholder="https://www.amazon.com/...")
    target_price = st.number_input("Target Alert Price (optional)", min_value=0.0, value=0.0, step=1.0)

    if st.button("Extract & Track", type="primary"):
        if not product_url.strip():
            st.warning("Please enter a valid product URL.")
        else:
            payload = {
                "url": product_url.strip(),
                "target_price": target_price if target_price > 0 else None,
            }
            with st.spinner("Converting HTML to Markdown and extracting JSON..."):
                resp = requests.post(f"{API_URL}/track", json=payload, timeout=30)
            if resp.ok:
                data = resp.json()
                st.success(f"Tracked: {data['title']} — {data['currency']} {data['price']:.2f}")
                if data.get("alert_sent"):
                    st.info("Price drop alert email sent!")
                st.json(data)
            else:
                st.error(f"Error: {resp.text}")

with col2:
    st.subheader("Ask the RAG Price Assistant")
    question = st.text_input(
        "Ask about tracked products",
        placeholder="Which tracked product is cheapest right now?",
    )
    if st.button("Ask Assistant"):
        if not question.strip():
            st.warning("Enter a question first.")
        else:
            with st.spinner("Searching tracked snapshots..."):
                resp = requests.post(f"{API_URL}/ask", json={"question": question}, timeout=30)
            if resp.ok:
                result = resp.json()
                st.markdown(result["answer"])
                with st.expander("Retrieved Sources"):
                    st.json(result["sources"])
            else:
                st.error(f"Error: {resp.text}")

st.subheader("Tracked Price History")
history_resp = requests.get(f"{API_URL}/history", timeout=10)
if history_resp.ok:
    snapshots = history_resp.json().get("snapshots", [])
    if snapshots:
        st.dataframe(snapshots, use_container_width=True)
    else:
        st.info("No snapshots logged yet. Track a URL above to get started.")
