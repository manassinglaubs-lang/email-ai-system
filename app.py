import streamlit as st
from analyzer import CATEGORIES, analyze_email

st.set_page_config(page_title="GenAI Email Assistant", page_icon="📧", layout="wide")

SAMPLES = {
    "(none)": "",
    "Delivery Issue": "Hello, I ordered a pair of headphones five days ago and they were supposed to arrive yesterday. I still haven't received them. Please check where my order is. Order ID: 45892.",
    "Product Complaint": "The blender I received today has a cracked jar. This is the second time this has happened! Order #77310. I am very disappointed.",
    "Refund Request": "I want my money back for order 20931. The shoes don't fit and I returned them last week. Please refund me as soon as possible.",
    "Product Inquiry": "Hi, is the Samsung 55-inch smart TV available in stock? Also, does it come with a wall mount?",
    "Technical Support": "URGENT: I am unable to log into my account since this morning. I keep getting 'invalid password' even after resetting it.",
    "General Inquiry": "Hello, I need some information about your services and your working hours. Thank you.",
}

PRIORITY_ICON = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}
SENTIMENT_ICON = {"Positive": "😊", "Neutral": "😐", "Negative": "😠"}


def get_api_key():
    """On Streamlit Cloud the key comes from st.secrets; locally from .env."""
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return None  # analyzer.py will fall back to the .env file


# ---------- Sidebar ----------
with st.sidebar:
    st.header("Try a sample")
    choice = st.selectbox("Sample email", list(SAMPLES))
    st.markdown("**Categories handled**")
    for c in CATEGORIES:
        st.write("•", c)

# ---------- Main page ----------
st.title("📧 GenAI Email Classification & Automated Response")
st.caption("Paste a customer email. The AI classifies it, extracts details and drafts a reply.")

email = st.text_area(
    "Customer email",
    value=SAMPLES[choice],
    height=200,
    placeholder="Paste the email here...",
    key=f"email_{choice}",  # resets the box when a sample is chosen
)

if st.button("Analyze Email", type="primary"):
    if not email.strip():
        st.warning("Please enter an email first.")
    else:
        with st.spinner("Analyzing..."):
            try:
                result = analyze_email(email, api_key=get_api_key())
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.stop()

        c1, c2, c3 = st.columns(3)
        c1.metric("Category", result.get("category", "-"))
        p = result.get("priority", "-")
        c2.metric("Priority", f"{PRIORITY_ICON.get(p, '')} {p}")
        s = result.get("sentiment", "-")
        c3.metric("Sentiment", f"{SENTIMENT_ICON.get(s, '')} {s}")

        st.subheader("Key Information")
        info = result.get("key_information") or {}
        shown = False
        for k, v in info.items():
            if v:
                st.write(f"• **{k.replace('_', ' ').title()}:** {v}")
                shown = True
        if not shown:
            st.write("No specific details found.")

        st.subheader("Recommended Action")
        st.info(result.get("recommended_action", "-"))

        st.subheader("AI-Generated Response")
        st.text_area("Draft reply", result.get("response", ""), height=250)

        with st.expander("Raw JSON output"):
            st.json(result)
