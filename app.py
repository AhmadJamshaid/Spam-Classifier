import streamlit as st
import pickle
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

try:
    nltk.data.find('corpora/stopwords')
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('stopwords')
    nltk.download('punkt')
    nltk.download('punkt_tab')

ps = PorterStemmer()

st.set_page_config(
    page_title="GuardianAI | Spam Shield",
    page_icon="🛡️",
    layout="centered"
)

st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=Syne:wght@700;800&display=swap" rel="stylesheet">

    <style>
    /* ─── RESET & BASE ─────────────────────────────────────────── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
        --bg-base:      #060810;
        --bg-surface:   #0c0e1a;
        --bg-raised:    #111426;
        --border:       rgba(255,255,255,0.06);
        --border-glow:  rgba(80,120,255,0.35);
        --accent:       #4d7cfe;
        --accent-dim:   rgba(77,124,254,0.12);
        --accent-glow:  rgba(77,124,254,0.25);
        --red:          #ff4757;
        --red-dim:      rgba(255,71,87,0.10);
        --green:        #2ed573;
        --green-dim:    rgba(46,213,115,0.10);
        --text-primary: #e8eaf6;
        --text-muted:   #6b7490;
        --text-faint:   #3a3f5c;
        --mono:         'Space Mono', monospace;
        --sans:         'DM Sans', sans-serif;
        --display:      'Syne', sans-serif;
        --grid-color:   rgba(77,124,254,0.03);
        --scan-color:   rgba(77,124,254,0.06);
    }

    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    .main, .stApp {
        font-family: var(--sans) !important;
        background-color: var(--bg-base) !important;
        color: var(--text-primary) !important;
    }

    /* ─── GRID BACKGROUND ──────────────────────────────────────── */
    [data-testid="stAppViewContainer"]::before {
        content: '';
        position: fixed;
        inset: 0;
        background-image:
            linear-gradient(var(--grid-color) 1px, transparent 1px),
            linear-gradient(90deg, var(--grid-color) 1px, transparent 1px);
        background-size: 40px 40px;
        pointer-events: none;
        z-index: 0;
    }

    /* Scan line animation */
    [data-testid="stAppViewContainer"]::after {
        content: '';
        position: fixed;
        left: 0; right: 0;
        height: 180px;
        background: linear-gradient(to bottom,
            transparent 0%,
            var(--scan-color) 50%,
            transparent 100%);
        animation: scanline 8s linear infinite;
        pointer-events: none;
        z-index: 1;
    }

    @keyframes scanline {
        0%   { top: -180px; }
        100% { top: 110vh; }
    }

    /* Ensure content stays above overlays */
    .block-container { position: relative; z-index: 2; }

    /* ─── HIDE STREAMLIT CHROME ────────────────────────────────── */
    #MainMenu, header, footer, .stDeployButton { visibility: hidden; display: none; }
    [data-testid="stHeader"] { background: transparent !important; }

    /* ─── LAYOUT ───────────────────────────────────────────────── */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 720px !important;
    }

    /* ─── SCROLLBAR ────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: var(--bg-base); }
    ::-webkit-scrollbar-thumb { background: var(--bg-raised); border-radius: 2px; }

    /* ─── SIDEBAR ──────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-surface) !important;
        border-right: 1px solid var(--border) !important;
        padding-top: 0 !important;
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 1.5rem !important;
    }

    /* ─── PANEL CARDS ──────────────────────────────────────────── */
    .panel {
        background: var(--bg-raised);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1.1rem 1.2rem;
        margin-bottom: 1rem;
        position: relative;
        overflow: hidden;
    }
    .panel::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--accent), transparent);
        opacity: 0.4;
    }
    .panel-label {
        font-family: var(--mono);
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: var(--accent);
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .panel-label::after {
        content: '';
        flex: 1;
        height: 1px;
        background: var(--border);
    }

    /* ─── STAT ROWS ────────────────────────────────────────────── */
    .stat-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.45rem 0;
        border-bottom: 1px solid var(--border);
    }
    .stat-row:last-child { border-bottom: none; }
    .stat-label {
        font-family: var(--mono);
        font-size: 0.72rem;
        color: var(--text-muted);
    }
    .stat-value {
        font-family: var(--mono);
        font-size: 0.72rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    .stat-value.ok { color: var(--green); }

    /* ─── HEADER ───────────────────────────────────────────────── */
    .hero {
        text-align: center;
        margin-bottom: 2.5rem;
        padding: 2.5rem 1.5rem 2rem;
        position: relative;
    }
    .hero-eyebrow {
        font-family: var(--mono);
        font-size: 0.65rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: var(--accent);
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.3rem 0.9rem;
        border: 1px solid rgba(77,124,254,0.25);
        border-radius: 2px;
        background: var(--accent-dim);
        margin-bottom: 1.25rem;
    }
    .hero-eyebrow::before {
        content: '●';
        font-size: 0.55rem;
        animation: blink 1.4s step-end infinite;
    }
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50%       { opacity: 0; }
    }
    .hero-title {
        font-family: var(--display);
        font-size: 3rem;
        font-weight: 800;
        color: var(--text-primary);
        letter-spacing: -0.03em;
        line-height: 1.05;
        margin-bottom: 0.25rem;
    }
    .hero-title span {
        color: var(--accent);
    }
    .hero-rule {
        width: 48px;
        height: 2px;
        background: var(--accent);
        margin: 1rem auto;
        border-radius: 1px;
    }
    .hero-sub {
        font-size: 0.9rem;
        color: var(--text-muted);
        line-height: 1.6;
        max-width: 440px;
        margin: 0 auto;
        font-weight: 300;
    }

    /* ─── INPUT SECTION ────────────────────────────────────────── */
    .input-section-label {
        font-family: var(--mono);
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: var(--text-muted);
        margin-bottom: 0.5rem;
    }

    div[data-baseweb="textarea"] {
        background-color: var(--bg-surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 6px !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    div[data-baseweb="textarea"]:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-glow) !important;
    }
    textarea {
        color: var(--text-primary) !important;
        font-family: var(--mono) !important;
        font-size: 0.83rem !important;
        line-height: 1.6 !important;
        background: transparent !important;
        caret-color: var(--accent) !important;
    }
    textarea::placeholder {
        color: var(--text-faint) !important;
    }

    /* Widget labels */
    div[data-testid="stWidgetLabel"] p {
        font-family: var(--mono) !important;
        font-size: 0.7rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.12em !important;
        text-transform: uppercase !important;
        color: var(--text-muted) !important;
        margin-bottom: 0.4rem !important;
    }

    /* ─── BUTTON ───────────────────────────────────────────────── */
    div.stButton { margin-top: 1rem; }
    div.stButton > button {
        width: 100% !important;
        background: transparent !important;
        color: var(--accent) !important;
        border: 1px solid var(--accent) !important;
        border-radius: 4px !important;
        padding: 0.75rem 1.5rem !important;
        font-family: var(--mono) !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.14em !important;
        text-transform: uppercase !important;
        transition: all 0.2s !important;
        position: relative !important;
        overflow: hidden !important;
    }
    div.stButton > button::before {
        content: '' !important;
        position: absolute !important;
        inset: 0 !important;
        background: var(--accent-dim) !important;
        opacity: 0 !important;
        transition: opacity 0.2s !important;
    }
    div.stButton > button:hover {
        background: var(--accent-dim) !important;
        box-shadow: 0 0 20px var(--accent-glow) !important;
        transform: translateY(-1px) !important;
    }
    div.stButton > button:active {
        transform: translateY(0) !important;
    }

    /* Sidebar buttons */
    section[data-testid="stSidebar"] div.stButton > button {
        border-color: var(--border) !important;
        color: var(--text-muted) !important;
        font-size: 0.72rem !important;
        padding: 0.55rem 0.9rem !important;
        text-transform: none !important;
        letter-spacing: 0.04em !important;
        text-align: left !important;
        justify-content: flex-start !important;
    }
    section[data-testid="stSidebar"] div.stButton > button:hover {
        border-color: var(--accent) !important;
        color: var(--text-primary) !important;
        box-shadow: none !important;
    }

    /* ─── RESULT CARDS ─────────────────────────────────────────── */
    .result-wrap {
        margin-top: 2rem;
        animation: fadeUp 0.35s ease-out forwards;
    }
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(12px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    .verdict-bar {
        display: flex;
        align-items: stretch;
        border-radius: 6px;
        overflow: hidden;
        border: 1px solid var(--border);
        margin-bottom: 1px;
    }
    .verdict-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 68px;
        font-size: 1.5rem;
        flex-shrink: 0;
    }
    .verdict-icon.spam { background: rgba(255,71,87,0.12); }
    .verdict-icon.ham  { background: rgba(46,213,115,0.10); }

    .verdict-content {
        flex: 1;
        padding: 1.1rem 1.25rem;
    }
    .verdict-tag {
        font-family: var(--mono);
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }
    .verdict-tag.spam { color: var(--red); }
    .verdict-tag.ham  { color: var(--green); }

    .verdict-title {
        font-family: var(--display);
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }
    .verdict-desc {
        font-size: 0.83rem;
        color: var(--text-muted);
        line-height: 1.6;
    }

    /* Confidence meter */
    .meter-block {
        background: var(--bg-raised);
        border: 1px solid var(--border);
        border-top: none;
        border-radius: 0 0 6px 6px;
        padding: 0.9rem 1.25rem;
    }
    .meter-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    .meter-label {
        font-family: var(--mono);
        font-size: 0.65rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--text-muted);
    }
    .meter-pct {
        font-family: var(--mono);
        font-size: 0.9rem;
        font-weight: 700;
    }
    .meter-pct.spam { color: var(--red); }
    .meter-pct.ham  { color: var(--green); }

    .meter-track {
        height: 4px;
        background: rgba(255,255,255,0.05);
        border-radius: 2px;
        overflow: hidden;
        position: relative;
    }
    .meter-fill {
        height: 100%;
        border-radius: 2px;
        position: relative;
    }
    .meter-fill.spam {
        background: linear-gradient(90deg, #c0392b, var(--red));
        box-shadow: 0 0 8px rgba(255,71,87,0.5);
    }
    .meter-fill.ham {
        background: linear-gradient(90deg, #27ae60, var(--green));
        box-shadow: 0 0 8px rgba(46,213,115,0.5);
    }

    /* ─── PRESETS HEADER ───────────────────────────────────────── */
    .sidebar-section-title {
        font-family: var(--mono);
        font-size: 0.63rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: var(--text-faint);
        padding: 0.6rem 0 0.4rem;
        border-top: 1px solid var(--border);
        margin-top: 0.5rem;
        margin-bottom: 0.3rem;
    }

    /* ─── DIVIDER ──────────────────────────────────────────────── */
    hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

    /* Warning & info messages */
    [data-testid="stAlert"] {
        background: var(--bg-raised) !important;
        border-color: var(--border) !important;
        border-radius: 6px !important;
        font-family: var(--mono) !important;
        font-size: 0.8rem !important;
    }

    /* Spinner */
    [data-testid="stSpinner"] p {
        font-family: var(--mono) !important;
        font-size: 0.8rem !important;
        color: var(--text-muted) !important;
    }
    </style>
""", unsafe_allow_html=True)


# ── BACKEND UTILS ──────────────────────────────────────────────────────────────

def transform_text(text):
    text = text.lower()
    text = nltk.word_tokenize(text)
    y = [i for i in text if i.isalnum()]
    y = [i for i in y if i not in stopwords.words('english')]
    y = [ps.stem(i) for i in y]
    return " ".join(y)

@st.cache_resource
def load_assets():
    with open('vectorizer.pkl', 'rb') as f:
        tfidf_vectorizer = pickle.load(f)
    with open('model.pkl', 'rb') as f:
        extra_trees_classifier = pickle.load(f)
    return tfidf_vectorizer, extra_trees_classifier

try:
    tfidf, model = load_assets()
except FileNotFoundError:
    st.error("❌  Resource Error: model.pkl and vectorizer.pkl not found in application directory.")
    st.stop()


# ── SIDEBAR ────────────────────────────────────────────────────────────────────

st.sidebar.markdown("""
    <div class="panel">
        <div class="panel-label">Engine</div>
        <div class="stat-row">
            <span class="stat-label">classifier</span>
            <span class="stat-value">Extra Trees</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">vectorizer</span>
            <span class="stat-value">TF-IDF</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">vocab dims</span>
            <span class="stat-value">7,403</span>
        </div>
    </div>

    <div class="panel">
        <div class="panel-label">Benchmark</div>
        <div class="stat-row">
            <span class="stat-label">accuracy</span>
            <span class="stat-value ok">98.24 %</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">precision</span>
            <span class="stat-value ok">98.92 %</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">recall</span>
            <span class="stat-value ok">97.35 %</span>
        </div>
        <div class="stat-row">
            <span class="stat-label">f1-score</span>
            <span class="stat-value ok">98.13 %</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── PRESET LOADER ──────────────────────────────────────────────────────────────

if "sms_input_raw" not in st.session_state:
    st.session_state.sms_input_raw = ""

def load_preset(text):
    st.session_state.sms_input_raw = text

presets = [
    {
        "label": "🚨  Spam — Lottery Prize",
        "text": "URGENT! You have won a 1-week free holiday to Spain plus £2,000 cash! Claim now by calling 09061701461. T&Cs apply."
    },
    {
        "label": "🚨  Spam — Phishing Link",
        "text": "Dear customer, your bank account has been flagged for suspicious logins. Please go to http://secure-verify-update.com immediately to secure it."
    },
    {
        "label": "✅  Ham — Meeting Reschedule",
        "text": "Hey, can we reschedule our project review meeting to 3 PM tomorrow? Let me know if that works for you."
    },
    {
        "label": "✅  Ham — Document Feedback",
        "text": "Thanks for sending the document, I will review it tonight and send back the comments first thing in the morning."
    }
]

st.sidebar.markdown('<div class="sidebar-section-title">Quick-Test Templates</div>', unsafe_allow_html=True)

for preset in presets:
    if st.sidebar.button(preset["label"], key=preset["label"] + "_btn"):
        load_preset(preset["text"])
        st.rerun()


# ── MAIN ───────────────────────────────────────────────────────────────────────

st.markdown("""
    <div class="hero">
        <div class="hero-eyebrow">Security Shield Active</div>
        <div class="hero-title">Guardian<span>AI</span></div>
        <div class="hero-rule"></div>
        <div class="hero-sub">
            Enterprise-grade spam classification powered by an
            optimized Extra&nbsp;Trees architecture with TF-IDF vectorization.
        </div>
    </div>
""", unsafe_allow_html=True)

input_sms = st.text_area(
    "INPUT — Paste email or SMS body for analysis",
    key="sms_input_raw",
    height=160,
    placeholder="// paste raw message, email body, or SMS text here..."
)

if st.button("▶  RUN THREAT ANALYSIS"):
    if not input_sms.strip():
        st.warning("⚠  Empty input — provide message text before running analysis.")
    else:
        with st.spinner("// vectorizing tokens and running classifier..."):
            processed_text  = transform_text(input_sms)
            vectorized_input = tfidf.transform([processed_text]).toarray()
            prediction_flag  = model.predict(vectorized_input)[0]
            probabilities    = model.predict_proba(vectorized_input)[0]
            ham_prob  = probabilities[0] * 100
            spam_prob = probabilities[1] * 100

            if prediction_flag == 1:
                confidence  = spam_prob
                theme_class = "spam"
                icon        = "🚨"
                verdict_tag = "THREAT DETECTED"
                title       = "Malicious SPAM Identified"
                desc        = (
                    "This transmission matches known patterns for automated, unsolicited, "
                    "or phishing communications. Structural characteristics flag this message "
                    "as high-risk. Do not click links or download attachments."
                )
            else:
                confidence  = ham_prob
                theme_class = "ham"
                icon        = "✅"
                verdict_tag = "CLEAN TRANSMISSION"
                title       = "Safe Message — HAM Verified"
                desc        = (
                    "No hazardous spam vectors or known suspicious footprints detected. "
                    "This transmission passes structural and statistical verification "
                    "and appears safe for normal interaction."
                )

            st.markdown(f"""
                <div class="result-wrap">
                    <div class="verdict-bar">
                        <div class="verdict-icon {theme_class}">{icon}</div>
                        <div class="verdict-content">
                            <div class="verdict-tag {theme_class}">{verdict_tag}</div>
                            <div class="verdict-title">{title}</div>
                            <div class="verdict-desc">{desc}</div>
                        </div>
                    </div>
                    <div class="meter-block">
                        <div class="meter-header">
                            <span class="meter-label">Classification Confidence</span>
                            <span class="meter-pct {theme_class}">{confidence:.2f}%</span>
                        </div>
                        <div class="meter-track">
                            <div class="meter-fill {theme_class}" style="width:{confidence:.2f}%"></div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
