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

ps = PorterStemmer()

st.set_page_config(
    page_title="GuardianAI | Spam Shield",
    page_icon="🛡️",
    layout="centered"
)

st.markdown("""
    <style>
    .stApp {
        background-color: #2F3136;
        color: #FFFFFF;
    }
    h1 {
        color: #5865F2 !important; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
        text-align: center;
        margin-bottom: 5px;
    }
    p {
        text-align: center;
        color: #B9BBBE;
        font-size: 1.05rem;
    }
    div[data-baseweb="textarea"] {
        background-color: #202225 !important;
        border-radius: 8px !important;
        border: 1px solid #4f545c !important;
    }
    textarea {
        color: #FFFFFF !important;
    }
    div.stButton {
        text-align: center;
        margin-top: 25px;
    }
    div.stButton > button:first-child {
        background-color: #5865F2 !important;
        color: white !important;
        border-radius: 8px;
        padding: 12px 35px;
        font-size: 1rem;
        font-weight: bold;
        border: none;
        box-shadow: 0px 4px 10px rgba(88, 101, 242, 0.2);
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #4752C4 !important;
        transform: translateY(-1px);
        box-shadow: 0px 6px 15px rgba(88, 101, 242, 0.4);
    }
    </style>
""", unsafe_allow_html=True)

def transform_text(text):
    text = text.lower()
    text = nltk.word_tokenize(text)
    
    y = []
    for i in text:
        if i.isalnum():
            y.append(i)
            
    text = y[:]
    y.clear()
    
    for i in text:
        if i not in stopwords.words('english'):
            y.append(i)
            
    text = y[:]
    y.clear()
    
    for i in text:
        y.append(ps.stem(i))
        
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
    st.error("❌ Resource Error: Missing pipeline component arrays inside '/kaggle/working/'. Confirm pickle dumps completed successfully.")
    st.stop()

st.markdown("<h1>🛡️ GuardianAI</h1>", unsafe_allow_html=True)
st.markdown("<p>System Level Spam Classification Dashboard Powered by Extra Trees Architecture</p>", unsafe_allow_html=True)
st.markdown("---")

input_sms = st.text_area("Provide raw email array or blueprint text for feature breakdown:", height=160, placeholder="Paste sequence body logs here...")

if st.button('Run Deep Security Analysis'):
    if input_sms.strip() == "":
        st.warning("⚠️ Warning: Execution halted. Input string field cannot remain empty.")
    else:
        with st.spinner('Deconstructing and classifying mathematical token vectors...'):
            processed_text = transform_text(input_sms)
            vectorized_input = tfidf.transform([processed_text]).toarray()
            prediction_flag = model.predict(vectorized_input)[0]
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if prediction_flag == 1:
                st.error("🚨 **System Threat Isolation Alert: This transmission matches known patterns for malicious SPAM.** Source metrics flag structural hazards.")
            else:
                st.success("🍏 **Validation Confirmed: This transmission passes structural checks as HAM (Safe).** No threat vectors isolated.")
