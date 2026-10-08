import html

import streamlit as st

from analyzer import CATEGORIES, analyze_email

st.set_page_config(page_title="Email Triage Assistant", page_icon="📧", layout="wide")

SAMPLES = {
    "Write my own": "",
    "Delivery Issue": "Hello, I ordered a pair of headphones five days ago and they were supposed to arrive yesterday. I still haven't received them. Please check where my order is. Order ID: 45892.",
    "Product Complaint": "The blender I received today has a cracked jar. This is the second time this has happened! Order #77310. I am very disappointed.",
    "Refund Request": "I want my money back for order 20931. The shoes don't fit and I returned them last week. Please refund me as soon as possible.",
    "Product Inquiry": "Hi, is the Samsung 55-inch smart TV available in stock? Also, does it come with a wall mount?",
    "Technical Support": "URGENT: I am unable to log into my account since this morning. I keep getting 'invalid password' even after resetting it.",
    "General Inquiry": "Hello, I need some information about your services and your working hours. Thank you.",
}

NEUTRAL = ("#E6EAF0", "#3C4858")
PRIORITY = {"High": ("#FBE4E1", "#A52A1F"), "Medium": ("#FCEFD6", "#8A5A0B"), "Low": ("#DDF1E4", "#1E6B41")}
SENTIMENT = {"Negative": ("#FBE4E1", "#A52A1F"), "Neutral": NEUTRAL, "Positive": ("#DDF1E4", "#1E6B41")}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Newsreader:ital,wght@0,400;0,500;1,400&display=swap');
html, body, .stApp, .stApp button, .stApp textarea, .stApp input { font-family: 'Plus Jakarta Sans', sans-serif; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2.5rem; max-width: 1180px; }
.title { font-size: 2.1rem; font-weight: 700; color: #1B2430; margin: 0; letter-spacing: -0.5px; }
.sub { color: #5B6675; margin: 0.3rem 0 1.8rem 0; font-size: 1.02rem; }
.card { background: #FFFFFF; border: 1px solid #DFE4EB; border-radius: 12px; padding: 1.1rem 1.3rem; margin-bottom: 1rem; }
.h { font-weight: 600; color: #1B2430; margin-bottom: 0.7rem; }
.lbl { color: #6B7686; font-size: 0.85rem; margin-bottom: 0.35rem; }
.triage { display: flex; gap: 2.5rem; flex-wrap: wrap; align-items: flex-end; }
.cat { font-size: 1.35rem; font-weight: 700; color: #1B2430; }
.pill { display: inline-block; padding: 0.3rem 0.85rem; border-radius: 999px; font-weight: 600; font-size: 0.95rem; }
.kvs { display: flex; flex-wrap: wrap; gap: 0.6rem; }
.kv { background: #F1F4F9; border-radius: 8px; padding: 0.45rem 0.8rem; color: #1B2430; font-size: 0.93rem; }
.kv span { color: #6B7686; margin-right: 0.5rem; }
.action { border-left: 4px solid #3B4CCA; }
.letter { font-family: 'Newsreader', Georgia, serif; font-size: 1.1rem; line-height: 1.65; color: #232B36; }
.muted { color: #6B7686; }
.empty { text-align: center; padding: 3.5rem 1rem; color: #6B7686; border: 1.5px dashed #C9D1DC; border-radius: 12px; }
</style>
"""


def get_api_key():
    """On Streamlit Cloud the key comes from st.secrets; locally from .env."""
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return None


def pill(text, colors):
    bg, fg = colors
    return f'<span class="pill" style="background:{bg};color:{fg}">{html.escape(str(text))}</span>'


def show_result(r):
    category = html.escape(str(r.get("category", "-")))
    priority = r.get("priority", "-")
    sentiment = r.get("sentiment", "-")
    st.markdown(
        '<div class="card triage">'
        f'<div><div class="lbl">Category</div><div class="cat">{category}</div></div>'
        f'<div><div class="lbl">Priority</div>{pill(priority, PRIORITY.get(priority, NEUTRAL))}</div>'
        f'<div><div class="lbl">Sentiment</div>{pill(sentiment, SENTIMENT.get(sentiment, NEUTRAL))}</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    info = {k: v for k, v in (r.get("key_information") or {}).items() if v}
    chips = "".join(
        f'<div class="kv"><span>{html.escape(k.replace("_", " ").capitalize())}</span>{html.escape(str(v))}</div>'
        for k, v in info.items()
    ) or '<span class="muted">No specific details found.</span>'
    st.markdown(
        f'<div class="card"><div class="h">Key information</div><div class="kvs">{chips}</div></div>',
        unsafe_allow_html=True,
    )

    action = html.escape(str(r.get("recommended_action", "-")))
    st.markdown(
        f'<div class="card action"><div class="h">Recommended action</div>{action}</div>',
        unsafe_allow_html=True,
    )

    reply = str(r.get("response", ""))
    reply_html = html.escape(reply).replace("\n", "<br>")
    st.markdown(
        f'<div class="card"><div class="h">Drafted reply</div><div class="letter">{reply_html}</div></div>',
        unsafe_allow_html=True,
    )
    st.download_button("Download reply (.txt)", reply, file_name="reply.txt")

    with st.expander("See raw JSON"):
        st.json(r)


# ---------- Page ----------
st.markdown(CSS, unsafe_allow_html=True)
st.markdown('<h1 class="title">Email Triage Assistant</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub">Paste a customer email to get its category, urgency, tone, key details and a drafted reply.</p>',
    unsafe_allow_html=True,
)

left, right = st.columns([5, 6], gap="large")

with left:
    choice = st.selectbox("Load a sample email", list(SAMPLES))
    email = st.text_area(
        "Incoming email",
        value=SAMPLES[choice],
        height=320,
        placeholder="Paste the customer's email here...",
        key=f"email_{choice}",
    )
    clicked = st.button("Analyze email", type="primary", use_container_width=True)
    st.caption("Handles: " + ", ".join(CATEGORIES))

with right:
    if clicked:
        if not email.strip():
            st.warning("Paste an email on the left, then click Analyze email.")
        else:
            with st.spinner("Reading the email..."):
                try:
                    st.session_state["result"] = analyze_email(email, api_key=get_api_key())
                except Exception as e:
                    st.session_state.pop("result", None)
                    st.error(f"The analysis failed: {e}")

    if "result" in st.session_state:
        show_result(st.session_state["result"])
    else:
        st.markdown(
            '<div class="empty">Your results will appear here.<br>Pick a sample or paste an email, then click Analyze email.</div>',
            unsafe_allow_html=True,
        )