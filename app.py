# app.py - Raw Rhythm Rumble v11.0 (Arcade Arena UI + full feature audit fixes)

import streamlit as st
import pandas as pd
import random
import json
import io
import os
from datetime import datetime
import base64
import plotly.express as px
import plotly.graph_objects as go
from openpyxl.styles import PatternFill
from collections import Counter
import hashlib
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import tempfile
import copy
import plotly.io as pio

# Neon/transparent charts so they sit on the arena background
try:
    pio.templates["plotly_dark"].layout.update(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#dfe8ff", family="Rajdhani, sans-serif"),
        colorway=["#00f0ff", "#ff2bd6", "#9dff00", "#ffd400", "#7a5cff", "#ff7a00"],
    )
except Exception:
    pass

# ---------- PAGE CONFIGURATION ----------
st.set_page_config(
    page_title="Raw Rhythm Rumble",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- THEME CONFIGURATION ----------
def init_theme():
    if 'theme' not in st.session_state:
        st.session_state.theme = "light"

def get_theme_colors():
    if st.session_state.theme == "dark":
        return {
            "bg": "#1e1e1e",
            "card_bg": "#2d2d2d",
            "text": "#ffffff",
            "text_secondary": "#b0b0b0",
            "border": "#404040",
            "header_bg": "#2d2d2d",
            "success": "#4CAF50",
            "warning": "#ff9800",
            "danger": "#f44336",
            "info": "#2196F3",
            "shadow": "rgba(255,255,255,0.05)"
        }
    else:
        return {
            "bg": "#ffffff",
            "card_bg": "#f8f9fa",
            "text": "#000000",
            "text_secondary": "#666666",
            "border": "#e0e0e0",
            "header_bg": "#ffffff",
            "success": "#4CAF50",
            "warning": "#ff9800",
            "danger": "#f44336",
            "info": "#2196F3",
            "shadow": "rgba(0,0,0,0.08)"
        }

init_theme()

# ---------- ARCADE THEME ----------
ARCADE_CSS = r"""<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@400;500;600;700&display=swap');
:root{
  --bg0:#070816; --bg1:#0d1030; --panel:rgba(18,22,56,.88); --panel2:rgba(28,34,82,.85);
  --cyan:#00f0ff; --magenta:#ff2bd6; --lime:#9dff00; --gold:#ffd400; --red:#ff3860;
  --text:#e8efff; --muted:#9fb0dc; --line:rgba(0,240,255,.28);
}
html, body, .stApp, [data-testid="stAppViewContainer"]{
  font-family:'Rajdhani','Segoe UI',sans-serif !important; font-size:17px;
}
.stApp{
  color:var(--text) !important;
  background:
    radial-gradient(900px 500px at 12% -10%, rgba(255,43,214,.22), transparent 60%),
    radial-gradient(900px 600px at 95% 5%, rgba(0,240,255,.18), transparent 60%),
    linear-gradient(rgba(0,240,255,.045) 1px, transparent 1px) 0 0/44px 44px,
    linear-gradient(90deg, rgba(0,240,255,.045) 1px, transparent 1px) 0 0/44px 44px,
    linear-gradient(180deg, var(--bg1), var(--bg0) 70%) !important;
  background-attachment: fixed !important;
}
.stApp::after{content:"";position:fixed;inset:0;pointer-events:none;z-index:9999;
  background:repeating-linear-gradient(to bottom, rgba(255,255,255,.025) 0, rgba(255,255,255,.025) 1px, transparent 1px, transparent 3px);}
[data-testid="stHeader"]{background:transparent !important;}
.block-container{padding-top:1.4rem !important; max-width:1280px;}
h1,h2,h3,h4{font-family:'Orbitron',sans-serif !important; letter-spacing:.04em; color:#fff !important;}
h2,h3{text-shadow:0 0 14px rgba(0,240,255,.45);}
h3{font-size:1.25rem !important;}
p, li, label, span, div, [data-testid="stWidgetLabel"] p, [data-testid="stMarkdownContainer"] p{color:inherit;}
[data-testid="stWidgetLabel"] p, label{color:var(--muted) !important; font-weight:600 !important; letter-spacing:.03em;}
[data-testid="stCaptionContainer"], .stCaption{color:var(--muted) !important;}
hr{border:none !important; height:2px !important; background:linear-gradient(90deg,transparent,var(--cyan),var(--magenta),transparent) !important; opacity:.55;}
/* ---------- HUD title ---------- */
.hud{position:relative; text-align:center; padding:26px 16px 20px; margin-bottom:6px; border-radius:18px;
  background:linear-gradient(135deg, rgba(255,43,214,.20), rgba(0,240,255,.14) 55%, rgba(157,255,0,.10));
  border:1px solid var(--line); box-shadow:0 0 0 1px rgba(255,43,214,.25) inset, 0 0 40px rgba(0,240,255,.18), 0 0 80px rgba(255,43,214,.12); overflow:hidden;}
.hud::before{content:"";position:absolute;inset:-2px;border-radius:18px;padding:2px;
  background:conic-gradient(from 0deg,var(--cyan),var(--magenta),var(--gold),var(--lime),var(--cyan));
  -webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0); -webkit-mask-composite:xor; mask-composite:exclude;
  animation:spin 6s linear infinite; opacity:.85; pointer-events:none;}
@keyframes spin{to{filter:hue-rotate(360deg)}}
.hud-title{font-family:'Orbitron',sans-serif; font-weight:900; font-size:clamp(26px,6vw,56px); line-height:1.05; margin:0;
  background:linear-gradient(90deg,#fff,var(--cyan) 35%,var(--magenta) 70%,#fff); -webkit-background-clip:text; background-clip:text; color:transparent;
  filter:drop-shadow(0 0 14px rgba(0,240,255,.55)); letter-spacing:.06em;}
.hud-sub{font-family:'Orbitron',sans-serif; color:var(--gold); font-size:clamp(11px,2.4vw,16px); letter-spacing:.28em; margin-top:8px; text-transform:uppercase;}
.hud-icons{margin-top:12px; font-size:clamp(20px,4vw,30px); display:flex; justify-content:center; gap:clamp(10px,3vw,26px);}
.hud-icons span{animation:bob 2.4s ease-in-out infinite; filter:drop-shadow(0 0 8px rgba(0,240,255,.7));}
.hud-icons span:nth-child(2){animation-delay:.2s}.hud-icons span:nth-child(3){animation-delay:.4s}
.hud-icons span:nth-child(4){animation-delay:.6s}.hud-icons span:nth-child(5){animation-delay:.8s}.hud-icons span:nth-child(6){animation-delay:1s}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}
.hud-bar{display:flex; justify-content:center; gap:10px; flex-wrap:wrap; margin-top:12px; font-family:'Orbitron',sans-serif; font-size:11px; letter-spacing:.18em;}
.hud-bar b{padding:4px 12px; border-radius:20px; border:1px solid var(--line); background:rgba(0,0,0,.35); color:var(--cyan);}
/* ---------- press start ---------- */
.press-start-wrap{text-align:center; padding:50px 10px;}
.press-start{font-family:'Orbitron',sans-serif; font-weight:900; font-size:clamp(28px,7vw,60px); color:var(--gold);
  text-shadow:0 0 12px var(--gold),0 0 36px var(--magenta); animation:blink 1.1s steps(2,start) infinite;}
@keyframes blink{50%{opacity:.25}}
.press-sub{color:var(--muted); margin:12px 0 22px; font-size:18px;}
.arcade-row{font-size:34px; display:flex; justify-content:center; gap:18px;}
/* ---------- tabs = game menu ---------- */
[data-baseweb="tab-list"]{gap:6px !important; background:rgba(0,0,0,.30); padding:6px; border-radius:14px; border:1px solid var(--line); flex-wrap:wrap;}
button[data-baseweb="tab"]{background:transparent !important; border-radius:10px !important; padding:8px 14px !important; height:auto !important;
  font-family:'Orbitron',sans-serif !important; font-size:12px !important; letter-spacing:.05em; transition:all .18s;}
button[data-baseweb="tab"] p{color:var(--muted) !important; font-family:'Orbitron',sans-serif !important; font-size:12px !important; font-weight:700 !important;}
button[data-baseweb="tab"]:hover{background:rgba(0,240,255,.10) !important;}
button[data-baseweb="tab"][aria-selected="true"]{background:linear-gradient(135deg,rgba(0,240,255,.28),rgba(255,43,214,.28)) !important; box-shadow:0 0 16px rgba(0,240,255,.45);}
button[data-baseweb="tab"][aria-selected="true"] p{color:#fff !important; text-shadow:0 0 8px var(--cyan);}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"]{display:none !important;}
/* ---------- buttons ---------- */
.stButton>button, .stDownloadButton>button, [data-testid="stFormSubmitButton"]>button{
  font-family:'Orbitron',sans-serif !important; font-weight:700 !important; font-size:13px !important; letter-spacing:.06em; text-transform:uppercase;
  color:#fff !important; border:1px solid rgba(255,255,255,.18) !important; border-radius:12px !important; padding:.55rem 1rem !important;
  background:linear-gradient(135deg,#7a1fff,#ff2bd6) !important; box-shadow:0 4px 0 #3b0a88, 0 0 18px rgba(255,43,214,.35); transition:transform .1s, box-shadow .15s, filter .15s;}
.stButton>button:hover, .stDownloadButton>button:hover{filter:brightness(1.18); box-shadow:0 4px 0 #3b0a88, 0 0 28px rgba(0,240,255,.6); border-color:var(--cyan) !important; color:#fff !important;}
.stButton>button:active, .stDownloadButton>button:active{transform:translateY(3px); box-shadow:0 1px 0 #3b0a88, 0 0 14px rgba(255,43,214,.5);}
.stDownloadButton>button{background:linear-gradient(135deg,#00b8d4,#00f0a0) !important; box-shadow:0 4px 0 #006b6b,0 0 18px rgba(0,240,255,.35); color:#04121a !important;}
.stDownloadButton>button p{color:#04121a !important;}
/* ---------- metrics = HUD stat panels ---------- */
[data-testid="stMetric"]{background:var(--panel); border:1px solid var(--line); border-left:5px solid var(--cyan); border-radius:14px; padding:12px 16px;
  box-shadow:0 0 22px rgba(0,240,255,.10), inset 0 0 22px rgba(0,0,0,.35);}
[data-testid="stMetricLabel"] p{color:var(--muted) !important; font-family:'Orbitron',sans-serif !important; font-size:11px !important; letter-spacing:.1em; text-transform:uppercase;}
[data-testid="stMetricValue"]{font-family:'Orbitron',sans-serif !important; color:#fff !important; text-shadow:0 0 12px rgba(0,240,255,.7); font-size:clamp(20px,3.4vw,32px) !important;}
/* ---------- inputs ---------- */
[data-baseweb="input"], [data-baseweb="select"]>div, [data-baseweb="textarea"], .stNumberInput input, .stTextInput input, textarea{
  background:rgba(6,9,30,.85) !important; color:var(--text) !important; border-color:var(--line) !important; border-radius:10px !important;}
[data-baseweb="input"]:focus-within, [data-baseweb="select"]>div:focus-within, [data-baseweb="textarea"]:focus-within{border-color:var(--cyan) !important; box-shadow:0 0 14px rgba(0,240,255,.5) !important;}
input, textarea{color:var(--text) !important; caret-color:var(--cyan);}
[data-baseweb="popover"] ul, [data-baseweb="menu"]{background:#0d1030 !important; border:1px solid var(--line);}
[data-baseweb="popover"] li{color:var(--text) !important;} [data-baseweb="popover"] li:hover{background:rgba(0,240,255,.15) !important;}
/* ---------- sidebar = player panel ---------- */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0b0e2c,#12072e) !important; border-right:1px solid var(--line); box-shadow:6px 0 30px rgba(255,43,214,.12);}
[data-testid="stSidebar"] *{color:var(--text);}
[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{font-size:1rem !important;}
/* ---------- expanders / alerts / tables ---------- */
[data-testid="stExpander"]{background:var(--panel); border:1px solid var(--line) !important; border-radius:14px !important;}
[data-testid="stExpander"] summary p{font-family:'Orbitron',sans-serif !important; font-size:13px !important; color:#fff !important;}
[data-testid="stAlert"]{border-radius:12px !important; border:1px solid var(--line); background:var(--panel2) !important;}
[data-testid="stAlert"] p, [data-testid="stAlert"] div{color:var(--text) !important;}
[data-testid="stDataFrame"]{border:1px solid var(--line); border-radius:12px; overflow:hidden; box-shadow:0 0 22px rgba(0,240,255,.10);}
[data-testid="stFileUploader"] section{background:rgba(6,9,30,.7) !important; border:2px dashed var(--line) !important; border-radius:14px;}
/* ---------- re-skin the app's existing inline HTML cards (they were hard-coded white) ---------- */
[style*="background-color: #ffffff"], [style*="background-color:#ffffff"], [style*="background-color: #f8f9fa"]{
  background:linear-gradient(145deg,rgba(24,30,72,.96),rgba(12,15,42,.96)) !important; color:var(--text) !important;
  border-color:var(--line) !important; box-shadow:0 0 24px rgba(0,240,255,.14), inset 0 0 26px rgba(0,0,0,.35) !important;}
[style*="background-color: #fff3cd"],[style*="background-color: #fff3e0"],[style*="background-color: #fff8e6"],[style*="background-color: #fff0e6"]{
  background:rgba(255,170,0,.13) !important; color:var(--text) !important;}
[style*="background-color: #e8f5e9"],[style*="background-color: #e6ffe6"]{background:rgba(0,255,140,.12) !important; color:var(--text) !important;}
[style*="background-color: #ffe6e6"],[style*="background-color: #ffebee"]{background:rgba(255,56,96,.14) !important; color:var(--text) !important;}
[style*="background-color: #f5f5f5"]{background:rgba(255,255,255,.06) !important; color:var(--text) !important;}
[style*="color: #000000"],[style*="color:#000000"],[style*="color: #1a1a1a"],[style*="color: #333333"]{color:#f4f8ff !important;}
[style*="color: #666666"],[style*="color: #666;"],[style*="color: #888888"],[style*="color: #555"]{color:var(--muted) !important;}
[style*="color: #2e7d32"],[style*="color: #006600"]{color:#69f0ae !important;}
[style*="color: #e65100"]{color:#ffb74d !important;} [style*="color: #c62828"]{color:#ff8a9b !important;}
[style*="border: 1px solid #d0d0d0"],[style*="border: 2px solid #d0d0d0"],[style*="border: 2px solid #e0e0e0"]{border-color:var(--line) !important;}
[style*="gradient(135deg, #ffd700"], [style*="gradient(135deg, #ffd700"] *{color:#1a1200 !important; text-shadow:none !important;}
[style*="gradient(135deg, #ffd700"]{box-shadow:0 0 40px rgba(255,212,0,.55) !important; border:2px solid #fff3a0 !important;}
@media (max-width:640px){
  html,body,.stApp{font-size:16px;} .block-container{padding:.6rem .6rem 3rem !important;}
  button[data-baseweb="tab"]{padding:6px 9px !important;} .hud{padding:18px 10px 14px;}
}
</style>"""
st.markdown(ARCADE_CSS, unsafe_allow_html=True)

# ---------- APP TITLE ----------
theme_colors = get_theme_colors()
st.markdown("""
<div class="hud">
<div class="hud-title">RAW RHYTHM RUMBLE</div>
<div class="hud-sub">Tournament &amp; Recruiting Arena</div>
<div class="hud-icons"><span>⚽</span><span>🎯</span><span>🥊</span><span>🏎️</span><span>🔫</span><span>🎮</span></div>
<div class="hud-bar"><b>LIVE SCORES</b><b>BRACKETS</b><b>SCOUTING</b><b>ANALYTICS</b></div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ---------- SESSION STATE (Memory) ----------
def init_session_state():
    """Initialize all session state variables with proper types"""
    if 'players' not in st.session_state:
        st.session_state.players = pd.DataFrame(columns=[
            'Name', 'Age', 'Age Group', 'Game', 'Station', 
            'Wins', 'Losses', 'Status', 'Potential', 'Highlighted', 
            'Recruiter Notes', 'Highlight Reason'
        ])
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'bracket' not in st.session_state:
        st.session_state.bracket = pd.DataFrame(columns=[
            'Match ID', 'Round', 'Player 1', 'Player 2', 
            'Winner', 'Loser', 'Age Group', 'Game', 'Station', 'Score', 'Status',
            'Leg', 'Leg Number', 'Match Type', 'Scoring', 'Stats', 'Aggregate Score',
            'Match Mode'
        ])
    
    if 'tournament_active' not in st.session_state:
        st.session_state.tournament_active = False
    
    if 'live_scores' not in st.session_state:
        st.session_state.live_scores = pd.DataFrame(columns=[
            'Timestamp', 'Station', 'Match ID', 'Player 1', 'Player 2', 
            'Score', 'Winner', 'Recorded By', 'Age Group', 'Game'
        ])
    
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now()
    
    if 'help_requests' not in st.session_state:
        st.session_state.help_requests = pd.DataFrame(columns=[
            'Request ID', 'Timestamp', 'Station', 'Requested By', 
            'Issue Type', 'Message', 'Status', 'Admin Response', 
            'Resolved By', 'Resolved At'
        ])
    
    if 'notifications' not in st.session_state:
        st.session_state.notifications = pd.DataFrame(columns=[
            'Notification ID', 'Timestamp', 'Type', 'Message', 
            'Related Request', 'Read', 'Target Role'
        ])
    
    if 'station_config' not in st.session_state:
        st.session_state.station_config = {
            f"Station {i}": {"capacity": 8, "current": 0} 
            for i in range(1, 7)
        }
    
    if 'past_tournaments' not in st.session_state:
        st.session_state.past_tournaments = {}
    
    if 'tournament_history' not in st.session_state:
        st.session_state.tournament_history = []
    
    if 'mobile_view' not in st.session_state:
        st.session_state.mobile_view = False
    
    if 'current_round' not in st.session_state:
        st.session_state.current_round = 1
    
    if 'max_rounds' not in st.session_state:
        st.session_state.max_rounds = 1
    
    # Custom leg configuration per game
    if 'game_legs_config' not in st.session_state:
        st.session_state.game_legs_config = {
            "FIFA (Soccer)": 2,
            "Call of Duty": 3,
            "Fighting Games": 3,
            "Racing Games": 3,
            "FPS": 3,
            "Other": 2
        }
    
    # Auto-refresh state
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = False
    
    # Login page state
    if 'show_login_credentials' not in st.session_state:
        st.session_state.show_login_credentials = False
    
    # Suggested player for quick add
    if 'suggested_game' not in st.session_state:
        st.session_state.suggested_game = None
    if 'suggested_age' not in st.session_state:
        st.session_state.suggested_age = None

    # Highlight overrides: names an admin/recruiter manually un-highlighted (auto-highlight must respect this)
    if 'highlight_overrides' not in st.session_state:
        st.session_state.highlight_overrides = []
    if 'confirm_reshuffle' not in st.session_state:
        st.session_state.confirm_reshuffle = False
    if 'tournament_balloons_shown' not in st.session_state:
        st.session_state.tournament_balloons_shown = False

init_session_state()

BRACKET_COLUMNS = [
    'Match ID', 'Round', 'Player 1', 'Player 2', 'Winner', 'Loser', 'Age Group', 'Game',
    'Station', 'Score', 'Status', 'Leg', 'Leg Number', 'Match Type', 'Scoring', 'Stats',
    'Aggregate Score', 'Match Mode'
]

def empty_bracket():
    return pd.DataFrame(columns=BRACKET_COLUMNS)

# ---------- SECURITY SYSTEM ----------
def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, provided_password):
    """Verify a password against its hash"""
    return stored_hash == hash_password(provided_password)

def change_password(username, old_password, new_password):
    """Change a user's password"""
    if username not in USERS:
        return False, "User not found"
    
    if not verify_password(USERS[username]["password"], old_password):
        return False, "Current password is incorrect"
    
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters"
    
    USERS[username]["password"] = hash_password(new_password)
    return True, "Password changed successfully!"

# Enhanced user database with hashed passwords
# cache_resource keeps ONE shared dict alive across reruns, so new users / changed passwords stick
@st.cache_resource
def get_users_db():
  return {
      "admin": {
          "password": hash_password("admin123"),
          "role": "admin",
          "name": "System Admin",
          "email": "admin@rrr.com",
          "created": datetime.now().strftime("%Y-%m-%d")
      },
      "station1": {
          "password": hash_password("station1"),
          "role": "station_manager",
          "name": "Station 1 Manager",
          "stations": ["Station 1"],
          "email": "station1@rrr.com",
          "created": datetime.now().strftime("%Y-%m-%d")
      },
      "station2": {
          "password": hash_password("station2"),
          "role": "station_manager",
          "name": "Station 2 Manager",
          "stations": ["Station 2"],
          "email": "station2@rrr.com",
          "created": datetime.now().strftime("%Y-%m-%d")
      },
      "station3": {
          "password": hash_password("station3"),
          "role": "station_manager",
          "name": "Station 3 Manager",
          "stations": ["Station 3"],
          "email": "station3@rrr.com",
          "created": datetime.now().strftime("%Y-%m-%d")
      },
      "station4": {
          "password": hash_password("station4"),
          "role": "station_manager",
          "name": "Station 4 Manager",
          "stations": ["Station 4"],
          "email": "station4@rrr.com",
          "created": datetime.now().strftime("%Y-%m-%d")
      },
      "station5": {
          "password": hash_password("station5"),
          "role": "station_manager",
          "name": "Station 5 Manager",
          "stations": ["Station 5"],
          "email": "station5@rrr.com",
          "created": datetime.now().strftime("%Y-%m-%d")
      },
      "station6": {
          "password": hash_password("station6"),
          "role": "station_manager",
          "name": "Station 6 Manager",
          "stations": ["Station 6"],
          "email": "station6@rrr.com",
          "created": datetime.now().strftime("%Y-%m-%d")
      },
      "recruiter": {
          "password": hash_password("recruit"),
          "role": "recruiter",
          "name": "Recruiter",
          "email": "recruiter@rrr.com",
          "created": datetime.now().strftime("%Y-%m-%d")
      }
  }

USERS = get_users_db()

# Add user management functions
def add_user(username, password, role, name, email="", stations=None):
    """Add a new user to the system"""
    if username in USERS:
        return False, "Username already exists"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    USERS[username] = {
        "password": hash_password(password),
        "role": role,
        "name": name,
        "email": email,
        "stations": stations if stations else [],
        "created": datetime.now().strftime("%Y-%m-%d")
    }
    return True, "User created successfully"

def delete_user(username):
    """Delete a user from the system"""
    if username == "admin":
        return False, "Cannot delete admin user"
    if username not in USERS:
        return False, "User not found"
    del USERS[username]
    return True, "User deleted successfully"

# ---------- GAME CONFIGURATION SYSTEM ----------
def get_game_config(game_name):
    """Get configuration for a specific game with custom leg count"""
    base_config = {
        "FIFA (Soccer)": {
            "type": "soccer",
            "scoring": "goals",
            "match_structure": ["First Leg", "Second Leg", "Aggregate"],
            "stat_tracking": ["Goals", "Shots", "Possession", "Corners"],
            "win_condition": "aggregate_goals",
            "description": "Two-leg format with aggregate scoring",
            "head_to_head": True,
            "individual_scoring": False
        },
        "Call of Duty": {
            "type": "fps",
            "scoring": "kills",
            "match_structure": ["Match 1", "Match 2", "Match 3"],
            "stat_tracking": ["Kills", "Deaths", "Assists", "K/D Ratio"],
            "win_condition": "best_of_3",
            "description": "Best of 3 matches based on kills",
            "head_to_head": False,
            "individual_scoring": True
        },
        "Fighting Games": {
            "type": "fighting",
            "scoring": "rounds",
            "match_structure": ["Round 1", "Round 2", "Round 3"],
            "stat_tracking": ["Rounds Won", "Perfect Rounds", "Combos"],
            "win_condition": "best_of_3",
            "description": "Best of 3 rounds",
            "head_to_head": True,
            "individual_scoring": False
        },
        "Racing Games": {
            "type": "racing",
            "scoring": "time",
            "match_structure": ["Race 1", "Race 2", "Race 3"],
            "stat_tracking": ["Best Time", "Average Time", "Laps", "Position"],
            "win_condition": "best_time",
            "description": "Best time across races",
            "head_to_head": True,
            "individual_scoring": False
        },
        "FPS": {
            "type": "fps",
            "scoring": "kills",
            "match_structure": ["Match 1", "Match 2", "Match 3"],
            "stat_tracking": ["Kills", "Deaths", "Assists", "K/D Ratio"],
            "win_condition": "best_of_3",
            "description": "Best of 3 matches",
            "head_to_head": False,
            "individual_scoring": True
        },
        "Other": {
            "type": "custom",
            "scoring": "points",
            "match_structure": ["Match 1", "Match 2"],
            "stat_tracking": ["Points", "Score"],
            "win_condition": "total_points",
            "description": "Custom tournament format",
            "head_to_head": True,
            "individual_scoring": False
        }
    }
    
    config = base_config.get(game_name, base_config["Other"]).copy()
    
    # Add custom legs from config
    legs = st.session_state.game_legs_config.get(game_name, 2)
    config["rounds"] = legs
    
    # Update match structure based on leg count
    if legs == 1:
        config["match_structure"] = ["Match"]
    elif legs == 2:
        config["match_structure"] = ["Leg 1", "Leg 2", "Aggregate"]
    elif legs == 3:
        config["match_structure"] = ["Match 1", "Match 2", "Match 3"]
    elif legs >= 4:
        config["match_structure"] = [f"Match {i+1}" for i in range(legs)] + ["Aggregate"]
    
    return config

# ---------- GAME-SPECIFIC MATCH STATS ----------

# Define stat templates for each game
GAME_STATS_TEMPLATES = {
    "FIFA (Soccer)": {
        "stats": [
            {"id": "goals", "label": "⚽ Goals", "type": "number", "icon": "⚽"},
            {"id": "shots", "label": "🎯 Shots", "type": "number", "icon": "🎯"},
            {"id": "shots_on_target", "label": "📊 Shots on Target", "type": "number", "icon": "📊"},
            {"id": "possession", "label": "🔄 Possession", "type": "percent", "icon": "🔄"},
            {"id": "corners", "label": "🏁 Corners", "type": "number", "icon": "🏁"},
            {"id": "yellow_cards", "label": "🟨 Yellow Cards", "type": "number", "icon": "🟨"},
            {"id": "red_cards", "label": "🟥 Red Cards", "type": "number", "icon": "🟥"}
        ],
        "key_stats": ["goals", "shots", "possession"],
        "winner_by": "goals"
    },
    "Call of Duty": {
        "stats": [
            {"id": "kills", "label": "💀 Kills", "type": "number", "icon": "💀"},
            {"id": "deaths", "label": "☠️ Deaths", "type": "number", "icon": "☠️"},
            {"id": "assists", "label": "🤝 Assists", "type": "number", "icon": "🤝"},
            {"id": "headshots", "label": "🎯 Headshots", "type": "number", "icon": "🎯"},
            {"id": "kd_ratio", "label": "📈 K/D Ratio", "type": "decimal", "icon": "📈"}
        ],
        "key_stats": ["kills", "kd_ratio", "headshots"],
        "winner_by": "kills"
    },
    "Fighting Games": {
        "stats": [
            {"id": "rounds_won", "label": "👊 Rounds Won", "type": "number", "icon": "👊"},
            {"id": "rounds_lost", "label": "✋ Rounds Lost", "type": "number", "icon": "✋"},
            {"id": "perfect_rounds", "label": "⭐ Perfect Rounds", "type": "number", "icon": "⭐"},
            {"id": "combos", "label": "🔥 Combos", "type": "number", "icon": "🔥"},
            {"id": "damage_dealt", "label": "💥 Damage Dealt", "type": "percent", "icon": "💥"}
        ],
        "key_stats": ["rounds_won", "combos", "perfect_rounds"],
        "winner_by": "rounds_won"
    },
    "Racing Games": {
        "stats": [
            {"id": "best_lap", "label": "🏎️ Best Lap", "type": "time", "icon": "🏎️"},
            {"id": "total_time", "label": "⏱️ Total Time", "type": "time", "icon": "⏱️"},
            {"id": "position", "label": "🏁 Position", "type": "number", "icon": "🏁"},
            {"id": "laps_completed", "label": "🔄 Laps Completed", "type": "number", "icon": "🔄"}
        ],
        "key_stats": ["best_lap", "total_time", "position"],
        "winner_by": "position"
    },
    "FPS": {
        "stats": [
            {"id": "kills", "label": "💀 Kills", "type": "number", "icon": "💀"},
            {"id": "deaths", "label": "☠️ Deaths", "type": "number", "icon": "☠️"},
            {"id": "assists", "label": "🤝 Assists", "type": "number", "icon": "🤝"},
            {"id": "kd_ratio", "label": "📈 K/D Ratio", "type": "decimal", "icon": "📈"}
        ],
        "key_stats": ["kills", "kd_ratio"],
        "winner_by": "kills"
    },
    "Other": {
        "stats": [
            {"id": "score", "label": "📊 Score", "type": "number", "icon": "📊"},
            {"id": "points", "label": "⭐ Points", "type": "number", "icon": "⭐"}
        ],
        "key_stats": ["score"],
        "winner_by": "score"
    }
}

def get_game_stats_template(game_name):
    """Get the stats template for a specific game"""
    return GAME_STATS_TEMPLATES.get(game_name, GAME_STATS_TEMPLATES["Other"])

def render_match_stats_form(game_name, player1_name, player2_name, leg_number=1, key_prefix=""):
    """Render a dynamic stats form for a match"""
    template = get_game_stats_template(game_name)
    
    st.markdown(f"### 📊 Match Statistics - Leg {leg_number}")
    st.caption(f"Enter detailed stats for {game_name}")
    
    # Create two columns for players
    col1, col2 = st.columns(2)
    
    stats_data = {"game": game_name, "player1": player1_name, "player2": player2_name, "leg": leg_number}
    
    with col1:
        st.markdown(f"### 👤 {player1_name}")
        for stat in template["stats"]:
            if stat["type"] == "number":
                value = st.number_input(
                    f"{stat['label']}",
                    min_value=0,
                    value=0,
                    step=1,
                    key=f"{key_prefix}stats_p1_{stat['id']}_{player1_name}_{leg_number}"
                )
                stats_data[f"p1_{stat['id']}"] = value
            elif stat["type"] == "percent":
                value = st.slider(
                    f"{stat['label']}",
                    min_value=0,
                    max_value=100,
                    value=50,
                    key=f"{key_prefix}stats_p1_{stat['id']}_{player1_name}_{leg_number}"
                )
                stats_data[f"p1_{stat['id']}"] = value
            elif stat["type"] == "decimal":
                value = st.number_input(
                    f"{stat['label']}",
                    min_value=0.0,
                    value=0.0,
                    step=0.1,
                    format="%.1f",
                    key=f"{key_prefix}stats_p1_{stat['id']}_{player1_name}_{leg_number}"
                )
                stats_data[f"p1_{stat['id']}"] = value
            elif stat["type"] == "time":
                value = st.text_input(
                    f"{stat['label']}",
                    value="0:00.000",
                    placeholder="e.g., 1:23.456",
                    key=f"{key_prefix}stats_p1_{stat['id']}_{player1_name}_{leg_number}"
                )
                stats_data[f"p1_{stat['id']}"] = value
    
    with col2:
        st.markdown(f"### 👤 {player2_name}")
        for stat in template["stats"]:
            if stat["type"] == "number":
                value = st.number_input(
                    f"{stat['label']}",
                    min_value=0,
                    value=0,
                    step=1,
                    key=f"{key_prefix}stats_p2_{stat['id']}_{player2_name}_{leg_number}"
                )
                stats_data[f"p2_{stat['id']}"] = value
            elif stat["type"] == "percent":
                value = st.slider(
                    f"{stat['label']}",
                    min_value=0,
                    max_value=100,
                    value=50,
                    key=f"{key_prefix}stats_p2_{stat['id']}_{player2_name}_{leg_number}"
                )
                stats_data[f"p2_{stat['id']}"] = value
            elif stat["type"] == "decimal":
                value = st.number_input(
                    f"{stat['label']}",
                    min_value=0.0,
                    value=0.0,
                    step=0.1,
                    format="%.1f",
                    key=f"{key_prefix}stats_p2_{stat['id']}_{player2_name}_{leg_number}"
                )
                stats_data[f"p2_{stat['id']}"] = value
            elif stat["type"] == "time":
                value = st.text_input(
                    f"{stat['label']}",
                    value="0:00.000",
                    placeholder="e.g., 1:23.456",
                    key=f"{key_prefix}stats_p2_{stat['id']}_{player2_name}_{leg_number}"
                )
                stats_data[f"p2_{stat['id']}"] = value
    
    return stats_data

def display_match_stats(stats_data, game_name, player1_name, player2_name):
    """Display match stats in a nice visual format"""
    if not stats_data or len(stats_data) < 3:
        return
    
    template = get_game_stats_template(game_name)
    
    st.markdown("### 📊 Match Statistics Summary")
    
    # Create a comparison table
    rows = []
    for stat in template["stats"]:
        p1_key = f"p1_{stat['id']}"
        p2_key = f"p2_{stat['id']}"
        
        if p1_key in stats_data and p2_key in stats_data:
            p1_val = stats_data[p1_key]
            p2_val = stats_data[p2_key]
            
            # Format display values
            if stat["type"] == "percent":
                p1_display = f"{p1_val}%"
                p2_display = f"{p2_val}%"
            elif stat["type"] == "decimal":
                p1_display = f"{p1_val:.1f}"
                p2_display = f"{p2_val:.1f}"
            elif stat["type"] == "time":
                p1_display = str(p1_val)
                p2_display = str(p2_val)
            else:
                p1_display = str(p1_val)
                p2_display = str(p2_val)
            
            # Determine winner for each stat
            if isinstance(p1_val, (int, float)) and isinstance(p2_val, (int, float)):
                if p1_val > p2_val:
                    p1_display = f"🏆 {p1_display}"
                elif p2_val > p1_val:
                    p2_display = f"🏆 {p2_display}"
            
            rows.append({
                "Stat": f"{stat['icon']} {stat['label']}",
                player1_name: p1_display,
                player2_name: p2_display
            })
    
    if rows:
        stats_df = pd.DataFrame(rows)
        st.dataframe(stats_df, use_container_width=True, hide_index=True)

# ---------- INDIVIDUAL SCORING FUNCTIONS ----------
def render_individual_score_form(match_data):
    """Render a form for entering individual match scores"""
    game_name = match_data['Game']
    player_name = match_data['Player 1']
    leg_number = match_data['Leg Number']
    key_prefix = f"{match_data['Match ID']}_"
    
    st.info(f"🎯 Individual Match - {player_name} is competing solo")
    st.caption(f"Enter the player's performance stats for {game_name}")
    
    # Get the stats template
    template = get_game_stats_template(game_name)
    
    stats_data = {"game": game_name, "player": player_name, "leg": leg_number}
    
    # Show all stats for the player
    for stat in template["stats"]:
        if stat["type"] == "number":
            value = st.number_input(
                f"{stat['label']}",
                min_value=0,
                value=0,
                step=1,
                key=f"{key_prefix}indiv_result_{stat['id']}_{player_name}_{leg_number}"
            )
            stats_data[stat['id']] = value
        elif stat["type"] == "percent":
            value = st.slider(
                f"{stat['label']}",
                min_value=0,
                max_value=100,
                value=50,
                key=f"{key_prefix}indiv_result_{stat['id']}_{player_name}_{leg_number}"
            )
            stats_data[stat['id']] = value
        elif stat["type"] == "decimal":
            value = st.number_input(
                f"{stat['label']}",
                min_value=0.0,
                value=0.0,
                step=0.1,
                format="%.1f",
                key=f"{key_prefix}indiv_result_{stat['id']}_{player_name}_{leg_number}"
            )
            stats_data[stat['id']] = value
    
    # Calculate a score based on the key stats
    scoring_stat = template.get("winner_by", "score")
    total_score = stats_data.get(scoring_stat, 0)
    if not isinstance(total_score, (int, float)):
        total_score = 0
    
    # Determine if player performed well based on game type
    if game_name == "Call of Duty" or game_name == "FPS":
        kills = stats_data.get('kills', 0)
        kd_ratio = stats_data.get('kd_ratio', 0)
        st.info(f"💀 Total Kills: {kills}")
        if kd_ratio > 2.0:
            st.success(f"🌟 Excellent K/D Ratio: {kd_ratio:.1f}")
        elif kd_ratio > 1.0:
            st.success(f"📈 Good K/D Ratio: {kd_ratio:.1f}")
        else:
            st.warning(f"📊 K/D Ratio: {kd_ratio:.1f}")
    
    return stats_data, total_score

def display_individual_match_stats(stats_data, game_name, player_name):
    """Display individual match stats for shooting games"""
    if not stats_data or len(stats_data) < 2:
        return
    
    template = get_game_stats_template(game_name)
    
    st.markdown(f"### 📊 {player_name} - Match Statistics")
    
    # Create a nice display of stats
    stat_rows = []
    for stat in template["stats"]:
        stat_id = stat['id']
        if stat_id in stats_data:
            value = stats_data[stat_id]
            # Format display values
            if stat["type"] == "percent":
                display_value = f"{value}%"
            elif stat["type"] == "decimal":
                display_value = f"{value:.1f}"
            else:
                display_value = str(value)
            
            stat_rows.append({
                "Stat": f"{stat['icon']} {stat['label']}",
                "Value": display_value
            })
    
    if stat_rows:
        stats_df = pd.DataFrame(stat_rows)
        st.dataframe(stats_df, use_container_width=True, hide_index=True)
    
    # Show key stats as highlight
    key_stats = template.get("key_stats", [])
    if key_stats:
        st.markdown("### 📈 Key Performance Indicators")
        cols = st.columns(min(len(key_stats), 3))
        for idx, stat_id in enumerate(key_stats[:3]):
            if stat_id in stats_data:
                value = stats_data[stat_id]
                # Find the stat label
                stat_label = stat_id
                for stat in template["stats"]:
                    if stat["id"] == stat_id:
                        stat_label = stat["label"]
                        break
                
                with cols[idx]:
                    st.metric(stat_label, value)

# ---------- MULTI-GAME TOURNAMENT CHAMPIONS SYSTEM ----------
def init_champions():
    """Initialize champions tracking in session state"""
    if 'tournament_champions' not in st.session_state:
        st.session_state.tournament_champions = {
            "FIFA (Soccer)": {"champion": "", "runner_up": "", "matches": [], "last_updated": ""},
            "Call of Duty": {"champion": "", "runner_up": "", "matches": [], "last_updated": ""},
            "Fighting Games": {"champion": "", "runner_up": "", "matches": [], "last_updated": ""},
            "Racing Games": {"champion": "", "runner_up": "", "matches": [], "last_updated": ""},
            "FPS": {"champion": "", "runner_up": "", "matches": [], "last_updated": ""},
            "Other": {"champion": "", "runner_up": "", "matches": [], "last_updated": ""}
        }

init_champions()

def get_game_champion(game_name):
    """Get the current champion for a specific game"""
    if game_name in st.session_state.tournament_champions:
        return st.session_state.tournament_champions[game_name]
    return None

def set_game_champion(game_name, champion, runner_up="", matches=None):
    """Set the champion for a specific game"""
    if game_name in st.session_state.tournament_champions:
        st.session_state.tournament_champions[game_name] = {
            "champion": champion,
            "runner_up": runner_up,
            "matches": matches if matches else [],
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return True
    return False

def determine_game_champion(bracket_df, game_name):
    """Determine champion + runner-up for a game.
    Individual games: highest total score. Head-to-head: most match wins (ties broken by goals/score)."""
    if bracket_df.empty:
        return None, None

    game_matches = bracket_df[
        (bracket_df['Game'] == game_name) &
        (bracket_df['Status'] == 'Completed') &
        (bracket_df['Winner'] != '')
    ]
    if game_matches.empty:
        return None, None

    game_config = get_game_config(game_name)

    if game_config.get('individual_scoring', False):
        totals = {}
        for _, row in game_matches.iterrows():
            try:
                totals[row['Player 1']] = totals.get(row['Player 1'], 0) + float(str(row['Score']).replace(',', ''))
            except (ValueError, TypeError):
                totals.setdefault(row['Player 1'], 0)
        ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
        if ranked:
            return ranked[0][0], (ranked[1][0] if len(ranked) > 1 else "")
        return None, None

    winners = [w for w in game_matches['Winner'].tolist() if w not in ['BYE', 'N/A', '']]
    if not winners:
        return None, None
    ranked = Counter(winners).most_common()
    return ranked[0][0], (ranked[1][0] if len(ranked) > 1 else "")

def get_game_icon(game_name):
    """Get an icon for each game type"""
    icons = {
        "FIFA (Soccer)": "⚽",
        "Call of Duty": "🎯",
        "Fighting Games": "🥊",
        "Racing Games": "🏎️",
        "FPS": "🔫",
        "Other": "🎮"
    }
    return icons.get(game_name, "🎮")

def get_game_color(game_name):
    """Get a color for each game type"""
    colors = {
        "FIFA (Soccer)": "#4CAF50",  # Green
        "Call of Duty": "#FF5722",   # Orange
        "Fighting Games": "#E91E63", # Pink
        "Racing Games": "#2196F3",   # Blue
        "FPS": "#FF9800",            # Amber
        "Other": "#9E9E9E"           # Gray
    }
    return colors.get(game_name, "#9E9E9E")

# ---------- FLEXIBLE TOURNAMENT FUNCTIONS ----------
def generate_flexible_bracket(players_df, start_id=1):
    """Generate tournament bracket grouping players by game type with custom legs"""
    matches = []
    active_players = players_df[players_df['Status'] == 'Active']
    
    if len(active_players) < 2:
        return empty_bracket()
    
    # Group players by game
    games_grouped = active_players.groupby('Game')
    
    match_id = start_id
    
    for game, group_players in games_grouped:
        # Get game configuration for this specific game with custom legs
        game_config = get_game_config(game)
        
        # Check if this is an individual scoring game (shooting games)
        is_individual = game_config.get('individual_scoring', False)
        
        # Get number of rounds/legs for this game from config
        num_rounds = game_config.get("rounds", 2)
        
        # Further group by age group within each game
        age_groups = group_players.groupby('Age Group')
        
        for age_group, age_group_players in age_groups:
            player_names = age_group_players['Name'].tolist()
            random.shuffle(player_names)
            
            if is_individual:
                # INDIVIDUAL SCORING MODE (Shooting Games)
                # Each player plays alone, scored against target/time
                for player in player_names:
                    player_station = age_group_players[age_group_players['Name'] == player].iloc[0]['Station']
                    for leg_index in range(num_rounds):
                        leg_name = f"Match {leg_index + 1}"
                        match = {
                            'Match ID': f"M{match_id}",
                            'Round': f"Round {leg_index + 1}",
                            'Player 1': player,
                            'Player 2': 'INDIVIDUAL',
                            'Winner': '',
                            'Loser': '',
                            'Age Group': age_group,
                            'Game': game,
                            'Station': player_station,
                            'Score': '',
                            'Status': 'Pending',
                            'Leg': leg_name,
                            'Leg Number': leg_index + 1,
                            'Match Type': game_config['type'],
                            'Scoring': f"{game_config['scoring']}_individual",
                            'Stats': '{}',
                            'Aggregate Score': '',
                            'Match Mode': 'Individual'
                        }
                        matches.append(match)
                        match_id += 1
            else:
                # HEAD-TO-HEAD MODE (Traditional)
                # Pair players for matches
                match_structure = game_config.get("match_structure", [f"Match {i+1}" for i in range(num_rounds)])
                
                for i in range(0, len(player_names) - 1, 2):
                    p1 = player_names[i]
                    p2 = player_names[i + 1] if i + 1 < len(player_names) else 'BYE'
                    
                    if p2 != 'BYE':
                        # Create matches for each leg/structure
                        for leg_index, leg_name in enumerate(match_structure):
                            # Skip aggregate if it's the last item and there are multiple legs
                            if leg_name == "Aggregate" and len(match_structure) > 1:
                                continue
                                
                            match = {
                                'Match ID': f"M{match_id}",
                                'Round': f"Round {leg_index + 1}",
                                'Player 1': p1,
                                'Player 2': p2,
                                'Winner': '',
                                'Loser': '',
                                'Age Group': age_group,
                                'Game': game,
                                'Station': age_group_players[age_group_players['Name'] == p1].iloc[0]['Station'],
                                'Score': '',
                                'Status': 'Pending',
                                'Leg': leg_name,
                                'Leg Number': leg_index + 1,
                                'Match Type': game_config['type'],
                                'Scoring': game_config['scoring'],
                                'Stats': '{}',
                                'Aggregate Score': '',
                                'Match Mode': 'Head-to-Head'
                            }
                            matches.append(match)
                            match_id += 1
                    else:
                        # BYE match - auto win
                        match = {
                            'Match ID': f"M{match_id}",
                            'Round': 'Round 1',
                            'Player 1': p1,
                            'Player 2': 'BYE',
                            'Winner': p1,
                            'Loser': '',
                            'Age Group': age_group,
                            'Game': game,
                            'Station': age_group_players[age_group_players['Name'] == p1].iloc[0]['Station'],
                            'Score': 'BYE',
                            'Status': 'Completed',
                            'Leg': 'BYE',
                            'Leg Number': 0,
                            'Match Type': game_config['type'],
                            'Scoring': game_config['scoring'],
                            'Stats': '{}',
                            'Aggregate Score': '',
                            'Match Mode': 'Head-to-Head'
                        }
                        matches.append(match)
                        match_id += 1
                
                # Handle odd number of players
                if len(player_names) % 2 == 1:
                    p1 = player_names[-1]
                    match = {
                        'Match ID': f"M{match_id}",
                        'Round': 'Round 1',
                        'Player 1': p1,
                        'Player 2': 'BYE',
                        'Winner': p1,
                        'Loser': '',
                        'Age Group': age_group,
                        'Game': game,
                        'Station': age_group_players[age_group_players['Name'] == p1].iloc[0]['Station'],
                        'Score': 'BYE',
                        'Status': 'Completed',
                        'Leg': 'BYE',
                        'Leg Number': 0,
                        'Match Type': game_config['type'],
                        'Scoring': game_config['scoring'],
                        'Stats': '{}',
                        'Aggregate Score': '',
                        'Match Mode': 'Head-to-Head'
                    }
                    matches.append(match)
                    match_id += 1
    
    # Update max rounds based on the game with most rounds
    if matches:
        max_rounds = max([m['Leg Number'] for m in matches if m['Leg Number'] > 0], default=1)
        st.session_state.max_rounds = max(max_rounds, 1)
    
    return pd.DataFrame(matches)

def reshuffle_bracket(players_df):
    """Reshuffle the bracket - regroup players by game and age group"""
    if not st.session_state.tournament_active:
        return None, "No active tournament to reshuffle"
    
    # Get active players
    active_players = players_df[players_df['Status'] == 'Active']
    
    if len(active_players) < 2:
        return None, "Need at least 2 active players to reshuffle"
    
    # Generate new bracket with reshuffled pairings
    new_bracket = generate_flexible_bracket(active_players)
    
    if new_bracket.empty:
        return None, "Could not generate bracket"
    
    return new_bracket, "Bracket reshuffled successfully!"

def _pair_legs(matches_df, match_id):
    """Return all legs (rows) that belong to the same pairing as match_id."""
    row = matches_df[matches_df['Match ID'] == match_id]
    if row.empty:
        return matches_df.iloc[0:0]
    row = row.iloc[0]
    if row['Player 2'] in ('BYE', 'INDIVIDUAL'):
        return row.to_frame().T
    pair = {row['Player 1'], row['Player 2']}
    same = matches_df[
        (matches_df['Game'] == row['Game']) &
        (matches_df['Age Group'] == row['Age Group']) &
        (matches_df['Player 1'].isin(pair)) &
        (matches_df['Player 2'].isin(pair))
    ]
    return same

def calculate_aggregate_score(matches_df, match_id):
    """Aggregate score (P1-P2 goals) across every leg of the same pairing"""
    legs = _pair_legs(matches_df, match_id)
    if len(legs) < 2:
        return None
    base_p1 = legs.iloc[0]['Player 1']
    totals = {base_p1: 0, 'other': 0}
    counted = 0
    for _, leg in legs.iterrows():
        if leg['Status'] != 'Completed' or not leg['Score'] or leg['Score'] == 'BYE':
            continue
        m = re.match(r'^\s*(\d+)\s*[-:]\s*(\d+)\s*$', str(leg['Score']))
        if not m:
            continue
        s1, s2 = int(m.group(1)), int(m.group(2))
        # scores are entered as Player1-Player2 of THAT leg's row
        if leg['Player 1'] == base_p1:
            totals[base_p1] += s1; totals['other'] += s2
        else:
            totals[base_p1] += s2; totals['other'] += s1
        counted += 1
    if counted == 0:
        return None
    return f"{totals[base_p1]}-{totals['other']}"

def update_match_aggregate(match_id):
    """Write the aggregate score onto every leg of the pairing"""
    bracket = st.session_state.bracket
    legs = _pair_legs(bracket, match_id)
    if len(legs) > 1:
        aggregate = calculate_aggregate_score(bracket, match_id)
        if aggregate:
            for idx in legs.index:
                st.session_state.bracket.loc[idx, 'Aggregate Score'] = aggregate

# ---------- BRACKET REBALANCING FUNCTION ----------
def rebalance_bracket():
    """Rebalance the bracket - fix duplicate entries and odd player counts"""
    if st.session_state.bracket.empty:
        return False, "No bracket to rebalance"
    
    # Get active players
    active_players = st.session_state.players[st.session_state.players['Status'] == 'Active']
    
    if len(active_players) < 2:
        return False, "Need at least 2 active players to rebalance"
    
    # Regenerate bracket with clean data
    new_bracket = generate_flexible_bracket(active_players)
    
    if new_bracket.empty:
        return False, "Could not generate rebalanced bracket"
    
    return True, new_bracket

def fix_duplicate_players():
    """Detect players who appear in more than one pairing within the same game/age group.
    (Several legs of the SAME pairing are normal and are never treated as duplicates.)"""
    if st.session_state.bracket.empty:
        return False, "No bracket to fix"

    df = st.session_state.bracket
    h2h = df[~df['Player 2'].isin(['BYE', 'INDIVIDUAL'])]
    opponents = {}
    for _, row in h2h.iterrows():
        for me, opp in ((row['Player 1'], row['Player 2']), (row['Player 2'], row['Player 1'])):
            opponents.setdefault((me, row['Game'], row['Age Group']), set()).add(opp)

    duplicated = [k for k, v in opponents.items() if len(v) > 1]
    if not duplicated:
        return True, "No duplicate issues found"

    completed = len(df[df['Status'] == 'Completed'])
    if completed > 0:
        return False, (f"Found {len(duplicated)} player(s) in more than one pairing, but {completed} matches are "
                       f"already completed. Reset or reshuffle the tournament to rebuild safely.")

    active_players = st.session_state.players[st.session_state.players['Status'] == 'Active']
    new_bracket = generate_flexible_bracket(active_players)
    if not new_bracket.empty:
        st.session_state.bracket = new_bracket
        return True, f"Fixed {len(duplicated)} duplicate pairing(s) and regenerated the bracket"
    return False, "Could not regenerate bracket"

# ---------- PLAYER BALANCE CHECKER ----------
def check_player_balance():
    """Check if all game/age group combinations have even numbers and suggest fixes"""
    active_players = st.session_state.players[st.session_state.players['Status'] == 'Active']
    
    if active_players.empty:
        return {
            'balanced': False,
            'message': "❌ No active players found. Add some players first!",
            'suggestions': [],
            'total_players': 0,
            'total_groups': 0,
            'perfect_groups': 0,
            'odd_groups': 0,
            'group_details': []
        }
    
    # Group players by Game and Age Group
    groups = active_players.groupby(['Game', 'Age Group'])
    
    suggestions = []
    total_odd_groups = 0
    perfect_groups = 0
    
    for (game, age_group), group in groups:
        count = len(group)
        game_config = get_game_config(game)
        is_individual = game_config.get('individual_scoring', False)
        
        # For individual scoring games, any number works (no pairing needed)
        if is_individual:
            perfect_groups += 1
            continue
        
        if count % 2 != 0:
            total_odd_groups += 1
            # Calculate how many more players needed
            needed = 1 if count % 2 == 1 else 0
            next_even = count + 1
            
            # Get player names for reference
            player_names = group['Name'].tolist()
            
            suggestions.append({
                'game': game,
                'age_group': age_group,
                'current_count': count,
                'needed': needed,
                'next_even': next_even,
                'players': player_names,
                'icon': '🟡' if count == 1 else '🔴'
            })
        else:
            perfect_groups += 1
    
    # Check if any age group has less than 2 players total (for non-individual games)
    age_groups = active_players.groupby('Age Group')
    for age_group, group in age_groups:
        total_in_age = len(group)
        if total_in_age < 2:
            # Check if all players in this age group are from individual games
            games_in_age = group['Game'].unique()
            all_individual = all(get_game_config(g).get('individual_scoring', False) for g in games_in_age)
            if not all_individual:
                suggestions.append({
                    'game': 'ALL',
                    'age_group': age_group,
                    'current_count': total_in_age,
                    'needed': 2 - total_in_age,
                    'next_even': 2,
                    'players': group['Name'].tolist(),
                    'icon': '🔴'
                })
    
    return {
        'balanced': len(suggestions) == 0,
        'total_players': len(active_players),
        'total_groups': len(groups),
        'perfect_groups': perfect_groups,
        'odd_groups': total_odd_groups,
        'message': get_balance_message(len(suggestions), len(active_players)),
        'suggestions': suggestions,
        'group_details': groups
    }

def get_balance_message(issue_count, total_players):
    """Generate a user-friendly balance message"""
    if issue_count == 0:
        if total_players == 0:
            return "⚠️ No active players! Add players to start."
        return "✅ Perfectly balanced! All game/age groups have even numbers."
    elif issue_count == 1:
        return "ℹ️ Found 1 group with an odd number of players."
    else:
        return f"ℹ️ Found {issue_count} groups with odd numbers of players."

def render_balance_dashboard():
    """Render a nice dashboard showing player balance"""
    balance_data = check_player_balance()
    
    # Show summary cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Total Players", balance_data.get('total_players', 0))
    col2.metric("🎮 Game Groups", balance_data.get('total_groups', 0))
    col3.metric("✅ Balanced Groups", balance_data.get('perfect_groups', 0))
    col4.metric("⚠️ Unbalanced", balance_data.get('odd_groups', 0))
    
    st.divider()
    
    # Show balance status
    if balance_data.get('balanced', False):
        st.success("✅ All game/age groups are perfectly balanced!")
        st.info(f"🎯 Total of {balance_data.get('total_players', 0)} players across {balance_data.get('total_groups', 0)} game groups")
    else:
        st.warning("⚠️ Some game/age groups need more players to be balanced")
        
        # Show detailed suggestions
        if balance_data.get('suggestions'):
            st.subheader("📋 Balance Recommendations")
            
            for suggestion in balance_data['suggestions']:
                with st.expander(f"{suggestion['icon']} {suggestion['game']} - {suggestion['age_group']}", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("👤 Current Players", suggestion['current_count'])
                    with col2:
                        st.metric("✅ Need", suggestion['needed'], delta=f"+{suggestion['needed']}")
                    with col3:
                        st.metric("📊 Target", suggestion['next_even'])
                    
                    if suggestion['players']:
                        st.write(f"**Current players:** {', '.join(suggestion['players'])}")
                    
                    # Show recommended player types to add
                    if suggestion['needed'] > 0:
                        st.info(f"💡 Add {suggestion['needed']} more {suggestion['age_group']} player(s) playing {suggestion['game']}")
                        
                        # Quick add button
                        if st.button(f"➕ Quick Add {suggestion['age_group']} Player for {suggestion['game']}", key=f"quick_add_{suggestion['game']}_{suggestion['age_group']}"):
                            st.session_state.suggested_game = suggestion['game']
                            st.session_state.suggested_age = suggestion['age_group']
                            st.session_state['_suggestion_pending'] = True
                            st.rerun()

# ---------- TOURNAMENT HISTORY FUNCTIONS ----------
def save_tournament_history():
    """Save the current tournament to history"""
    if st.session_state.bracket.empty:
        return False, "No tournament to save"
    
    tournament_data = {
        "id": f"T{len(st.session_state.tournament_history) + 1:04d}",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "matches": st.session_state.bracket.to_dict('records'),
        "players": st.session_state.players.to_dict('records'),
        "champions": copy.deepcopy(st.session_state.tournament_champions),
        "live_scores": st.session_state.live_scores.to_dict('records'),
        "total_matches": len(st.session_state.bracket),
        "completed_matches": len(st.session_state.bracket[st.session_state.bracket['Status'] == 'Completed'])
    }
    
    st.session_state.tournament_history.append(tournament_data)
    st.session_state.past_tournaments[tournament_data["id"]] = tournament_data
    
    return True, f"Tournament {tournament_data['id']} saved successfully!"

def delete_tournament_history(tournament_id):
    """Delete a tournament from history"""
    if tournament_id in st.session_state.past_tournaments:
        del st.session_state.past_tournaments[tournament_id]
        # Also remove from list if present
        st.session_state.tournament_history = [
            t for t in st.session_state.tournament_history 
            if t.get("id") != tournament_id
        ]
        return True, f"Tournament {tournament_id} deleted successfully!"
    return False, "Tournament not found"

def load_tournament_history(tournament_id):
    """Load a tournament from history"""
    if tournament_id in st.session_state.past_tournaments:
        data = st.session_state.past_tournaments[tournament_id]
        st.session_state.bracket = pd.DataFrame(data["matches"])
        st.session_state.players = pd.DataFrame(data["players"])
        st.session_state.tournament_champions = data["champions"]
        st.session_state.live_scores = pd.DataFrame(data["live_scores"])
        st.session_state.tournament_active = True
        return True, f"Tournament {tournament_id} loaded successfully!"
    return False, "Tournament not found"

# ---------- PDF EXPORT FUNCTIONS ----------
def generate_pdf_report():
    """Generate a detailed PDF report of the tournament with recruiter-focused information and match details"""
    if st.session_state.bracket.empty:
        return None
    
    # Create a temporary file for the PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        pdf_path = tmp_file.name
    
    doc = SimpleDocTemplate(pdf_path, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.blue,
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.darkgrey,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.darkgreen,
        spaceAfter=12,
        spaceBefore=20
    )
    
    stat_style = ParagraphStyle(
        'StatStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6
    )
    
    # Title
    story.append(Paragraph("🎮 RAW RHYTHM RUMBLE - TOURNAMENT REPORT", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
    story.append(Spacer(1, 20))
    
    # ========== 1. TOURNAMENT OVERVIEW ==========
    story.append(Paragraph("📊 TOURNAMENT OVERVIEW", section_title_style))
    story.append(Spacer(1, 5))
    
    total_matches = len(st.session_state.bracket)
    completed_matches = len(st.session_state.bracket[st.session_state.bracket['Status'] == 'Completed'])
    pending_matches = len(st.session_state.bracket[st.session_state.bracket['Status'] == 'Pending'])
    total_players = len(st.session_state.players)
    active_players = len(st.session_state.players[st.session_state.players['Status'] == 'Active'])
    
    overview_data = [
        ["Metric", "Value"],
        ["Total Matches", str(total_matches)],
        ["Completed Matches", str(completed_matches)],
        ["Pending Matches", str(pending_matches)],
        ["Completion Rate", f"{round((completed_matches/total_matches)*100 if total_matches > 0 else 0)}%"],
        ["Total Players", str(total_players)],
        ["Active Players", str(active_players)],
        ["Tournament Status", "Active" if st.session_state.tournament_active else "Completed"]
    ]
    
    overview_table = Table(overview_data, colWidths=[2*inch, 2*inch])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
        ('BACKGROUND', (0, 1), (1, -1), colors.beige),
        ('GRID', (0, 0), (1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (1, -1), 11)
    ]))
    story.append(overview_table)
    story.append(Spacer(1, 20))
    
    # ========== 2. GAME SUMMARY ==========
    story.append(Paragraph("🎯 GAME SUMMARY BY TYPE", section_title_style))
    story.append(Spacer(1, 5))
    
    game_summary_data = [["Game", "Mode", "Players", "Matches", "Completed"]]
    
    for game in st.session_state.players['Game'].unique():
        game_players = st.session_state.players[st.session_state.players['Game'] == game]
        game_matches = st.session_state.bracket[st.session_state.bracket['Game'] == game]
        game_completed = game_matches[game_matches['Status'] == 'Completed']
        game_config = get_game_config(game)
        mode = "Individual" if game_config.get('individual_scoring', False) else "Head-to-Head"
        
        game_summary_data.append([
            game,
            mode,
            str(len(game_players)),
            str(len(game_matches)),
            str(len(game_completed))
        ])
    
    game_summary_table = Table(game_summary_data, colWidths=[1.8*inch, 1.2*inch, 1*inch, 1*inch, 1*inch])
    game_summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10)
    ]))
    story.append(game_summary_table)
    story.append(Spacer(1, 20))
    
    # ========== 3. CHAMPIONS ==========
    story.append(Paragraph("🏆 TOURNAMENT CHAMPIONS", section_title_style))
    story.append(Spacer(1, 5))
    
    champions_found = False
    for game, data in st.session_state.tournament_champions.items():
        if data['champion']:
            champions_found = True
            champion_text = f"<b>{game}</b>: {data['champion']}"
            if data.get('runner_up'):
                champion_text += f" (Runner Up: {data['runner_up']})"
            story.append(Paragraph(champion_text, stat_style))
    
    if not champions_found:
        story.append(Paragraph("No champions have been crowned yet.", stat_style))
    
    story.append(Spacer(1, 20))
    
    # ========== 4. PLAYER PERFORMANCE STATISTICS ==========
    story.append(Paragraph("👥 PLAYER PERFORMANCE STATISTICS", section_title_style))
    story.append(Spacer(1, 5))
    
    # Get all players with their stats
    player_stats = []
    for idx, player in st.session_state.players.iterrows():
        wins = int(player.get('Wins', 0))
        losses = int(player.get('Losses', 0))
        total = wins + losses
        win_rate = round((wins / total * 100) if total > 0 else 0)
        
        # Get player's matches
        player_matches = st.session_state.bracket[
            (st.session_state.bracket['Player 1'] == player['Name']) | 
            (st.session_state.bracket['Player 2'] == player['Name'])
        ]
        matches_played = len(player_matches)
        
        # Get player's game
        game = player.get('Game', 'N/A')
        
        # Get potential
        potential = int(player.get('Potential', 0))
        potential_level = get_potential_level(potential)
        
        player_stats.append({
            'Name': player['Name'],
            'Game': game,
            'Age Group': player.get('Age Group', 'N/A'),
            'Wins': wins,
            'Losses': losses,
            'Win Rate': win_rate,
            'Matches': matches_played,
            'Potential': potential,
            'Potential Level': potential_level,
            'Highlighted': '⭐' if player.get('Highlighted', False) else ''
        })
    
    # Sort by potential (highest first)
    player_stats.sort(key=lambda x: x['Potential'], reverse=True)
    
    # Create player stats table
    player_table_data = [["Name", "Game", "Age", "W/L", "Win %", "Matches", "Potential", "Level", "⭐"]]
    
    for stat in player_stats[:30]:  # Show top 30 players
        player_table_data.append([
            stat['Name'],
            stat['Game'],
            stat['Age Group'],
            f"{stat['Wins']}/{stat['Losses']}",
            f"{stat['Win Rate']}%",
            str(stat['Matches']),
            f"{stat['Potential']}%",
            stat['Potential Level'].replace('🌟', '').replace('⭐', '').strip(),
            stat['Highlighted']
        ])
    
    if len(player_stats) > 30:
        player_table_data.append(["... and more", "", "", "", "", "", "", "", ""])
    
    player_table = Table(player_table_data, colWidths=[1.2*inch, 1*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1.2*inch, 0.5*inch])
    player_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8)
    ]))
    story.append(player_table)
    story.append(Spacer(1, 20))
    
    # ========== 5. TOP PERFORMERS ==========
    story.append(Paragraph("🌟 TOP PERFORMERS BY CATEGORY", section_title_style))
    story.append(Spacer(1, 5))
    
    # Top 5 by wins
    top_winners = sorted(player_stats, key=lambda x: x['Wins'], reverse=True)[:5]
    story.append(Paragraph("<b>🏆 Most Wins:</b>", stat_style))
    for i, player in enumerate(top_winners, 1):
        if player['Wins'] > 0:
            story.append(Paragraph(f"  {i}. {player['Name']} - {player['Wins']} wins ({player['Game']})", stat_style))
    
    # Top 5 by win rate (minimum 3 matches)
    top_win_rate = sorted([p for p in player_stats if p['Matches'] >= 3], key=lambda x: x['Win Rate'], reverse=True)[:5]
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>📈 Best Win Rate (min 3 matches):</b>", stat_style))
    for i, player in enumerate(top_win_rate, 1):
        story.append(Paragraph(f"  {i}. {player['Name']} - {player['Win Rate']}% ({player['Wins']}-{player['Losses']})", stat_style))
    
    # Top 5 by potential
    top_potential = sorted(player_stats, key=lambda x: x['Potential'], reverse=True)[:5]
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>⭐ Highest Potential:</b>", stat_style))
    for i, player in enumerate(top_potential, 1):
        story.append(Paragraph(f"  {i}. {player['Name']} - {player['Potential']}% ({player['Potential Level']})", stat_style))
    
    # Elite prospects (potential >= 80)
    elite_players = [p for p in player_stats if p['Potential'] >= 80]
    if elite_players:
        story.append(Spacer(1, 5))
        story.append(Paragraph("<b>🌟 Elite Prospects (80%+ potential):</b>", stat_style))
        for player in elite_players:
            story.append(Paragraph(f"  • {player['Name']} - {player['Game']} ({player['Potential']}%) - {player['Wins']} wins", stat_style))
    
    story.append(Spacer(1, 20))
    
    # ========== 6. MATCH DETAILS ==========
    story.append(Paragraph("📋 MATCH RESULTS", section_title_style))
    story.append(Spacer(1, 5))
    
    # Get all matches sorted by game
    matches_by_game = st.session_state.bracket.sort_values(['Game', 'Match ID'])
    
    # Show matches per game with full details
    for game in matches_by_game['Game'].unique():
        game_matches = matches_by_game[matches_by_game['Game'] == game]
        game_config = get_game_config(game)
        is_individual = game_config.get('individual_scoring', False)
        
        story.append(Paragraph(f"<b>{game}</b> ({'Individual' if is_individual else 'Head-to-Head'})", ParagraphStyle(
            'GameHeader',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.darkgreen,
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )))
        
        # Calculate game statistics
        total_games = len(game_matches)
        completed_games = len(game_matches[game_matches['Status'] == 'Completed'])
        completion_rate = round((completed_games / total_games * 100) if total_games > 0 else 0)
        
        # Show game stats header
        game_stats_data = [
            ["Total Matches", "Completed", "Completion Rate"],
            [str(total_games), str(completed_games), f"{completion_rate}%"]
        ]
        game_stats_table = Table(game_stats_data, colWidths=[2*inch, 2*inch, 2*inch])
        game_stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10)
        ]))
        story.append(game_stats_table)
        story.append(Spacer(1, 10))
        
        if is_individual:
            # Individual scoring match table with full details
            match_data = [["Match", "Player", "Score", "Status", "Leg", "Round", "Station"]]
            
            for idx, row in game_matches.iterrows():
                score = row['Score'] if row['Score'] else 'Pending'
                status = row['Status']
                leg = row.get('Leg', 'N/A')
                round_num = row.get('Round', 'N/A')
                station = row.get('Station', 'N/A')
                
                status_display = "✅ Completed" if status == 'Completed' else "⏳ Pending"
                
                match_data.append([
                    row['Leg'],
                    row['Player 1'],
                    score,
                    status_display,
                    leg,
                    round_num,
                    station
                ])
            
            if len(match_data) > 1:
                match_table = Table(match_data, colWidths=[1*inch, 1.5*inch, 1*inch, 1.2*inch, 1*inch, 1*inch, 1.2*inch])
                match_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8)
                ]))
                story.append(match_table)
            else:
                story.append(Paragraph("No matches in this game yet.", stat_style))
        else:
            # Head-to-head match table with full details
            match_data = [["ID", "Player 1", "Player 2", "Score", "Winner", "Status", "Leg", "Round", "Station"]]
            
            for idx, row in game_matches.iterrows():
                score = row['Score'] if row['Score'] else 'Pending'
                winner = row['Winner'] if row['Winner'] else '—'
                status = row['Status']
                leg = row.get('Leg', 'N/A')
                round_num = row.get('Round', 'N/A')
                station = row.get('Station', 'N/A')
                
                if status == 'Completed':
                    match_data.append([
                        row['Match ID'],
                        row['Player 1'],
                        row['Player 2'],
                        score,
                        f"🏆 {winner}",
                        "✅ Completed",
                        leg,
                        round_num,
                        station
                    ])
                else:
                    match_data.append([
                        row['Match ID'],
                        row['Player 1'],
                        row['Player 2'],
                        score,
                        "—",
                        "⏳ Pending",
                        leg,
                        round_num,
                        station
                    ])
            
            if len(match_data) > 1:
                match_table = Table(match_data, colWidths=[0.7*inch, 1*inch, 1*inch, 0.8*inch, 1*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
                match_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 7)
                ]))
                story.append(match_table)
            else:
                story.append(Paragraph("No matches in this game yet.", stat_style))
        
        story.append(Spacer(1, 15))
    
    # ========== 7. MATCH STATISTICS SUMMARY ==========
    story.append(Paragraph("📊 MATCH STATISTICS SUMMARY", section_title_style))
    story.append(Spacer(1, 5))
    
    # Compile all match stats
    match_stats_data = [["Game", "Total", "Completed", "Completion %", "Players", "Wins Recorded"]]
    
    for game in st.session_state.players['Game'].unique():
        game_matches = st.session_state.bracket[st.session_state.bracket['Game'] == game]
        total = len(game_matches)
        completed = len(game_matches[game_matches['Status'] == 'Completed'])
        completion_pct = round((completed / total * 100) if total > 0 else 0)
        players = len(st.session_state.players[st.session_state.players['Game'] == game])
        
        # Count wins recorded
        wins = len(game_matches[game_matches['Status'] == 'Completed']['Winner'].dropna())
        
        match_stats_data.append([
            game,
            str(total),
            str(completed),
            f"{completion_pct}%",
            str(players),
            str(wins)
        ])
    
    match_stats_table = Table(match_stats_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1.2*inch])
    match_stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9)
    ]))
    story.append(match_stats_table)
    
    story.append(Spacer(1, 20))
    
    # ========== 8. RECRUITER NOTES ==========
    story.append(Paragraph("📝 RECRUITER NOTES", section_title_style))
    story.append(Spacer(1, 5))
    
    # Find players with recruiter notes
    players_with_notes = st.session_state.players[
        st.session_state.players['Recruiter Notes'].notna() & 
        (st.session_state.players['Recruiter Notes'] != '')
    ]
    
    if not players_with_notes.empty:
        notes_data = [["Player", "Game", "Potential", "Notes"]]
        
        for idx, row in players_with_notes.iterrows():
            notes_data.append([
                row['Name'],
                row['Game'],
                f"{int(row['Potential'])}%",
                row['Recruiter Notes']
            ])
        
        notes_table = Table(notes_data, colWidths=[1.2*inch, 1*inch, 0.8*inch, 3*inch])
        notes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9)
        ]))
        story.append(notes_table)
    else:
        story.append(Paragraph("No recruiter notes have been added yet.", stat_style))
    
    story.append(Spacer(1, 20))
    
    # ========== 9. SUMMARY STATISTICS ==========
    story.append(Paragraph("📊 SUMMARY STATISTICS", section_title_style))
    story.append(Spacer(1, 5))
    
    # Calculate additional stats
    unique_winners = len(st.session_state.bracket[st.session_state.bracket['Status'] == 'Completed']['Winner'].unique()) if not st.session_state.bracket.empty else 0
    total_teams = len(st.session_state.players['Game'].unique())
    avg_age = st.session_state.players['Age'].mean() if not st.session_state.players.empty else 0
    total_wins = st.session_state.players['Wins'].sum() if not st.session_state.players.empty else 0
    
    summary_stats = [
        ["Statistic", "Value"],
        ["Total Games", str(total_teams)],
        ["Unique Winners", str(unique_winners)],
        ["Average Player Age", f"{avg_age:.1f}"],
        ["Total Wins Recorded", str(int(total_wins))],
        ["Highlighted Players", str(len(st.session_state.players[st.session_state.players['Highlighted'] == True]))]
    ]
    
    summary_table = Table(summary_stats, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (1, 0), 10),
        ('BACKGROUND', (0, 1), (1, -1), colors.beige),
        ('GRID', (0, 0), (1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (1, -1), 10)
    ]))
    story.append(summary_table)
    
    # ========== FOOTER ==========
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Raw Rhythm Rumble v10.6 - Comprehensive Tournament Report", footer_style))
    story.append(Paragraph(f"Report generated on {datetime.now().strftime('%Y-%m-%d at %H:%M')}", footer_style))
    story.append(Paragraph("For recruiting inquiries, please contact the tournament administrator.", footer_style))
    
    # Build the PDF
    doc.build(story)
    
    return pdf_path

def generate_live_scoreboard_pdf():
    """Generate a detailed PDF of the live scoreboard with match details"""
    if st.session_state.live_scores.empty:
        return None
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        pdf_path = tmp_file.name
    
    doc = SimpleDocTemplate(pdf_path, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.blue,
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.darkgreen,
        spaceAfter=12,
        spaceBefore=20
    )
    
    story.append(Paragraph("🎮 Live Scoreboard Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Group scores by game
    games = st.session_state.live_scores['Game'].unique()
    
    for game in games:
        game_scores = st.session_state.live_scores[st.session_state.live_scores['Game'] == game]
        
        story.append(Paragraph(f"🎯 {game}", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        # ===== Scoreboard =====
        story.append(Paragraph("🏆 Scoreboard", section_title_style))
        
        # Get all players and their win counts for this game
        winners = game_scores['Winner'].value_counts()
        
        scoreboard_data = [["Rank", "Player", "Wins", "Matches Played"]]
        
        for rank, (player, wins) in enumerate(winners.items(), 1):
            matches_played = len(game_scores[
                (game_scores['Player 1'] == player) | 
                (game_scores['Player 2'] == player)
            ])
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
            scoreboard_data.append([medal, player, str(wins), str(matches_played)])
        
        if len(scoreboard_data) > 1:
            scoreboard_table = Table(scoreboard_data, colWidths=[0.8*inch, 2*inch, 1*inch, 1.5*inch])
            scoreboard_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(scoreboard_table)
        else:
            story.append(Paragraph("No scores recorded for this game yet.", styles['Normal']))
        
        story.append(Spacer(1, 15))
        
        # ===== Match Details =====
        story.append(Paragraph("📋 Match Details", section_title_style))
        
        match_data = [["Time", "Player 1", "Player 2", "Score", "Winner", "Station", "Age Group"]]
        
        for idx, row in game_scores.iterrows():
            match_data.append([
                row['Timestamp'],
                row['Player 1'],
                row['Player 2'] if row['Player 2'] != 'INDIVIDUAL' else 'Solo',
                row['Score'],
                f"🏆 {row['Winner']}",
                row['Station'],
                row['Age Group']
            ])
        
        if len(match_data) > 1:
            match_table = Table(match_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 0.8*inch, 1.2*inch, 1*inch, 1*inch])
            match_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8)
            ]))
            story.append(match_table)
        
        story.append(Spacer(1, 20))
    
    # ===== Summary =====
    story.append(Paragraph("📊 Summary Statistics", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    total_matches = len(st.session_state.live_scores)
    unique_players = len(st.session_state.live_scores['Winner'].unique())
    
    summary_data = [
        ["Metric", "Value"],
        ["Total Matches", str(total_matches)],
        ["Unique Winners", str(unique_players)],
        ["Games Played", str(len(games))]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
        ('BACKGROUND', (0, 1), (1, -1), colors.beige),
        ('GRID', (0, 0), (1, -1), 1, colors.black)
    ]))
    story.append(summary_table)
    
    # ========== FOOTER ==========
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Raw Rhythm Rumble v10.6 - Live Scoreboard Report", footer_style))
    story.append(Paragraph(f"Report generated on {datetime.now().strftime('%Y-%m-%d at %H:%M')}", footer_style))
    
    # Build the PDF
    doc.build(story)
    
    return pdf_path

# ---------- STATION MANAGEMENT FUNCTIONS ----------
def add_station(station_name, capacity=8):
    """Add a new gaming station"""
    if station_name in st.session_state.station_config:
        return False, f"Station '{station_name}' already exists"
    
    st.session_state.station_config[station_name] = {
        "capacity": capacity,
        "current": 0
    }
    return True, f"Station '{station_name}' added successfully!"

def remove_station(station_name):
    """Remove a gaming station"""
    if station_name not in st.session_state.station_config:
        return False, f"Station '{station_name}' not found"
    
    # Check if station has players
    players_at_station = st.session_state.players[
        st.session_state.players['Station'] == station_name
    ]
    if not players_at_station.empty:
        return False, f"Cannot remove station with {len(players_at_station)} players. Move players first."
    
    del st.session_state.station_config[station_name]
    return True, f"Station '{station_name}' removed successfully!"

# ---------- DATA TYPE FIX FUNCTION ----------
def fix_dataframe_types(df):
    """Ensure numeric columns have proper dtypes"""
    if df.empty:
        return df
    
    # Convert numeric columns
    numeric_cols = ['Age', 'Wins', 'Losses', 'Potential']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Convert boolean columns
    if 'Highlighted' in df.columns:
        df['Highlighted'] = df['Highlighted'].astype(bool)
    
    return df

def fix_all_data_types():
    """Fix data types for all dataframes in session state"""
    if not st.session_state.players.empty:
        st.session_state.players = fix_dataframe_types(st.session_state.players)
    
    if not st.session_state.bracket.empty:
        # Convert numeric columns in bracket
        for col in ['Match ID']:
            if col in st.session_state.bracket.columns:
                st.session_state.bracket[col] = st.session_state.bracket[col].astype(str)

# Call this after any data load or initialization
fix_all_data_types()

# ---------- HELPER FUNCTIONS ----------
def get_age_group(age):
    """Get age group based on age"""
    if age <= 12: return "Under 12"
    elif age <= 17: return "Teen"
    elif age <= 25: return "Young Adult"
    elif age <= 35: return "Adult"
    else: return "Senior"

def login(username, password):
    """Authenticate user with hashed password"""
    if username in USERS:
        if verify_password(USERS[username]["password"], password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.user_role = USERS[username]["role"]
            st.session_state.user_name = USERS[username]["name"]
            
            if "stations" in USERS[username]:
                st.session_state.user_stations = USERS[username]["stations"]
            else:
                st.session_state.user_stations = ["All"]
            
            check_notifications()
            return True
    return False

def calculate_potential(player_row):
    """Calculate player potential score with proper type handling"""
    wins = int(player_row.get('Wins', 0))
    losses = int(player_row.get('Losses', 0))
    total = wins + losses
    
    if total == 0:
        win_score = 25
    else:
        win_score = min((wins / total) * 50, 50)
    
    age = int(player_row.get('Age', 25))
    if age <= 16:
        age_score = 30
    elif age <= 18:
        age_score = 25
    elif age <= 21:
        age_score = 20
    elif age <= 25:
        age_score = 15
    elif age <= 30:
        age_score = 10
    else:
        age_score = 5
    
    if total > 10:
        experience_bonus = 10
    elif total > 5:
        experience_bonus = 5
    else:
        experience_bonus = 0
    
    potential = min(round(win_score + age_score + experience_bonus), 100)
    return potential

def get_potential_color(potential):
    """Get color based on potential score"""
    if potential >= 80:
        return "#00ff00"
    elif potential >= 70:
        return "#90ee90"
    elif potential >= 60:
        return "#ffff00"
    else:
        return "#ffcccc"

def get_potential_level(potential):
    """Get potential level description"""
    if potential >= 80:
        return "🌟 Elite Prospect"
    elif potential >= 70:
        return "⭐ High Potential"
    elif potential >= 60:
        return "📈 Developing"
    else:
        return "📊 Needs Experience"

def update_all_potentials():
    """Update potential scores for all players"""
    if st.session_state.players.empty:
        return
    
    # Ensure proper types first
    st.session_state.players = fix_dataframe_types(st.session_state.players)
    
    for idx, row in st.session_state.players.iterrows():
        potential = calculate_potential(row)
        st.session_state.players.loc[idx, 'Potential'] = potential
        
        if row['Name'] in st.session_state.highlight_overrides:
            continue  # someone removed this highlight on purpose - don't re-add it
        reason = str(row.get('Highlight Reason', '') or '')
        manual = reason.startswith("Manual")
        if potential >= 80 and row['Status'] == 'Active':
            st.session_state.players.loc[idx, 'Highlighted'] = True
            if not manual:
                st.session_state.players.loc[idx, 'Highlight Reason'] = f"Auto-Highlight: Elite Prospect ({potential}%)"
        elif potential >= 70 and row['Status'] == 'Active':
            st.session_state.players.loc[idx, 'Highlighted'] = True
            if not manual:
                st.session_state.players.loc[idx, 'Highlight Reason'] = f"Auto-Highlight: High Potential ({potential}%)"

def add_live_score(match_id, player1, player2, score, winner, station, age_group, game):
    """Add a live score entry"""
    new_score = pd.DataFrame([{
        'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Station': station,
        'Match ID': match_id,
        'Player 1': player1,
        'Player 2': player2,
        'Score': score,
        'Winner': winner,
        'Recorded By': st.session_state.user_name,
        'Age Group': age_group,
        'Game': game
    }])
    
    st.session_state.live_scores = pd.concat([st.session_state.live_scores, new_score], ignore_index=True)
    st.session_state.last_update = datetime.now()

def create_help_request(station, issue_type, message, requested_by):
    """Create a help request"""
    request_id = f"REQ{len(st.session_state.help_requests) + 1:04d}"
    
    new_request = pd.DataFrame([{
        'Request ID': request_id,
        'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Station': station,
        'Requested By': requested_by,
        'Issue Type': issue_type,
        'Message': message,
        'Status': 'Pending',
        'Admin Response': '',
        'Resolved By': '',
        'Resolved At': ''
    }])
    
    st.session_state.help_requests = pd.concat([st.session_state.help_requests, new_request], ignore_index=True)
    
    create_notification(
        'help_request',
        f"🆘 Help Request from {station}: {issue_type}",
        request_id,
        'admin'
    )
    
    return request_id

def create_notification(notification_type, message, related_request, target_role):
    """Create a notification"""
    notification_id = f"N{len(st.session_state.notifications) + 1:04d}"
    
    new_notification = pd.DataFrame([{
        'Notification ID': notification_id,
        'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Type': notification_type,
        'Message': message,
        'Related Request': related_request,
        'Read': False,
        'Target Role': target_role
    }])
    
    st.session_state.notifications = pd.concat([st.session_state.notifications, new_notification], ignore_index=True)

def check_notifications():
    """Check for unread notifications"""
    if st.session_state.user_role == 'admin':
        unread = len(st.session_state.notifications[
            (st.session_state.notifications['Read'] == False) &
            (st.session_state.notifications['Target Role'] == 'admin')
        ])
        st.session_state.unread_notifications = unread

def mark_notification_read(notification_id):
    """Mark a notification as read"""
    idx = st.session_state.notifications[
        st.session_state.notifications['Notification ID'] == notification_id
    ].index[0]
    st.session_state.notifications.loc[idx, 'Read'] = True

def resolve_help_request(request_id, admin_response, resolved_by):
    """Resolve a help request"""
    idx = st.session_state.help_requests[
        st.session_state.help_requests['Request ID'] == request_id
    ].index[0]
    
    st.session_state.help_requests.loc[idx, 'Status'] = 'Resolved'
    st.session_state.help_requests.loc[idx, 'Admin Response'] = admin_response
    st.session_state.help_requests.loc[idx, 'Resolved By'] = resolved_by
    st.session_state.help_requests.loc[idx, 'Resolved At'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def update_station_counts():
    """Update current player counts for all stations"""
    for station in st.session_state.station_config.keys():
        count = len(st.session_state.players[
            (st.session_state.players['Station'] == station) &
            (st.session_state.players['Status'] == 'Active')
        ])
        st.session_state.station_config[station]['current'] = count

def get_station_status(station):
    """Get station status based on current load"""
    config = st.session_state.station_config.get(station, {"capacity": 8, "current": 0})
    current = config['current']
    capacity = config['capacity']
    
    if current < capacity * 0.5:
        return "under", "🟡 Under capacity"
    elif current > capacity:
        return "over", "🔴 Over capacity"
    else:
        return "balanced", "🟢 Balanced"

def balance_players_across_stations():
    """Auto-balance players across stations"""
    update_station_counts()
    
    overloaded = []
    underloaded = []
    
    for station, config in st.session_state.station_config.items():
        if config['current'] > config['capacity']:
            overloaded.append((station, config['current'] - config['capacity']))
        elif config['current'] < config['capacity'] * 0.5:
            underloaded.append((station, config['capacity'] - config['current']))
    
    if not overloaded or not underloaded:
        return "No balancing needed. All stations are balanced."
    
    moves_made = []
    
    for over_station, excess in overloaded:
        players_to_move = st.session_state.players[
            (st.session_state.players['Station'] == over_station) &
            (st.session_state.players['Status'] == 'Active')
        ].head(excess)
        
        for under_station, deficit in underloaded:
            if len(players_to_move) == 0:
                break
                
            for idx, player in players_to_move.iterrows():
                if len(st.session_state.players[
                    (st.session_state.players['Station'] == under_station) &
                    (st.session_state.players['Status'] == 'Active')
                ]) < st.session_state.station_config[under_station]['capacity']:
                    
                    st.session_state.players.loc[idx, 'Station'] = under_station
                    moves_made.append(f"{player['Name']}: {over_station} → {under_station}")
                    
                    st.session_state.station_config[over_station]['current'] -= 1
                    st.session_state.station_config[under_station]['current'] += 1
                    break
    
    if moves_made:
        return f"✅ Balanced! Moved {len(moves_made)} players:\n" + "\n".join(moves_made)
    else:
        return "No moves needed. All stations are balanced."

def move_player_to_station(player_name, target_station):
    """Move a specific player to a different station"""
    idx = st.session_state.players[
        st.session_state.players['Name'] == player_name
    ].index[0]
    
    old_station = st.session_state.players.loc[idx, 'Station']
    st.session_state.players.loc[idx, 'Station'] = target_station
    
    update_station_counts()
    
    return f"✅ Moved {player_name} from {old_station} to {target_station}"

def get_players_by_station(station):
    """Get all players at a specific station"""
    return st.session_state.players[
        st.session_state.players['Station'] == station
    ]

def save_data_to_json():
    """Save all data to JSON"""
    data = {
        "version": "10.6",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "players": st.session_state.players.to_dict('records'),
        "bracket": st.session_state.bracket.to_dict('records'),
        "live_scores": st.session_state.live_scores.to_dict('records'),
        "help_requests": st.session_state.help_requests.to_dict('records'),
        "notifications": st.session_state.notifications.to_dict('records'),
        "station_config": st.session_state.station_config,
        "tournament_active": st.session_state.tournament_active,
        "tournament_champions": st.session_state.tournament_champions,
        "tournament_history": st.session_state.tournament_history,
        "past_tournaments": st.session_state.past_tournaments,
        "game_legs_config": st.session_state.game_legs_config,
        "highlight_overrides": st.session_state.highlight_overrides
    }
    return json.dumps(data, indent=2, default=str)

def load_data_from_json(json_data):
    """Load data from JSON with type fixing"""
    try:
        data = json.loads(json_data)
        
        if data.get('players'):
            st.session_state.players = pd.DataFrame(data['players'])
            st.session_state.players = fix_dataframe_types(st.session_state.players)
        else:
            st.session_state.players = pd.DataFrame(columns=[
                'Name', 'Age', 'Age Group', 'Game', 'Station', 
                'Wins', 'Losses', 'Status', 'Potential', 'Highlighted', 
                'Recruiter Notes', 'Highlight Reason'
            ])
        
        if data.get('bracket'):
            st.session_state.bracket = pd.DataFrame(data['bracket'])
        else:
            st.session_state.bracket = empty_bracket()
        
        if data.get('live_scores'):
            st.session_state.live_scores = pd.DataFrame(data['live_scores'])
        else:
            st.session_state.live_scores = pd.DataFrame(columns=[
                'Timestamp', 'Station', 'Match ID', 'Player 1', 'Player 2', 
                'Score', 'Winner', 'Recorded By', 'Age Group', 'Game'
            ])
        
        if data.get('help_requests'):
            st.session_state.help_requests = pd.DataFrame(data['help_requests'])
        else:
            st.session_state.help_requests = pd.DataFrame(columns=[
                'Request ID', 'Timestamp', 'Station', 'Requested By', 
                'Issue Type', 'Message', 'Status', 'Admin Response', 
                'Resolved By', 'Resolved At'
            ])
        
        if data.get('notifications'):
            st.session_state.notifications = pd.DataFrame(data['notifications'])
        else:
            st.session_state.notifications = pd.DataFrame(columns=[
                'Notification ID', 'Timestamp', 'Type', 'Message', 
                'Related Request', 'Read', 'Target Role'
            ])
        
        if data.get('station_config'):
            st.session_state.station_config = data['station_config']
        
        if 'tournament_active' in data:
            st.session_state.tournament_active = data['tournament_active']
        
        if data.get('tournament_champions'):
            st.session_state.tournament_champions = data['tournament_champions']
        
        if data.get('tournament_history'):
            st.session_state.tournament_history = data['tournament_history']
        
        if data.get('past_tournaments'):
            st.session_state.past_tournaments = data['past_tournaments']
        
        if data.get('game_legs_config'):
            st.session_state.game_legs_config = data['game_legs_config']

        st.session_state.highlight_overrides = data.get('highlight_overrides', [])

        # Make sure a loaded bracket has every column the app expects (older saves lack some)
        for col in BRACKET_COLUMNS:
            if col not in st.session_state.bracket.columns:
                st.session_state.bracket[col] = '' if col not in ('Leg Number',) else 0
        st.session_state.bracket = st.session_state.bracket.fillna('')
        if not st.session_state.bracket.empty:
            st.session_state.max_rounds = int(max(pd.to_numeric(st.session_state.bracket['Leg Number'], errors='coerce').fillna(1).max(), 1))
        
        update_all_potentials()
        update_station_counts()
        fix_all_data_types()
        
        return True, "✅ Data loaded successfully!"
    except Exception as e:
        return False, f"❌ Error loading data: {str(e)}"

# ---------- ANALYTICS FUNCTIONS ----------
def create_performance_chart(players_df):
    """Create performance bar chart with type safety"""
    if players_df.empty:
        return None
    
    # Ensure numeric types
    players_df = fix_dataframe_types(players_df)
    
    # Get top 10 by wins (only if there are players with wins)
    players_with_wins = players_df[players_df['Wins'] > 0]
    
    if players_with_wins.empty:
        # Show all players sorted by potential instead
        top_players = players_df.nlargest(10, 'Potential')[['Name', 'Wins', 'Losses', 'Potential']]
    else:
        top_players = players_with_wins.nlargest(10, 'Wins')[['Name', 'Wins', 'Losses', 'Potential']]
    
    if top_players.empty:
        return None
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=top_players['Name'],
        y=top_players['Wins'],
        name='Wins',
        marker_color='#00ff00'
    ))
    
    fig.add_trace(go.Bar(
        x=top_players['Name'],
        y=top_players['Losses'],
        name='Losses',
        marker_color='#ff6b6b'
    ))
    
    fig.update_layout(
        title='Top 10 Players - Wins vs Losses',
        xaxis_title='Player',
        yaxis_title='Count',
        barmode='group',
        height=400,
        template='plotly_dark'
    )
    
    return fig

def create_age_distribution_chart(players_df):
    """Create age group distribution pie chart"""
    if players_df.empty:
        return None
    
    age_counts = players_df['Age Group'].value_counts()
    
    fig = go.Figure(data=[go.Pie(
        labels=age_counts.index,
        values=age_counts.values,
        hole=0.3,
        marker=dict(colors=['#ff6b6b', '#ffd93d', '#6bcb77', '#4d96ff', '#9b59b6'])
    )])
    
    fig.update_layout(
        title='Age Group Distribution',
        height=400,
        template='plotly_dark'
    )
    
    return fig

def create_game_popularity_chart(players_df):
    """Create game popularity bar chart"""
    if players_df.empty:
        return None
    
    game_counts = players_df['Game'].value_counts()
    
    fig = px.bar(
        x=game_counts.index,
        y=game_counts.values,
        title='Game Popularity',
        labels={'x': 'Game', 'y': 'Number of Players'},
        color=game_counts.values,
        color_continuous_scale='viridis'
    )
    
    fig.update_layout(height=400, template='plotly_dark')
    return fig

def create_station_performance_chart(players_df):
    """Create station performance chart"""
    if players_df.empty:
        return None
    
    # Ensure numeric types for aggregation
    players_df = fix_dataframe_types(players_df)
    
    station_stats = players_df.groupby('Station').agg({
        'Name': 'count',
        'Wins': 'sum',
        'Potential': 'mean'
    }).reset_index()
    
    station_stats.columns = ['Station', 'Players', 'Total Wins', 'Avg Potential']
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=station_stats['Station'],
        y=station_stats['Total Wins'],
        name='Total Wins',
        marker_color='#ffd93d'
    ))
    
    fig.add_trace(go.Scatter(
        x=station_stats['Station'],
        y=station_stats['Avg Potential'],
        name='Avg Potential',
        yaxis='y2',
        mode='lines+markers',
        line=dict(color='#4d96ff', width=3),
        marker=dict(size=10)
    ))
    
    fig.update_layout(
        title='Station Performance',
        xaxis_title='Station',
        yaxis_title='Total Wins',
        yaxis2=dict(
            title='Avg Potential',
            overlaying='y',
            side='right'
        ),
        height=400,
        template='plotly_dark'
    )
    
    return fig

def create_potential_distribution_chart(players_df):
    """Create potential distribution histogram"""
    if players_df.empty:
        return None
    
    # Ensure numeric types
    players_df = fix_dataframe_types(players_df)
    
    fig = px.histogram(
        players_df,
        x='Potential',
        nbins=20,
        title='Player Potential Distribution',
        labels={'Potential': 'Potential Score', 'count': 'Number of Players'},
        color_discrete_sequence=['#00ff00']
    )
    
    fig.update_layout(height=400, template='plotly_dark')
    
    fig.add_vline(x=80, line_dash="dash", line_color="green", annotation_text="Elite")
    fig.add_vline(x=70, line_dash="dash", line_color="yellow", annotation_text="High")
    fig.add_vline(x=60, line_dash="dash", line_color="orange", annotation_text="Developing")
    
    return fig

def create_tournament_progress_chart():
    """Create tournament progress gauge"""
    if st.session_state.bracket.empty:
        return None
    
    total = len(st.session_state.bracket)
    completed = len(st.session_state.bracket[st.session_state.bracket['Status'] == 'Completed'])
    progress = (completed / total * 100) if total > 0 else 0
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=progress,
        title={'text': "Tournament Progress"},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#00ff00"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 80], 'color': "gray"},
                {'range': [80, 100], 'color': "darkgray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=300, template='plotly_dark')
    return fig

def create_win_rate_chart(players_df):
    """Create win rate scatter plot with type safety"""
    if players_df.empty:
        return None
    
    # Ensure numeric types
    players_df = fix_dataframe_types(players_df)
    
    # Filter players with at least one match
    players_with_matches = players_df[(players_df['Wins'] + players_df['Losses']) > 0].copy()
    
    if players_with_matches.empty:
        return None
    
    players_with_matches['Win Rate'] = (players_with_matches['Wins'] / 
                                        (players_with_matches['Wins'] + players_with_matches['Losses'])) * 100
    
    fig = px.scatter(
        players_with_matches,
        x='Age',
        y='Win Rate',
        size='Wins',
        color='Potential',
        hover_name='Name',
        title='Win Rate vs Age',
        labels={'Win Rate': 'Win Rate (%)', 'Age': 'Age'},
        color_continuous_scale='RdYlGn'
    )
    
    fig.update_layout(height=400, template='plotly_dark')
    return fig

def create_help_request_timeline():
    """Create help request timeline"""
    if st.session_state.help_requests.empty:
        return None
    
    timeline_data = st.session_state.help_requests.groupby('Status').size().reset_index(name='Count')
    
    fig = px.pie(
        timeline_data,
        values='Count',
        names='Status',
        title='Help Request Status',
        color='Status',
        color_discrete_map={'Pending': '#ff6b6b', 'Resolved': '#6bcb77'}
    )
    
    fig.update_layout(height=350, template='plotly_dark')
    return fig

def render_player_exports(players_df, key_prefix="exp"):
    """CSV / highlighted CSV / green-highlight Excel downloads (direct buttons - no nested buttons)"""
    stamp = datetime.now().strftime('%Y%m%d')
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📊 Download All Players CSV", data=players_df.to_csv(index=False),
                           file_name=f"RRR_Players_{stamp}.csv", mime="text/csv",
                           use_container_width=True, key=f"{key_prefix}_csv_all")
    highlighted_players = players_df[players_df['Highlighted'] == True]
    with c2:
        if highlighted_players.empty:
            st.caption("⭐ No highlighted players yet - highlighted exports unlock when you have recruits.")
        else:
            st.download_button("⭐ Download Highlighted CSV", data=highlighted_players.to_csv(index=False),
                               file_name=f"RRR_Highlighted_{stamp}.csv", mime="text/csv",
                               use_container_width=True, key=f"{key_prefix}_csv_hl")
    if not highlighted_players.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            highlighted_players.to_excel(writer, sheet_name='Recruits', index=False)
            worksheet = writer.sheets['Recruits']
            green_fill = PatternFill(start_color="00FF00", end_color="00FF00", fill_type="solid")
            for row_idx in range(2, len(highlighted_players) + 2):
                for col_idx in range(1, len(highlighted_players.columns) + 1):
                    worksheet.cell(row=row_idx, column=col_idx).fill = green_fill
        st.download_button("📥 Download Excel with Green Highlights", data=output.getvalue(),
                           file_name=f"RRR_Recruits_Green_{stamp}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True, key=f"{key_prefix}_xlsx")

# ---------- SIDEBAR ----------
with st.sidebar:
  
    
    # Mobile/PC view toggle
    current_view = "📱 Mobile" if st.session_state.mobile_view else "💻 Desktop"
    next_view = "💻 PC" if st.session_state.mobile_view else "📱 Mobile"
    
    if st.button(f"🔄 Toggle to {next_view} View", use_container_width=True):
        st.session_state.mobile_view = not st.session_state.mobile_view
        st.rerun()
    
    if st.session_state.mobile_view:
        st.info("📱 Mobile Optimized View Active")
    
    if st.session_state.logged_in:
        st.success(f"🟢 Live Updates Active")
        st.caption(f"Last update: {st.session_state.last_update.strftime('%H:%M:%S')}")
        
        if st.session_state.user_role == 'admin':
            unread = len(st.session_state.notifications[
                (st.session_state.notifications['Read'] == False) &
                (st.session_state.notifications['Target Role'] == 'admin')
            ])
            if unread > 0:
                st.warning(f"🔔 {unread} new notification{'s' if unread > 1 else ''}!")
        
        if st.button("🔄 Refresh Live Data", use_container_width=True):
            st.session_state.last_update = datetime.now()
            fix_all_data_types()
            st.rerun()
        
        st.divider()
    
    if not st.session_state.logged_in:
        st.subheader("🔐 Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", use_container_width=True):
            if login(username, password):
                fix_all_data_types()
                st.success(f"✅ Welcome, {st.session_state.user_name}!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
    
    else:
        st.write(f"👤 **{st.session_state.user_name}**")
        st.write(f"🎯 Role: **{st.session_state.user_role}**")
        if st.session_state.user_role == "station_manager":
            st.write(f"📌 Stations: **{', '.join(st.session_state.user_stations)}**")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
        
        st.divider()
        
        # ADD PLAYER FORM
        if st.session_state.user_role in ["admin", "station_manager"]:
            st.subheader("➕ Add Player")
            
            # Check if we have a suggested game/age from balance checker
            if st.session_state.suggested_game and st.session_state.suggested_age:
                st.info(f"💡 Suggested: Add a {st.session_state.suggested_age} player for {st.session_state.suggested_game}")
            
            name = st.text_input("Player Name", key="add_player_name")
            age = st.number_input("Age", min_value=5, max_value=99, step=1, key="add_player_age")
            
            # Pre-fill game if suggested
            game_options = ["FIFA (Soccer)", "Call of Duty", "Fighting Games", "Racing Games", "FPS", "Other"]
            if 'add_player_game' not in st.session_state:
                st.session_state['add_player_game'] = game_options[0]
            if st.session_state.get('_suggestion_pending') and st.session_state.suggested_game in game_options:
                st.session_state['add_player_game'] = st.session_state.suggested_game
                st.session_state['_suggestion_pending'] = False
            game = st.selectbox("Game", game_options, key="add_player_game")
            
            if st.session_state.user_role == "admin":
                station = st.selectbox("Station", list(st.session_state.station_config.keys()), key="add_player_station_admin")
            else:
                station = st.session_state.user_stations[0] if st.session_state.user_stations else list(st.session_state.station_config.keys())[0]
                st.info(f"📌 Adding to: {station}")
            
            if st.button("Add Player", use_container_width=True):
                name = (name or "").strip()
                if name and name.lower() in [str(n).lower() for n in st.session_state.players['Name'].tolist()]:
                    st.error(f"❌ A player named '{name}' already exists. Names must be unique (add a surname or initial).")
                elif name and age:
                    age_group = get_age_group(age)
                    
                    new_player = pd.DataFrame([{
                        'Name': name,
                        'Age': age,
                        'Age Group': age_group,
                        'Game': game,
                        'Station': station,
                        'Wins': 0,
                        'Losses': 0,
                        'Status': 'Active',
                        'Potential': 50,
                        'Highlighted': False,
                        'Recruiter Notes': '',
                        'Highlight Reason': ''
                    }])
                    
                    st.session_state.players = pd.concat([st.session_state.players, new_player], ignore_index=True)
                    st.session_state.players = fix_dataframe_types(st.session_state.players)
                    update_all_potentials()
                    update_station_counts()
                    
                    # Clear suggestions after adding
                    st.session_state.suggested_game = None
                    st.session_state.suggested_age = None
                    
                    st.success(f"✅ Added {name} ({age_group}) to {station}")
                    st.rerun()
                else:
                    st.warning("⚠️ Enter a player name first")
        
        # Password Change Section (visible to all logged-in users)
        st.divider()
        with st.expander("🔑 Change Password"):
            st.subheader("Change Your Password")
            
            current_pass = st.text_input("Current Password", type="password", key="current_pass")
            new_pass = st.text_input("New Password", type="password", key="new_pass")
            confirm_pass = st.text_input("Confirm New Password", type="password", key="confirm_pass")
            
            if st.button("Update Password", use_container_width=True):
                if current_pass and new_pass and confirm_pass:
                    if new_pass != confirm_pass:
                        st.error("❌ New passwords don't match!")
                    elif len(new_pass) < 6:
                        st.error("❌ Password must be at least 6 characters!")
                    else:
                        success, message = change_password(
                            st.session_state.username,
                            current_pass,
                            new_pass
                        )
                        if success:
                            st.success(f"✅ {message}")
                            st.info("Please login again with your new password.")
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.warning("⚠️ Please fill in all fields")

# ---------- MAIN CONTENT ----------
# The rest of the code continues with the tabs and main content...


if st.session_state.logged_in:
    
    # Ensure proper data types
    fix_all_data_types()
    
    # Update station counts and potentials
    update_station_counts()
    if not st.session_state.players.empty:
        update_all_potentials()
    
    # Create tabs based on role (keyed by name, so each role always gets the right content)
    if st.session_state.user_role == "admin":
        _tab_spec = [("dashboard", "📊 Dashboard"), ("analytics", "📈 Analytics"), ("players", "👥 Players"),
                     ("balance", "🎯 Balance"), ("balance_check", "⚖️ Balance Check"), ("tournament", "🏆 Tournament"),
                     ("live", "🔴 Live Scores"), ("recruiting", "⭐ Recruiting"), ("match", "📊 Match Details"),
                     ("help", "🆘 Help Requests"), ("saveload", "💾 Save/Load"), ("admin", "⚙️ Admin")]
    elif st.session_state.user_role == "station_manager":
        _tab_spec = [("dashboard", "📊 Dashboard"), ("analytics", "📈 Analytics"), ("players", "👥 Players"),
                     ("balance", "🎯 Balance"), ("balance_check", "⚖️ Balance Check"), ("tournament", "🏆 Tournament"),
                     ("live", "🔴 Live Scores"), ("recruiting", "⭐ Recruiting"), ("match", "📊 Match Details"),
                     ("help", "🆘 Request Help"), ("saveload", "💾 Save/Load")]
    else:  # recruiter
        _tab_spec = [("analytics", "📈 Analytics"), ("recruiting", "🔍 Recruiting"), ("players", "📊 Players"),
                     ("balance_check", "⚖️ Balance Check"), ("live", "🔴 Live Scores"), ("match", "📊 Match Details"),
                     ("saveload", "💾 Save/Load"), ("export", "📥 Export")]
    T = dict(zip([k for k, _ in _tab_spec], st.tabs([lbl for _, lbl in _tab_spec])))
    
    # ---------- TAB 1: DASHBOARD ----------
    if 'dashboard' in T:
        with T['dashboard']:
            st.subheader(f"📊 Dashboard - {st.session_state.user_name}")
        
            # Responsive layout
            if st.session_state.mobile_view:
                cols = st.columns(2)
            else:
                cols = st.columns(4)
        
            if st.session_state.user_role == "station_manager":
                display_players = st.session_state.players[
                    st.session_state.players['Station'].isin(st.session_state.user_stations)
                ]
            else:
                display_players = st.session_state.players
        
            display_players = fix_dataframe_types(display_players)
        
            total_players = len(display_players)
            active_players = len(display_players[display_players['Status'] == 'Active'])
            highlighted = len(display_players[display_players['Highlighted'] == True])
            matches = len(st.session_state.bracket[st.session_state.bracket['Status'] == 'Completed'])
        
            cols[0].metric("👥 Total Players", total_players)
            cols[1].metric("🎮 Active", active_players)
            if not st.session_state.mobile_view:
                cols[2].metric("⭐ Highlighted", highlighted)
                cols[3].metric("🏆 Matches", matches)
            else:
                cols[0].metric("⭐ Highlighted", highlighted)
                cols[1].metric("🏆 Matches", matches)
        
            # Balance Alert on Dashboard
            balance_data = check_player_balance()
            if not balance_data.get('balanced', True) and balance_data.get('suggestions'):
                with st.expander("⚠️ Balance Alert - Click to see what players you need", expanded=True):
                    st.warning(f"⚠️ {balance_data.get('odd_groups', 0)} game/age group(s) need more players!")
                
                    for suggestion in balance_data.get('suggestions', []):
                        if suggestion.get('needed', 0) > 0:
                            st.markdown(f"""
                            <div style='background-color: #fff3cd; padding: 10px; border-radius: 8px; margin: 5px 0; border-left: 4px solid #ffc107;'>
                                <strong>🎮 {suggestion['game']}</strong> - {suggestion['age_group']}<br>
                                👤 Current: {suggestion['current_count']} players | Need: <strong>+{suggestion.get('needed', 0)}</strong> more<br>
                                📝 Players: {', '.join(suggestion['players']) if suggestion['players'] else 'None'}
                            </div>
                            """, unsafe_allow_html=True)
                
                    st.info("💡 Go to the 'Balance Check' tab for detailed recommendations")
        
            # Show station status
            st.subheader("📌 Station Status")
        
            update_station_counts()
        
            # Responsive station cards
            if st.session_state.mobile_view:
                station_cols = st.columns(2)
            else:
                station_cols = st.columns(min(len(st.session_state.station_config), 3))
        
            for idx, (station, config) in enumerate(st.session_state.station_config.items()):
                with station_cols[idx % len(station_cols)]:
                    status, status_text = get_station_status(station)
                    icon = "🟢" if status == "balanced" else "🟡" if status == "under" else "🔴"
                
                    st.markdown(f"""
                    <div style='
                        background-color: #ffffff; 
                        padding: 20px; 
                        border-radius: 12px; 
                        text-align: center; 
                        margin: 8px 0; 
                        border: 2px solid #e0e0e0;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.08);
                    '>
                        <div style='color: #000000; font-size: 18px; font-weight: 700; margin-bottom: 8px;'>
                            {station}
                        </div>
                        <div style='font-size: 32px; margin-bottom: 8px;'>
                            {icon}
                        </div>
                        <div style='color: #000000; font-size: 16px; font-weight: 600; margin-bottom: 4px;'>
                            Players: {config['current']} / {config['capacity']}
                        </div>
                        <div style='
                            color: {'#2e7d32' if status == 'balanced' else '#e65100' if status == 'under' else '#c62828'}; 
                            font-size: 15px; 
                            font-weight: 700;
                            background-color: {'#e8f5e9' if status == 'balanced' else '#fff3e0' if status == 'under' else '#ffebee'};
                            padding: 4px 12px;
                            border-radius: 20px;
                            display: inline-block;
                            margin-top: 4px;
                        '>
                            {status_text}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
            if st.session_state.user_role == 'admin':
                pending_requests = len(st.session_state.help_requests[st.session_state.help_requests['Status'] == 'Pending'])
                if pending_requests > 0:
                    st.warning(f"🆘 {pending_requests} pending help request{'s' if pending_requests > 1 else ''}!")

    # ---------- TAB 2: ANALYTICS ----------
    if 'analytics' in T:
        with T['analytics']:
            st.subheader("📈 Advanced Analytics")
        
            st.info("""
            **📊 Analytics Dashboard**
            Visual insights into your tournament data. Hover over charts for details.
            """)
        
            # Filter for station manager
            if st.session_state.user_role == "station_manager":
                display_players = st.session_state.players[
                    st.session_state.players['Station'].isin(st.session_state.user_stations)
                ]
            else:
                display_players = st.session_state.players
        
            display_players = fix_dataframe_types(display_players)
        
            # Row 1: Key Metrics
            st.subheader("🎯 Key Performance Indicators")
        
            if not display_players.empty:
                if st.session_state.mobile_view:
                    cols = st.columns(2)
                else:
                    cols = st.columns(5)
            
                total = len(display_players)
                avg_potential = display_players['Potential'].mean()
                total_wins = display_players['Wins'].sum()
                avg_age = display_players['Age'].mean()
                total_matches = len(st.session_state.bracket[st.session_state.bracket['Status'] == 'Completed'])
            
                cols[0].metric("👥 Total Players", total)
                cols[1].metric("⭐ Avg Potential", f"{avg_potential:.1f}%")
                if not st.session_state.mobile_view:
                    cols[2].metric("🏆 Total Wins", int(total_wins))
                    cols[3].metric("📅 Avg Age", f"{avg_age:.1f}")
                    cols[4].metric("🎮 Matches", total_matches)
                else:
                    cols[0].metric("🏆 Wins", int(total_wins))
                    cols[1].metric("🎮 Matches", total_matches)
        
            st.divider()
        
            # Charts - responsive layout
            if st.session_state.mobile_view:
                chart_cols = [1]
            else:
                chart_cols = st.columns(2)
        
            # Row 2: Charts
            if st.session_state.mobile_view:
                fig1 = create_performance_chart(display_players)
                if fig1:
                    st.plotly_chart(fig1, use_container_width=True)
                else:
                    st.info("Add more players to see performance charts")
            
                fig2 = create_age_distribution_chart(display_players)
                if fig2:
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("Add more players to see age distribution")
            else:
                with chart_cols[0]:
                    fig1 = create_performance_chart(display_players)
                    if fig1:
                        st.plotly_chart(fig1, use_container_width=True)
                    else:
                        st.info("Add more players to see performance charts")
            
                with chart_cols[1]:
                    fig2 = create_age_distribution_chart(display_players)
                    if fig2:
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.info("Add more players to see age distribution")
        
            # Row 3: Charts
            if st.session_state.mobile_view:
                fig3 = create_game_popularity_chart(display_players)
                if fig3:
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.info("Add more players to see game popularity")
            
                fig4 = create_potential_distribution_chart(display_players)
                if fig4:
                    st.plotly_chart(fig4, use_container_width=True)
                else:
                    st.info("Add more players to see potential distribution")
            else:
                with chart_cols[0]:
                    fig3 = create_game_popularity_chart(display_players)
                    if fig3:
                        st.plotly_chart(fig3, use_container_width=True)
                    else:
                        st.info("Add more players to see game popularity")
            
                with chart_cols[1]:
                    fig4 = create_potential_distribution_chart(display_players)
                    if fig4:
                        st.plotly_chart(fig4, use_container_width=True)
                    else:
                        st.info("Add more players to see potential distribution")
        
            # Row 4: Station performance
            if st.session_state.user_role == "admin" or len(st.session_state.user_stations) > 1:
                st.subheader("📍 Station Performance")
                fig5 = create_station_performance_chart(display_players)
                if fig5:
                    st.plotly_chart(fig5, use_container_width=True)
                else:
                    st.info("Add more players to see station performance")
        
            # Row 5: Tournament & Help Analytics
            if st.session_state.mobile_view:
                fig6 = create_tournament_progress_chart()
                if fig6:
                    st.plotly_chart(fig6, use_container_width=True)
                else:
                    st.info("Start a tournament to see progress")
            
                fig7 = create_help_request_timeline()
                if fig7:
                    st.plotly_chart(fig7, use_container_width=True)
                else:
                    st.info("No help requests yet")
            else:
                col1, col2 = st.columns(2)
            
                with col1:
                    fig6 = create_tournament_progress_chart()
                    if fig6:
                        st.plotly_chart(fig6, use_container_width=True)
                    else:
                        st.info("Start a tournament to see progress")
            
                with col2:
                    fig7 = create_help_request_timeline()
                    if fig7:
                        st.plotly_chart(fig7, use_container_width=True)
                    else:
                        st.info("No help requests yet")
        
            # Row 6: Win Rate vs Age
            if len(display_players) > 2:
                st.subheader("📊 Win Rate Analysis")
                fig8 = create_win_rate_chart(display_players)
                if fig8:
                    st.plotly_chart(fig8, use_container_width=True)
        
            # Export analytics
            st.divider()
            st.subheader("📥 Export Analytics Report")
        
            if st.button("📊 Generate Analytics Report (CSV)"):
                if not display_players.empty:
                    csv = display_players.to_csv(index=False)
                    st.download_button(
                        label="Download Analytics CSV",
                        data=csv,
                        file_name=f"RRR_Analytics_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                    st.success("✅ Analytics report generated!")
                else:
                    st.warning("No data to export")
    
    # ---------- TAB 3: PLAYERS ----------
    if 'players' in T:
        with T['players']:
            st.subheader("👥 Player Management")
        
            if st.session_state.user_role == "station_manager":
                display_players = st.session_state.players[
                    st.session_state.players['Station'].isin(st.session_state.user_stations)
                ]
            else:
                display_players = st.session_state.players
        
            display_players = fix_dataframe_types(display_players)
        
            if not display_players.empty:
                display_df = display_players.copy()
            
                for idx, row in display_df.iterrows():
                    potential = row.get('Potential', 0)
                    display_df.loc[idx, 'Status'] = f"{row['Status']}"
            
                st.dataframe(display_df[['Name', 'Age', 'Age Group', 'Game', 'Station', 'Wins', 'Losses', 'Potential', 'Highlighted', 'Status']], use_container_width=True)
            
                st.subheader("✏️ Manage Players")
                player_names = display_players['Name'].tolist()
            
                if player_names:
                    selected_player = st.selectbox("Select Player", player_names, key="manage_player_select")
                    player_data = st.session_state.players[st.session_state.players['Name'] == selected_player].iloc[0]
                
                    if st.session_state.mobile_view:
                        col1, col2 = st.columns(2)
                    else:
                        col1, col2, col3 = st.columns(3)
                
                    with col1:
                        if st.button("⭐ Mark as High Potential"):
                            idx = st.session_state.players[st.session_state.players['Name'] == selected_player].index[0]
                            st.session_state.players.loc[idx, 'Highlighted'] = True
                            st.session_state.players.loc[idx, 'Highlight Reason'] = "Manual Highlight - Top Prospect"
                            if selected_player in st.session_state.highlight_overrides:
                                st.session_state.highlight_overrides.remove(selected_player)
                            st.success(f"✅ {selected_player} marked as High Potential!")
                            st.rerun()
                
                    with col2:
                        if st.button("❌ Remove Highlight"):
                            idx = st.session_state.players[st.session_state.players['Name'] == selected_player].index[0]
                            st.session_state.players.loc[idx, 'Highlighted'] = False
                            st.session_state.players.loc[idx, 'Highlight Reason'] = ''
                            if selected_player not in st.session_state.highlight_overrides:
                                st.session_state.highlight_overrides.append(selected_player)
                            st.success(f"✅ Removed highlight from {selected_player}")
                            st.rerun()
                
                    if not st.session_state.mobile_view:
                        with col3:
                            if st.button("🔄 Reset Stats"):
                                idx = st.session_state.players[st.session_state.players['Name'] == selected_player].index[0]
                                st.session_state.players.loc[idx, 'Wins'] = 0
                                st.session_state.players.loc[idx, 'Losses'] = 0
                                st.success(f"✅ Reset stats for {selected_player}")
                                st.rerun()
                
                    st.subheader("📝 Recruiter Notes")
                    notes = st.text_area("Notes for this player", value=player_data.get('Recruiter Notes', ''), key=f"notes_{selected_player}")
                    if st.button("💾 Save Notes"):
                        idx = st.session_state.players[st.session_state.players['Name'] == selected_player].index[0]
                        st.session_state.players.loc[idx, 'Recruiter Notes'] = notes
                        st.success("✅ Notes saved!")
            else:
                st.info("No players in your station(s). Add players from the sidebar.")
    
    # ---------- TAB 4: BALANCE ----------
    if st.session_state.user_role in ["admin", "station_manager"]:
        with T['balance']:
            st.subheader("🎯 Player Balancing System")
            
            st.info("""
            **How Player Balancing Works:**
            - Each station has a maximum capacity (default: 8 players)
            - Stations with less than 50% capacity are "Under capacity"
            - Stations with more than 100% capacity are "Over capacity"
            - Auto-balance moves players from overloaded to underloaded stations
            - You can also manually move players
            """)
            
            update_station_counts()
            
            if st.session_state.user_role == "admin":
                st.subheader("⚙️ Station Configuration")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    selected_station = st.selectbox("Select Station", list(st.session_state.station_config.keys()), key="station_config_select")
                    current_capacity = st.session_state.station_config[selected_station]['capacity']
                    new_capacity = st.number_input(
                        f"Capacity for {selected_station}",
                        min_value=2,
                        max_value=20,
                        value=current_capacity,
                        step=2
                    )
                    
                    if st.button("💾 Update Capacity"):
                        st.session_state.station_config[selected_station]['capacity'] = new_capacity
                        st.success(f"✅ Updated {selected_station} capacity to {new_capacity}")
                        st.rerun()
                
                with col2:
                    st.subheader("📊 Current Station Load")
                    
                    for station, config in st.session_state.station_config.items():
                        status, status_text = get_station_status(station)
                        icon = "🟢" if status == "balanced" else "🟡" if status == "under" else "🔴"
                        st.write(f"{icon} {station}: {config['current']} / {config['capacity']} players")
            
            st.subheader("🔄 Auto-Balance Players")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if st.button("🎯 Auto-Balance All Stations", use_container_width=True):
                    result = balance_players_across_stations()
                    st.info(result)
                    st.rerun()
            
            with col2:
                if st.button("📊 Show Station Summary", use_container_width=True):
                    update_station_counts()
                    
                    st.subheader("📊 Station Summary")
                    
                    summary_data = []
                    for station, config in st.session_state.station_config.items():
                        status, status_text = get_station_status(station)
                        summary_data.append({
                            'Station': station,
                            'Current Players': config['current'],
                            'Capacity': config['capacity'],
                            'Status': status_text,
                            'Available Slots': config['capacity'] - config['current']
                        })
                    
                    summary_df = pd.DataFrame(summary_data)
                    st.dataframe(summary_df, use_container_width=True)
            
            st.divider()
            st.subheader("✋ Manual Player Movement")
            
            active_players = st.session_state.players[st.session_state.players['Status'] == 'Active']
            
            if not active_players.empty:
                if st.session_state.mobile_view:
                    col1, col2 = st.columns(2)
                else:
                    col1, col2, col3 = st.columns(3)
                
                with col1:
                    player_to_move = st.selectbox("Select Player", active_players['Name'].tolist(), key="move_player_select")
                
                with col2:
                    current_station = active_players[active_players['Name'] == player_to_move]['Station'].iloc[0]
                    st.write(f"📍 Current: **{current_station}**")
                    
                    available_stations = [s for s in st.session_state.station_config.keys() if s != current_station]
                    target_station = st.selectbox("Move To", available_stations, key="move_target_select")
                
                if not st.session_state.mobile_view:
                    with col3:
                        if st.button("🚚 Move Player", use_container_width=True):
                            if player_to_move and target_station:
                                target_config = st.session_state.station_config[target_station]
                                if target_config['current'] < target_config['capacity']:
                                    result = move_player_to_station(player_to_move, target_station)
                                    st.success(result)
                                    st.rerun()
                                else:
                                    st.warning(f"⚠️ {target_station} is at full capacity ({target_config['current']}/{target_config['capacity']})")
                
                if st.session_state.mobile_view:
                    if st.button("🚚 Move Player", use_container_width=True):
                        if player_to_move and target_station:
                            target_config = st.session_state.station_config[target_station]
                            if target_config['current'] < target_config['capacity']:
                                result = move_player_to_station(player_to_move, target_station)
                                st.success(result)
                                st.rerun()
                            else:
                                st.warning(f"⚠️ {target_station} is at full capacity ({target_config['current']}/{target_config['capacity']})")
            else:
                st.info("No active players to move. Add players first.")
            
            st.divider()
            st.subheader("📍 Players by Station")
            
            for station in st.session_state.station_config.keys():
                station_players = get_players_by_station(station)
                status, status_text = get_station_status(station)
                
                st.markdown(f"""
                <div style='background-color: #f8f9fa; padding: 10px; border-radius: 10px; margin: 5px 0; border-left: 5px solid {'#4caf50' if status == 'balanced' else '#ff9800' if status == 'under' else '#f44336'}; color: #1a1a1a;'>
                    <strong style='color: #1a1a1a;'>{station}</strong> - {status_text} ({len(station_players)} players)
                </div>
                """, unsafe_allow_html=True)
                
                if not station_players.empty:
                    player_list = station_players['Name'].tolist()
                    st.write(", ".join(player_list))
                else:
                    st.write("*No players at this station*")
    
    # ---------- TAB 5: BALANCE CHECK ----------
    if 'balance_check' in T:
        with T['balance_check']:
            st.subheader("⚖️ Player Balance Checker")
        
            st.info("""
            **Why balance matters:**
            - Even numbers of players per game/age group ensure no BYE matches (for head-to-head games)
            - Individual scoring games (shooting games) don't require pairing
            - This tool tells you exactly what players you need to add
            """)
        
            render_balance_dashboard()
        
            st.divider()
        
            # Quick fix options
            st.subheader("🔧 Quick Fix Options")
        
            col1, col2 = st.columns(2)
        
            with col1:
                if st.button("🔧 Fix Duplicate Players", use_container_width=True):
                    success, message = fix_duplicate_players()
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        
            with col2:
                if st.button("⚖️ Rebalance Bracket", use_container_width=True):
                    success, result = rebalance_bracket()
                    if success and isinstance(result, pd.DataFrame):
                        st.session_state.bracket = result
                        st.success("✅ Bracket rebalanced successfully!")
                        st.rerun()
                    else:
                        st.error(result)
    
    # ---------- TAB 6: TOURNAMENT ----------
    if 'tournament' in T:
        with T['tournament']:
            st.subheader("🏆 Tournament Management")
        
            if st.session_state.user_role in ["admin", "station_manager"]:
            
                # Custom Leg Configuration
                with st.expander("⚙️ Customize Legs/Rounds per Game", expanded=False):
                    st.info("Set how many legs/rounds each game type should have in the tournament")
                
                    col1, col2 = st.columns(2)
                
                    games_list = ["FIFA (Soccer)", "Call of Duty", "Fighting Games", "Racing Games", "FPS", "Other"]
                
                    for idx, game in enumerate(games_list):
                        if idx % 2 == 0:
                            with col1:
                                current_legs = st.session_state.game_legs_config.get(game, 2)
                                new_legs = st.number_input(
                                    f"{game}",
                                    min_value=1,
                                    max_value=10,
                                    value=current_legs,
                                    step=1,
                                    key=f"legs_{game}"
                                )
                                if new_legs != current_legs:
                                    st.session_state.game_legs_config[game] = new_legs
                        else:
                            with col2:
                                current_legs = st.session_state.game_legs_config.get(game, 2)
                                new_legs = st.number_input(
                                    f"{game}",
                                    min_value=1,
                                    max_value=10,
                                    value=current_legs,
                                    step=1,
                                    key=f"legs_{game}"
                                )
                                if new_legs != current_legs:
                                    st.session_state.game_legs_config[game] = new_legs
                
                    st.success("✅ Leg configurations saved! Generate a new bracket to apply changes.")
            
                st.divider()
            
                if st.session_state.mobile_view:
                    col1, col2 = st.columns(2)
                else:
                    col1, col2, col3 = st.columns(3)
            
                with col1:
                    if st.button("🎯 Generate Bracket", use_container_width=True):
                        if st.session_state.user_role == "station_manager":
                            players_for_tournament = st.session_state.players[
                                st.session_state.players['Station'].isin(st.session_state.user_stations)
                            ]
                        else:
                            players_for_tournament = st.session_state.players
                    
                        players_for_tournament = fix_dataframe_types(players_for_tournament)
                    
                        if len(players_for_tournament) >= 2:
                            # Get active players only
                            active_players = players_for_tournament[players_for_tournament['Status'] == 'Active']
                        
                            if len(active_players) >= 2:
                                # Generate bracket - automatically groups by game
                                if st.session_state.user_role == "station_manager" and not st.session_state.bracket.empty:
                                    # keep other stations' matches, rebuild only this manager's
                                    others = st.session_state.bracket[
                                        ~st.session_state.bracket['Station'].isin(st.session_state.user_stations)
                                    ]
                                    used = pd.to_numeric(others['Match ID'].astype(str).str.lstrip('M'), errors='coerce').max()
                                    next_id = int(used) + 1 if pd.notna(used) else 1
                                    mine = generate_flexible_bracket(active_players, start_id=next_id)
                                    st.session_state.bracket = pd.concat([others, mine], ignore_index=True)
                                else:
                                    st.session_state.bracket = generate_flexible_bracket(active_players)
                                st.session_state.tournament_active = True
                                st.session_state.tournament_balloons_shown = False
                            
                                # Count matches by game
                                game_counts = st.session_state.bracket['Game'].value_counts()
                                game_summary = ", ".join([f"{game}: {count}" for game, count in game_counts.items()])
                            
                                st.success(f"✅ Generated {len(st.session_state.bracket)} matches grouped by game type!")
                                st.info(f"📊 Games: {game_summary}")
                                st.rerun()
                            else:
                                st.error("Need at least 2 active players! Currently active players: " + ", ".join(active_players['Name'].tolist() if not active_players.empty else ["None"]))
                        else:
                            st.error("Need at least 2 players total!")
            
                with col2:
                    if st.button("🔄 Reshuffle Bracket", use_container_width=True):
                        if st.session_state.tournament_active and not st.session_state.bracket.empty:
                            done = len(st.session_state.bracket[
                                (st.session_state.bracket['Status'] == 'Completed') &
                                (st.session_state.bracket['Player 2'] != 'BYE')
                            ])
                            if done > 0:
                                st.session_state.confirm_reshuffle = True
                            else:
                                active_players = st.session_state.players[st.session_state.players['Status'] == 'Active']
                                new_bracket, message = reshuffle_bracket(active_players)
                                if new_bracket is not None:
                                    st.session_state.bracket = new_bracket
                                    st.success("✅ Bracket reshuffled successfully!")
                                    st.rerun()
                        else:
                            st.warning("No active tournament to reshuffle. Generate a bracket first.")

                if st.session_state.confirm_reshuffle:
                    st.warning("⚠️ Some matches are already completed. Reshuffling will RESET every match result!")
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        if st.button("✅ Yes, reshuffle everything", use_container_width=True, key="do_reshuffle"):
                            active_players = st.session_state.players[st.session_state.players['Status'] == 'Active']
                            new_bracket, message = reshuffle_bracket(active_players)
                            st.session_state.confirm_reshuffle = False
                            if new_bracket is not None:
                                st.session_state.bracket = new_bracket
                                st.session_state.live_scores = st.session_state.live_scores.iloc[0:0]
                                st.session_state.tournament_balloons_shown = False
                                st.rerun()
                    with cc2:
                        if st.button("↩️ Cancel", use_container_width=True, key="cancel_reshuffle"):
                            st.session_state.confirm_reshuffle = False
                            st.rerun()

                if not st.session_state.mobile_view:
                    with col3:
                        if st.button("🔄 Reset Tournament", use_container_width=True):
                            st.session_state.bracket = empty_bracket()
                            st.session_state.live_scores = st.session_state.live_scores.iloc[0:0]
                            st.session_state.tournament_balloons_shown = False
                            st.session_state.tournament_active = False
                            st.success("✅ Tournament reset!")
                            st.rerun()
            
                if st.session_state.mobile_view:
                    if st.button("🔄 Reset Tournament", use_container_width=True):
                        st.session_state.bracket = empty_bracket()
                        st.session_state.live_scores = st.session_state.live_scores.iloc[0:0]
                        st.session_state.tournament_balloons_shown = False
                        st.session_state.tournament_active = False
                        st.success("✅ Tournament reset!")
                        st.rerun()
            
                # Show tournament summary by game
                if not st.session_state.bracket.empty:
                    st.divider()
                    st.subheader("📊 Tournament Summary by Game")
                
                    # Group by game and show counts
                    game_summary = st.session_state.bracket.groupby('Game').agg({
                        'Match ID': 'count',
                        'Status': lambda x: (x == 'Completed').sum(),
                        'Leg Number': 'max',
                        'Match Mode': 'first'
                    }).reset_index()
                    game_summary.columns = ['Game', 'Total Matches', 'Completed', 'Legs per Match', 'Mode']
                
                    st.dataframe(game_summary, use_container_width=True)
                
                    st.divider()
                    st.subheader("📋 Tournament Bracket")
                
                    # Show rounds/legs info
                    max_rounds = st.session_state.max_rounds
                    st.caption(f"📌 This tournament has up to {max_rounds} round(s)/leg(s) per match")
                
                    st.dataframe(st.session_state.bracket, use_container_width=True)
                
                    st.divider()
                
                    st.subheader("✏️ Enter Match Results")
                
                    pending_matches = st.session_state.bracket[
                        st.session_state.bracket['Status'] == 'Pending'
                    ]
                    if st.session_state.user_role == "station_manager":
                        pending_matches = pending_matches[pending_matches['Station'].isin(st.session_state.user_stations)]
                
                    if not pending_matches.empty:
                        match_ids = pending_matches['Match ID'].tolist()
                        selected_match = st.selectbox("Select Match", match_ids, key="tournament_match_select")
                    
                        match_data = st.session_state.bracket[
                            st.session_state.bracket['Match ID'] == selected_match
                        ].iloc[0]
                    
                        # Check if this is an individual scoring match
                        is_individual = match_data.get('Match Mode') == 'Individual'
                    
                        if is_individual:
                            # Individual scoring mode (shooting games)
                            st.info(f"🎯 Individual Match for {match_data['Player 1']}")
                            st.caption(f"Game: {match_data['Game']} | {match_data['Leg']}")
                        
                            # Show match info
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Player", match_data['Player 1'])
                            with col2:
                                st.metric("Game", match_data['Game'])
                            with col3:
                                st.metric("Leg", match_data['Leg'])
                        
                            st.divider()
                        
                            # Stats form for individual player
                            game_name = match_data['Game']
                            player_name = match_data['Player 1']
                        
                            stats_data, total_score = render_individual_score_form(match_data)
                        
                            # Show stats preview
                            if st.button("👁️ Preview Stats"):
                                display_individual_match_stats(stats_data, game_name, player_name)
                        
                            # Submit result
                            if st.button("✅ Submit Result"):
                                idx = st.session_state.bracket[
                                    st.session_state.bracket['Match ID'] == selected_match
                                ].index[0]
                            
                                # Store the stats
                                if 'stats_data' in locals():
                                    # Clean up stats_data before saving
                                    stats_to_save = {k: v for k, v in stats_data.items() if k not in ['game', 'player', 'leg']}
                                    st.session_state.bracket.loc[idx, 'Stats'] = json.dumps(stats_to_save)
                            
                                # Set score and status
                                st.session_state.bracket.loc[idx, 'Score'] = str(total_score)
                                st.session_state.bracket.loc[idx, 'Winner'] = player_name
                                st.session_state.bracket.loc[idx, 'Loser'] = 'N/A'
                                st.session_state.bracket.loc[idx, 'Status'] = 'Completed'
                            
                                # Solo attempts are ranked by score - they don't count as head-to-head wins/losses
                                update_all_potentials()
                            
                                # Add to live scores (with individual scoring note)
                                add_live_score(
                                    selected_match,
                                    player_name,
                                    'INDIVIDUAL',
                                    str(total_score),
                                    player_name,
                                    match_data['Station'],
                                    match_data['Age Group'],
                                    match_data['Game']
                                )
                            
                                st.success(f"✅ {player_name}'s performance recorded! Score: {total_score}")
                                st.rerun()
                    
                        elif match_data['Player 2'] != 'BYE':
                            # Regular head-to-head mode
                            col1, col2, col3 = st.columns(3)
                        
                            with col1:
                                winner = st.selectbox("Winner", [match_data['Player 1'], match_data['Player 2']], key="match_winner_select")
                        
                            with col2:
                                score = st.text_input("Score", placeholder="e.g., 3-2", help="Enter score as Player1-Player2")
                        
                            with col3:
                                station = st.text_input("Station", value=match_data['Station'])
                        
                            # Show leg/round info
                            st.info(f"📌 {match_data['Leg']} - Round {match_data['Leg Number']} of {st.session_state.max_rounds}")
                        
                            # Add match stats section
                            st.divider()
                            with st.expander("📊 Enter Detailed Match Statistics", expanded=False):
                                st.caption("Track game-specific stats for this match")
                                game_name = match_data.get('Game', 'Other')
                                stats_data = render_match_stats_form(
                                    game_name, 
                                    match_data['Player 1'], 
                                    match_data['Player 2'],
                                    match_data['Leg Number'],
                                    key_prefix=f"{selected_match}_"
                                )
                        
                            # Preview stats button
                            if st.button("👁️ Preview Stats"):
                                if 'stats_data' in locals():
                                    display_match_stats(
                                        stats_data, 
                                        game_name,
                                        match_data['Player 1'], 
                                        match_data['Player 2']
                                    )
                        
                            if st.button("✅ Submit Result"):
                                score_ok = True
                                parsed = re.match(r'^\s*(\d+)\s*[-:]\s*(\d+)\s*$', score or '')
                                if score and parsed and match_data['Match Type'] in ('soccer', 'fighting', 'custom'):
                                    s1, s2 = int(parsed.group(1)), int(parsed.group(2))
                                    if s1 != s2:
                                        expected = match_data['Player 1'] if s1 > s2 else match_data['Player 2']
                                        if winner != expected:
                                            score_ok = False
                                            st.error(f"❌ Score {score} means {expected} won (format is Player1-Player2). Fix the winner or the score.")
                                if score and score_ok:
                                    idx = st.session_state.bracket[
                                        st.session_state.bracket['Match ID'] == selected_match
                                    ].index[0]
                                
                                    loser = match_data['Player 1'] if winner == match_data['Player 2'] else match_data['Player 2']
                                
                                    st.session_state.bracket.loc[idx, 'Winner'] = winner
                                    st.session_state.bracket.loc[idx, 'Loser'] = loser
                                    st.session_state.bracket.loc[idx, 'Score'] = score
                                    st.session_state.bracket.loc[idx, 'Status'] = 'Completed'
                                    st.session_state.bracket.loc[idx, 'Station'] = station
                                
                                    # Save the stats data
                                    if 'stats_data' in locals():
                                        # Clean up stats_data before saving
                                        stats_to_save = {k: v for k, v in stats_data.items() if k not in ['game', 'player1', 'player2', 'leg']}
                                        st.session_state.bracket.loc[idx, 'Stats'] = json.dumps(stats_to_save)
                                
                                    # Ensure numeric before incrementing
                                    st.session_state.players = fix_dataframe_types(st.session_state.players)
                                
                                    st.session_state.players.loc[
                                        st.session_state.players['Name'] == winner, 'Wins'
                                    ] += 1
                                    st.session_state.players.loc[
                                        st.session_state.players['Name'] == loser, 'Losses'
                                    ] += 1
                                
                                    update_all_potentials()
                                    update_match_aggregate(selected_match)
                                
                                    add_live_score(
                                        selected_match,
                                        match_data['Player 1'],
                                        match_data['Player 2'],
                                        score,
                                        winner,
                                        station,
                                        match_data['Age Group'],
                                        match_data['Game']
                                    )
                                
                                    st.success(f"✅ Match completed! {winner} wins! (Live score updated)")
                                    st.rerun()
                                elif not score:
                                    st.error("Please enter the score")
                        else:
                            st.info(f"🔄 {match_data['Player 1']} gets a BYE (auto-win)")
                    else:
                        st.success("🎉 All matches completed!")
                    
                        # Save tournament to history
                        if st.button("💾 Save Tournament to History", use_container_width=True):
                            success, message = save_tournament_history()
                            if success:
                                st.success(message)
                            else:
                                st.warning(message)
                    
                        # Get unique games in the tournament
                        games_in_tournament = st.session_state.bracket['Game'].unique()
                    
                        if len(games_in_tournament) > 0:
                            # Show champions for each game
                            st.subheader("🏆 Tournament Champions by Game")
                        
                            # Create a grid of champion cards
                            if st.session_state.mobile_view:
                                champ_cols = st.columns(2)
                            else:
                                champ_cols = st.columns(min(len(games_in_tournament), 3))
                        
                            for idx, game in enumerate(games_in_tournament):
                                if game:  # Skip empty game names
                                    champion, runner_up = determine_game_champion(st.session_state.bracket, game)
                                
                                    if champion:
                                        with champ_cols[idx % len(champ_cols)]:
                                            game_icon = get_game_icon(game)
                                            game_color = get_game_color(game)
                                        
                                            st.markdown(f"""
                                            <div style='
                                                background-color: #ffffff; 
                                                padding: 20px; 
                                                border-radius: 12px; 
                                                text-align: center; 
                                                margin: 8px 0; 
                                                border: 3px solid {game_color};
                                                box-shadow: 0 4px 12px rgba(0,0,0,0.10);
                                            '>
                                                <div style='font-size: 40px;'>{game_icon}</div>
                                                <div style='font-size: 16px; font-weight: 700; color: {game_color}; margin: 8px 0;'>
                                                    {game}
                                                </div>
                                                <div style='font-size: 14px; color: #666666;'>🏆 Champion</div>
                                                <div style='font-size: 24px; font-weight: 700; color: #000000; margin: 4px 0;'>
                                                    {champion}
                                                </div>
                                                {f'<div style="font-size: 14px; color: #666666;">🥈 Runner Up: {runner_up}</div>' if runner_up else ''}
                                            </div>
                                            """, unsafe_allow_html=True)
                                        
                                            # Save champion to session state
                                            set_game_champion(game, champion, runner_up)
                        
                            # Show all-time champions
                            st.divider()
                            st.subheader("🏆 All-Time Game Champions")
                        
                            # Get all champions from session state
                            all_champions = st.session_state.tournament_champions
                        
                            # Create a nice display of all champions
                            if st.session_state.mobile_view:
                                champ_cols = st.columns(2)
                            else:
                                champ_cols = st.columns(max(1, min(len([g for g in all_champions if all_champions[g]['champion']]), 3)))
                        
                            champ_idx = 0
                            for game, data in all_champions.items():
                                if data['champion']:  # Only show games that have champions
                                    with champ_cols[champ_idx % len(champ_cols)]:
                                        game_icon = get_game_icon(game)
                                        game_color = get_game_color(game)
                                    
                                        st.markdown(f"""
                                        <div style='
                                            background-color: #f8f9fa; 
                                            padding: 15px; 
                                            border-radius: 10px; 
                                            text-align: center; 
                                            margin: 5px 0; 
                                            border-left: 5px solid {game_color};
                                        '>
                                            <div style='font-size: 24px;'>{game_icon}</div>
                                            <div style='font-size: 14px; font-weight: 600; color: {game_color};'>
                                                {game}
                                            </div>
                                            <div style='font-size: 18px; font-weight: 700; color: #000000;'>
                                                👑 {data['champion']}
                                            </div>
                                            {f'<div style="font-size: 13px; color: #666666;">🥈 {data["runner_up"]}</div>' if data['runner_up'] else ''}
                                        </div>
                                        """, unsafe_allow_html=True)
                                        champ_idx += 1
                        
                            if champ_idx == 0:
                                st.info("No champions have been crowned yet. Complete a tournament to see champions here!")
                        
                            # Balloons for the overall tournament completion (once, not on every rerun)
                            if not st.session_state.tournament_balloons_shown:
                                st.balloons()
                                st.session_state.tournament_balloons_shown = True
                            st.markdown(f"""
                            <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #ffd700, #ffaa00); border-radius: 10px;'>
                                <h2 style='color: #000;'>🏆 TOURNAMENT COMPLETE! 🏆</h2>
                                <p style='color: #000; font-size: 18px;'>
                                    {len(games_in_tournament)} game tournament completed successfully!
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Fallback for single game tournaments
                            winners = st.session_state.bracket[
                                st.session_state.bracket['Status'] == 'Completed'
                            ]['Winner'].tolist()
                        
                            if winners:
                                champion = winners[-1] if winners else "Unknown"
                                if not st.session_state.tournament_balloons_shown:
                                    st.balloons()
                                    st.session_state.tournament_balloons_shown = True
                                st.markdown(f"""
                                <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #ffd700, #ffaa00); border-radius: 10px;'>
                                    <h2 style='color: #000;'>🏆 TOURNAMENT COMPLETE! 🏆</h2>
                                    <h1 style='color: #000;'>👑 {champion} is the Champion!</h1>
                                </div>
                                """, unsafe_allow_html=True)
            else:
                st.info("Only Admins and Station Managers can manage tournaments")
    
    # ---------- TAB 7: LIVE SCORES ----------
    if 'live' in T:
        with T['live']:
            st.subheader("🔴 Live Scores Dashboard")
        
            # Fixed auto-refresh - using session state instead of meta refresh
            auto_refresh = st.checkbox("🔄 Auto-refresh every 5 seconds", value=st.session_state.auto_refresh)
        
            if auto_refresh != st.session_state.auto_refresh:
                st.session_state.auto_refresh = auto_refresh
                st.rerun()
        
            if st.session_state.auto_refresh:
                st.info("🔄 Auto-refresh is ON - Data updates every 5 seconds")
                # <script> tags are stripped by Streamlit and a browser reload would log everyone out.
                # A timed fragment re-runs the app inside the SAME session instead.
                if hasattr(st, "fragment"):
                    st.session_state['_fresh_run'] = True

                    @st.fragment(run_every=5)
                    def _auto_refresh_tick():
                        if st.session_state.get('_fresh_run'):
                            st.session_state['_fresh_run'] = False   # first paint after a full run: do nothing
                            return
                        st.session_state.last_update = datetime.now()
                        st.rerun()

                    _auto_refresh_tick()
                else:
                    st.warning("Auto-refresh needs Streamlit 1.37+. Use the 🔄 Refresh button in the sidebar meanwhile.")
        
            if st.session_state.user_role == "admin":
                if not st.session_state.live_scores.empty:
                    station_filter = st.selectbox("Filter by Station", ["All"] + list(st.session_state.live_scores['Station'].unique()), key="live_score_filter")
                else:
                    station_filter = "All"
            elif st.session_state.user_role == "station_manager":
                station_filter = st.session_state.user_stations[0] if st.session_state.user_stations else "All"
            else:
                station_filter = "All"
        
            if station_filter != "All" and not st.session_state.live_scores.empty:
                display_scores = st.session_state.live_scores[
                    st.session_state.live_scores['Station'] == station_filter
                ]
            else:
                display_scores = st.session_state.live_scores
        
            if not display_scores.empty:
                display_scores = display_scores.sort_values('Timestamp', ascending=False)
            
                # Live Scoreboard by Game
                st.subheader("🏆 Live Scoreboard")
                st.caption("Real-time rankings by game type - competitors climb the board as they win!")
            
                # Group scores by game
                games = display_scores['Game'].unique()
            
                if st.session_state.mobile_view:
                    score_cols = st.columns(1)
                else:
                    score_cols = st.columns(min(len(games), 2))
            
                for idx, game in enumerate(games):
                    game_scores = display_scores[display_scores['Game'] == game]
                    winners = game_scores['Winner'].value_counts()
                
                    with score_cols[idx % len(score_cols)]:
                        st.markdown(f"### 🎯 {game}")
                    
                        if not winners.empty:
                            scoreboard_data = []
                            for rank, (player, wins) in enumerate(winners.items(), 1):
                                matches_played = len(game_scores[
                                    (game_scores['Player 1'] == player) | 
                                    (game_scores['Player 2'] == player)
                                ])
                                scoreboard_data.append({
                                    "Rank": f"#{rank}",
                                    "Player": player,
                                    "Wins": wins,
                                    "Matches": matches_played
                                })
                        
                            if scoreboard_data:
                                scoreboard_df = pd.DataFrame(scoreboard_data)
                                st.dataframe(scoreboard_df, use_container_width=True, hide_index=True)
                        else:
                            st.info(f"No scores recorded for {game} yet")
            
                st.divider()
                st.subheader("📋 Live Match Results")
            
                # Show match results
                for idx, row in display_scores.iterrows():
                    # ULTRA-VISIBLE: High contrast white card with bold black text
                    st.markdown(f"""
                    <div style='
                        background-color: #ffffff; 
                        padding: 15px; 
                        border-radius: 10px; 
                        margin: 8px 0; 
                        border-left: 6px solid #00cc00; 
                        border: 1px solid #d0d0d0;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                        color: #000000;
                    '>
                        <div style='font-size: 15px; margin-bottom: 4px;'>
                            <strong style='color: #000000; font-size: 16px;'>⏰ {row['Timestamp']}</strong> 
                            | <strong style='color: #000000; font-size: 16px;'>📍 {row['Station']}</strong>
                        </div>
                        <div style='font-size: 15px; margin-bottom: 3px;'>
                            🎮 <span style='color: #000000; font-weight: 500;'>{row['Game']}</span> 
                            | <span style='color: #000000; font-weight: 500;'>{row['Age Group']}</span>
                        </div>
                        <div style='font-size: 15px; margin-bottom: 3px;'>
                            👤 <span style='color: #000000; font-weight: 500;'>{row['Player 1']}</span> 
                            vs <span style='color: #000000; font-weight: 500;'>{row['Player 2']}</span>
                        </div>
                        <div style='font-size: 16px; margin-bottom: 3px;'>
                            📊 Score: <strong style='color: #000000; font-size: 18px;'>{row['Score']}</strong>
                        </div>
                        <div style='font-size: 16px; margin-bottom: 3px;'>
                            🏆 Winner: <strong style='color: #006600; font-size: 17px;'>{row['Winner']}</strong>
                        </div>
                        <div style='color: #888888; font-size: 12px; margin-top: 5px; border-top: 1px solid #eeeeee; padding-top: 5px;'>
                            Recorded by: {row['Recorded By']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
                st.subheader("📊 Live Score Statistics")
                if st.session_state.mobile_view:
                    stat_cols = st.columns(2)
                else:
                    stat_cols = st.columns(3)
            
                total_matches = len(display_scores)
                unique_winners = display_scores['Winner'].nunique()
            
                if not display_scores.empty:
                    top_winner = display_scores['Winner'].value_counts().index[0]
                    top_winner_wins = display_scores['Winner'].value_counts().values[0]
                else:
                    top_winner = "N/A"
                    top_winner_wins = 0
            
                stat_cols[0].metric("🏆 Total Matches", total_matches)
                stat_cols[1].metric("👥 Unique Winners", unique_winners)
                if len(stat_cols) > 2:
                    stat_cols[2].metric("⭐ Top Winner", f"{top_winner} ({top_winner_wins} wins)")
                else:
                    stat_cols[0].metric("⭐ Top Winner", f"{top_winner} ({top_winner_wins} wins)")
            
                # Export live scores
                st.divider()
                st.subheader("📥 Export Live Scoreboard")
            
                col1, col2 = st.columns(2)
            
                with col1:
                    st.download_button(
                        label="📊 Download Live Scores CSV",
                        data=display_scores.to_csv(index=False),
                        file_name=f"RRR_LiveScores_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
                with col2:
                    if st.button("📄 Generate Scoreboard PDF", use_container_width=True):
                        pdf_path = generate_live_scoreboard_pdf()
                        if pdf_path:
                            with open(pdf_path, 'rb') as f:
                                st.session_state['scoreboard_pdf'] = f.read()
                            try:
                                os.unlink(pdf_path)
                            except Exception:
                                pass
                        else:
                            st.warning("No live scores to export")
                    if st.session_state.get('scoreboard_pdf'):
                        st.download_button(
                            label="📥 Download Scoreboard PDF",
                            data=st.session_state['scoreboard_pdf'],
                            file_name=f"RRR_Scoreboard_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
            else:
                st.info("No live scores yet. Start a tournament and enter results!")
    
    # ---------- TAB 8: RECRUITING ----------
    if 'recruiting' in T:
        with T['recruiting']:
            st.subheader("⭐ Recruiting Dashboard")
        
            if st.session_state.user_role == "station_manager":
                display_players = st.session_state.players[
                    st.session_state.players['Station'].isin(st.session_state.user_stations)
                ]
            else:
                display_players = st.session_state.players
        
            display_players = fix_dataframe_types(display_players)
        
            if not display_players.empty:
            
                if st.session_state.mobile_view:
                    col1, col2 = st.columns(2)
                else:
                    col1, col2, col3, col4 = st.columns(4)
            
                total = len(display_players)
                elite = len(display_players[display_players['Potential'] >= 80])
                high = len(display_players[(display_players['Potential'] >= 70) & (display_players['Potential'] < 80)])
                highlighted = len(display_players[display_players['Highlighted'] == True])
            
                col1.metric("👥 Total Players", total)
                col2.metric("🌟 Elite (80%+)", elite, delta="⭐")
                if not st.session_state.mobile_view:
                    col3.metric("📈 High (70-79%)", high)
                    col4.metric("⭐ Highlighted", highlighted)
                else:
                    col1.metric("📈 High", high)
                    col2.metric("⭐ Highlighted", highlighted)
            
                st.divider()
            
                st.subheader("📊 Player Potential Rankings")
            
                sorted_players = display_players.sort_values('Potential', ascending=False)
            
                for idx, row in sorted_players.iterrows():
                    potential = int(row['Potential'])
                    # STRONGER, MORE VIBRANT COLORS
                    if potential >= 80:
                        color = "#00cc00"  # Bright green
                        bg_color = "#e6ffe6"  # Light green background
                        border_color = "#00cc00"  # Green border
                    elif potential >= 70:
                        color = "#ffaa00"  # Bright orange/gold
                        bg_color = "#fff8e6"  # Light yellow background
                        border_color = "#ffaa00"  # Orange border
                    elif potential >= 60:
                        color = "#ff6600"  # Bright orange
                        bg_color = "#fff0e6"  # Light orange background
                        border_color = "#ff6600"  # Orange border
                    else:
                        color = "#cc3333"  # Bright red
                        bg_color = "#ffe6e6"  # Light red background
                        border_color = "#cc3333"  # Red border
                
                    level = get_potential_level(potential)
                
                    highlighted = "⭐ " if row['Highlighted'] else ""
                
                    st.markdown(f"""
                    <div style='
                        background-color: #ffffff; 
                        padding: 18px; 
                        border-radius: 12px; 
                        margin: 10px 0; 
                        border-left: 8px solid {border_color};
                        border: 2px solid #d0d0d0;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.10);
                    '>
                        <div style='font-size: 18px; font-weight: 700; color: #000000; margin-bottom: 8px;'>
                            {highlighted}{row['Name']}
                        </div>
                        <div style='font-size: 15px; color: #000000; margin-bottom: 5px;'>
                            📅 {row['Age Group']} | 🎮 {row['Game']}
                        </div>
                        <div style='font-size: 16px; color: #000000; margin-bottom: 5px; background-color: {bg_color}; padding: 8px 12px; border-radius: 8px; border-left: 4px solid {border_color};'>
                            📊 Potential: <strong style='color: {color}; font-size: 22px; text-shadow: 0 0 8px {color}40;'>{potential}%</strong> - <span style='color: {color}; font-weight: 700;'>{level}</span>
                        </div>
                        <div style='font-size: 15px; color: #000000; margin-bottom: 4px;'>
                            📌 Station: <strong style='color: #000000;'>{row['Station']}</strong> 
                            | 🏆 Wins: <strong style='color: #000000;'>{int(row['Wins'])}</strong> 
                            | ❌ Losses: <strong style='color: #000000;'>{int(row['Losses'])}</strong>
                        </div>
                        {f'<div style="font-size: 14px; color: #333333; margin-top: 8px; background-color: #f5f5f5; padding: 8px 12px; border-radius: 6px; border-left: 3px solid #999999;">📝 {row["Recruiter Notes"]}</div>' if row.get("Recruiter Notes") else ''}
                    </div>
                    """, unsafe_allow_html=True)
                
                    if st.session_state.mobile_view:
                        col1, col2 = st.columns(2)
                    else:
                        col1, col2 = st.columns(2)
                
                    with col1:
                        if not row['Highlighted'] and potential >= 70:
                            if st.button(f"⭐ Highlight {row['Name']}", key=f"highlight_{idx}"):
                                player_idx = st.session_state.players[st.session_state.players['Name'] == row['Name']].index[0]
                                st.session_state.players.loc[player_idx, 'Highlighted'] = True
                                st.session_state.players.loc[player_idx, 'Highlight Reason'] = f"Manual Highlight - {level}"
                                if row['Name'] in st.session_state.highlight_overrides:
                                    st.session_state.highlight_overrides.remove(row['Name'])
                                st.rerun()
                
                    with col2:
                        if row['Highlighted']:
                            if st.button(f"❌ Remove Highlight {row['Name']}", key=f"remove_{idx}"):
                                player_idx = st.session_state.players[st.session_state.players['Name'] == row['Name']].index[0]
                                st.session_state.players.loc[player_idx, 'Highlighted'] = False
                                st.session_state.players.loc[player_idx, 'Highlight Reason'] = ''
                                if row['Name'] not in st.session_state.highlight_overrides:
                                    st.session_state.highlight_overrides.append(row['Name'])
                                st.rerun()
            
                st.subheader("📥 Export Recruiting Report")
            
                render_player_exports(display_players, key_prefix="recruiting")
            else:
                st.info("No players in your station(s). Add players to start recruiting!")
    
    # ---------- TAB 9: MATCH DETAILS ----------
    if 'match' in T:
        with T['match']:
            st.subheader("📊 Match Details Viewer")
        
            st.info("""
            **View detailed statistics for completed matches**
            Select a completed match to see all tracked stats including game-specific metrics.
            """)
        
            # Get completed matches with stats
            completed_matches = st.session_state.bracket[
                st.session_state.bracket['Status'] == 'Completed'
            ]
        
            if not completed_matches.empty:
                # Filter to matches that have stats
                matches_with_stats = completed_matches[
                    (completed_matches['Stats'] != '') & 
                    (completed_matches['Stats'] != '{}') &
                    (completed_matches['Stats'].notna())
                ]
            
                if not matches_with_stats.empty:
                    match_options = matches_with_stats['Match ID'].tolist()
                    selected_match_view = st.selectbox(
                        "Select Match to View Details",
                        match_options,
                        key="match_view_select"
                    )
                
                    if selected_match_view:
                        match_data = completed_matches[
                            completed_matches['Match ID'] == selected_match_view
                        ].iloc[0]
                    
                        # Check if individual match
                        is_individual = match_data.get('Match Mode') == 'Individual'
                    
                        # Show match summary
                        st.subheader("📋 Match Summary")
                        if st.session_state.mobile_view:
                            col1, col2 = st.columns(2)
                        else:
                            col1, col2, col3, col4 = st.columns(4)
                    
                        with col1:
                            st.metric("🎮 Game", match_data['Game'])
                        with col2:
                            if is_individual:
                                st.metric("🏆 Player", match_data['Player 1'])
                            else:
                                st.metric("🏆 Winner", match_data['Winner'])
                        if not st.session_state.mobile_view:
                            with col3:
                                st.metric("📊 Score", match_data['Score'])
                            with col4:
                                st.metric("📌 Station", match_data['Station'])
                        else:
                            with col1:
                                st.metric("📊 Score", match_data['Score'])
                            with col2:
                                st.metric("📌 Station", match_data['Station'])
                    
                        if is_individual:
                            st.info(f"🎯 Individual Match Mode - {match_data['Player 1']} competed solo")
                    
                        st.divider()
                    
                        # Display stats
                        if match_data.get('Stats') and match_data['Stats'] not in ['', '{}', 'nan']:
                            try:
                                stats_data = json.loads(match_data['Stats'])
                                game_name = match_data['Game']
                            
                                if is_individual:
                                    display_individual_match_stats(
                                        stats_data,
                                        game_name,
                                        match_data['Player 1']
                                    )
                                else:
                                    display_match_stats(
                                        stats_data,
                                        game_name,
                                        match_data['Player 1'],
                                        match_data['Player 2']
                                    )
                            except Exception as e:
                                st.warning(f"Could not load stats for this match: {str(e)}")
                        else:
                            st.info("No detailed stats recorded for this match. Stats are added when entering match results.")
                else:
                    st.info("No matches with detailed stats available. Complete matches and add stats to see them here.")
            else:
                st.info("No completed matches yet. Complete matches to see details here.")
    
    # ---------- TAB 10: HELP REQUESTS ----------
    if st.session_state.user_role == "station_manager":
        with T['help']:
            st.subheader("🆘 Request Help")
            st.info("If you need assistance, send a request to the Admin.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                help_topic = st.selectbox("Issue Type", [
                    "Technical Issue",
                    "Player Management",
                    "Tournament Issue",
                    "Station Problem",
                    "Live Scores Issue",
                    "Recruiting Question",
                    "Equipment Problem",
                    "Other"
                ], key="help_topic_select")
            
            with col2:
                station = st.selectbox("Station", st.session_state.user_stations if st.session_state.user_stations else ["Station 1"], key="help_station_select")
            
            help_message = st.text_area("Describe your issue in detail", height=150)
            
            if st.button("📤 Send Help Request", use_container_width=True):
                if help_message:
                    request_id = create_help_request(
                        station,
                        help_topic,
                        help_message,
                        st.session_state.user_name
                    )
                    
                    st.success(f"✅ Help request {request_id} sent to Admin!")
                    st.info("📋 Your request has been logged. Admin will respond shortly.")
                    
                    st.subheader("📋 Request Summary")
                    st.write(f"**Request ID:** {request_id}")
                    st.write(f"**Station:** {station}")
                    st.write(f"**Issue Type:** {help_topic}")
                    st.write(f"**Message:** {help_message}")
                    st.write(f"**Status:** Pending")
                    st.write(f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    st.error("Please describe your issue")
            
            st.divider()
            st.subheader("📋 My Help Requests")
            
            my_requests = st.session_state.help_requests[
                st.session_state.help_requests['Requested By'] == st.session_state.user_name
            ]
            
            if not my_requests.empty:
                for idx, row in my_requests.iterrows():
                    status_color = "🟡" if row['Status'] == 'Pending' else "🟢"
                    st.markdown(f"""
                    <div style='background-color: #f8f9fa; padding: 10px; border-radius: 10px; margin: 5px 0; border-left: 5px solid {'#ffaa00' if row['Status'] == 'Pending' else '#00aa00'}; color: #1a1a1a;'>
                        <strong style='color: #1a1a1a;'>{status_color} {row['Request ID']}</strong> - {row['Issue Type']}
                        <br>
                        <span style='color: #666666;'>{row['Timestamp']}</span>
                        <br>
                        Status: <strong>{row['Status']}</strong>
                        {f'<br>Admin Response: {row["Admin Response"]}' if row['Admin Response'] else ''}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No help requests yet")
    
    elif st.session_state.user_role == "admin":
        with T['help']:
            st.subheader("🆘 Help Request Management")
            
            st.subheader("🔔 Notification Center")
            
            admin_notifications = st.session_state.notifications[
                st.session_state.notifications['Target Role'] == 'admin'
            ].sort_values('Timestamp', ascending=False)
            
            if not admin_notifications.empty:
                for idx, row in admin_notifications.iterrows():
                    read_mark = "✅" if row['Read'] else "🆕"
                    color = "#e8f5e9" if row['Read'] else "#fff3e0"
                    
                    st.markdown(f"""
                    <div style='background-color: {color}; padding: 10px; border-radius: 10px; margin: 5px 0; border-left: 5px solid {'#4caf50' if row['Read'] else '#ff9800'}; color: #1a1a1a;'>
                        <strong style='color: #1a1a1a;'>{read_mark} {row['Message']}</strong>
                        <br>
                        <span style='color: #666666; font-size: 12px;'>{row['Timestamp']}</span>
                        {f'<br>Request: {row["Related Request"]}' if row['Related Request'] else ''}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if not row['Read']:
                        if st.button(f"✅ Mark as Read", key=f"read_{idx}"):
                            mark_notification_read(row['Notification ID'])
                            st.rerun()
            else:
                st.info("No notifications")
            
            st.divider()
            
            st.subheader("📋 Pending Help Requests")
            
            pending_requests = st.session_state.help_requests[
                st.session_state.help_requests['Status'] == 'Pending'
            ].sort_values('Timestamp', ascending=False)
            
            if not pending_requests.empty:
                for idx, row in pending_requests.iterrows():
                    st.markdown(f"""
                    <div style='background-color: #fff3e0; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 5px solid #ff6b6b; color: #1a1a1a;'>
                        <strong style='color: #1a1a1a;'>🆘 {row['Request ID']}</strong> - {row['Issue Type']}
                        <br>
                        📌 Station: {row['Station']} | 👤 Requested by: {row['Requested By']}
                        <br>
                        ⏰ {row['Timestamp']}
                        <br>
                        📝 {row['Message']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        admin_response = st.text_input(f"Response for {row['Request ID']}", placeholder="Type your response...", key=f"response_{idx}")
                    with col2:
                        if st.button(f"✅ Resolve", key=f"resolve_{idx}"):
                            if admin_response:
                                resolve_help_request(
                                    row['Request ID'],
                                    admin_response,
                                    st.session_state.user_name
                                )
                                
                                create_notification(
                                    'help_resolved',
                                    f"✅ Your help request {row['Request ID']} has been resolved by Admin",
                                    row['Request ID'],
                                    'station_manager'
                                )
                                
                                st.success(f"✅ Request {row['Request ID']} resolved!")
                                st.rerun()
                            else:
                                st.warning("Please enter a response")
            else:
                st.info("🎉 No pending help requests! All stations are running smoothly.")
            
            st.divider()
            st.subheader("📋 Resolved Requests History")
            
            resolved_requests = st.session_state.help_requests[
                st.session_state.help_requests['Status'] == 'Resolved'
            ].sort_values('Resolved At', ascending=False)
            
            if not resolved_requests.empty:
                for idx, row in resolved_requests.head(10).iterrows():
                    st.markdown(f"""
                    <div style='background-color: #e8f5e9; padding: 10px; border-radius: 10px; margin: 5px 0; border-left: 5px solid #4caf50; color: #1a1a1a;'>
                        <strong style='color: #1a1a1a;'>✅ {row['Request ID']}</strong> - {row['Issue Type']}
                        <br>
                        📌 Station: {row['Station']} | Resolved by: {row['Resolved By']}
                        <br>
                        ⏰ Resolved: {row['Resolved At']}
                        <br>
                        📝 Response: {row['Admin Response']}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No resolved requests yet")
    
    # ---------- TAB 11: SAVE/LOAD ----------
    if 'saveload' in T:
        with T['saveload']:
            st.subheader("💾 Save & Load Data")
        
            st.info("""
            **How Save/Load Works:**
            - **Save:** Exports all your data to a JSON file
            - **Load:** Imports data from a JSON file
            - **Use Cases:**
              - Backup your tournament data
              - Transfer data between computers
              - Offline storage
              - Share data with other organizers
            """)
        
            col1, col2 = st.columns(2)
        
            with col1:
                st.subheader("💾 Save Data")
            
                st.write("**Data to be saved:**")
                st.write(f"- 👥 Players: {len(st.session_state.players)}")
                st.write(f"- 🏆 Tournament Matches: {len(st.session_state.bracket)}")
                st.write(f"- 🔴 Live Scores: {len(st.session_state.live_scores)}")
                st.write(f"- 🆘 Help Requests: {len(st.session_state.help_requests)}")
                st.write(f"- 📌 Stations: {len(st.session_state.station_config)}")
                st.write(f"- 🏆 Champions: {len([g for g in st.session_state.tournament_champions if st.session_state.tournament_champions[g]['champion']])}")
                st.write(f"- 📜 Past Tournaments: {len(st.session_state.tournament_history)}")
            
                st.download_button(
                    label="💾 Download RRR_Data.json",
                    data=save_data_to_json(),
                    file_name=f"RRR_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
            with col2:
                st.subheader("📤 Load Data")
            
                st.write("**Load from file:**")
                st.write("Upload a previously saved JSON file")
            
                uploaded_file = st.file_uploader(
                    "Choose a JSON file",
                    type=['json'],
                    help="Upload a .json file saved from this system"
                )
            
                if uploaded_file is not None:
                    try:
                        file_content = uploaded_file.read().decode('utf-8')
                    
                        data_preview = json.loads(file_content)
                        st.write("**File contains:**")
                        st.write(f"- Players: {len(data_preview.get('players', []))}")
                        st.write(f"- Tournament Matches: {len(data_preview.get('bracket', []))}")
                        st.write(f"- Live Scores: {len(data_preview.get('live_scores', []))}")
                        st.write(f"- Help Requests: {len(data_preview.get('help_requests', []))}")
                        st.write(f"- Champions: {len(data_preview.get('tournament_champions', {}))}")
                        st.write(f"- Past Tournaments: {len(data_preview.get('tournament_history', []))}")
                    
                        if st.button("📤 Load Data", use_container_width=True):
                            success, message = load_data_from_json(file_content)
                            if success:
                                st.success(message)
                                st.info("🔄 Refreshing page to show loaded data...")
                                st.rerun()
                            else:
                                st.error(message)
                            
                    except json.JSONDecodeError:
                        st.error("❌ Invalid JSON file. Please upload a valid RRR data file.")
                    except Exception as e:
                        st.error(f"❌ Error reading file: {str(e)}")
        
            st.divider()
            st.subheader("📊 Current Data Summary")
        
            if st.session_state.mobile_view:
                col1, col2 = st.columns(2)
            else:
                col1, col2, col3, col4 = st.columns(4)
        
            col1.metric("👥 Players", len(st.session_state.players))
            col2.metric("🏆 Matches", len(st.session_state.bracket))
            if not st.session_state.mobile_view:
                col3.metric("🔴 Live Scores", len(st.session_state.live_scores))
                col4.metric("🆘 Help Requests", len(st.session_state.help_requests))
            else:
                col1.metric("🔴 Live Scores", len(st.session_state.live_scores))
                col2.metric("🆘 Help Requests", len(st.session_state.help_requests))
        
            st.caption(f"💡 Data is stored in memory. Use 'Save' to export, 'Load' to import.")
            st.caption(f"🕐 Current session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ---------- EXPORT TAB (recruiter) ----------
    if 'export' in T:
        with T['export']:
            st.subheader("📥 Export Center")
            st.caption("Download player data for scouting and follow-up")
            _exp_players = fix_dataframe_types(st.session_state.players)
            if _exp_players.empty:
                st.info("No players to export yet.")
            else:
                render_player_exports(_exp_players, key_prefix="export_tab")
                if st.button("📄 Build Tournament PDF Report", use_container_width=True, key="rec_pdf_build"):
                    _pdf = generate_pdf_report()
                    if _pdf:
                        with open(_pdf, 'rb') as _f:
                            st.session_state['recruiter_pdf'] = _f.read()
                        try:
                            os.unlink(_pdf)
                        except Exception:
                            pass
                    else:
                        st.warning("No tournament data yet.")
                if st.session_state.get('recruiter_pdf'):
                    st.download_button("📥 Download Tournament PDF", data=st.session_state['recruiter_pdf'],
                                       file_name=f"RRR_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                                       mime="application/pdf", use_container_width=True, key="rec_pdf_dl")
    
    # ---------- TAB 12: ADMIN PANEL ----------
    if st.session_state.user_role == "admin":
        with T['admin']:
            st.subheader("⚙️ Admin Panel")
            
            st.info("👑 Welcome to the Admin Panel")
            
            # Admin tabs
            admin_tabs = st.tabs(["📊 Overview", "👥 User Management", "📍 Station Management", "📜 Tournament History"])
            
            # Overview Tab
            with admin_tabs[0]:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 System Overview")
                    st.write(f"**Total Players:** {len(st.session_state.players)}")
                    st.write(f"**Active Players:** {len(st.session_state.players[st.session_state.players['Status'] == 'Active'])}")
                    st.write(f"**Highlighted Players:** {len(st.session_state.players[st.session_state.players['Highlighted'] == True])}")
                    st.write(f"**Total Matches:** {len(st.session_state.bracket)}")
                    st.write(f"**Live Scores:** {len(st.session_state.live_scores)}")
                    st.write(f"**Help Requests:** {len(st.session_state.help_requests)}")
                    st.write(f"**Pending Help:** {len(st.session_state.help_requests[st.session_state.help_requests['Status'] == 'Pending'])}")
                    st.write(f"**Tournament Active:** {'✅ Yes' if st.session_state.tournament_active else '❌ No'}")
                    
                    # Show champions count
                    champion_count = len([g for g in st.session_state.tournament_champions if st.session_state.tournament_champions[g]['champion']])
                    st.write(f"**🏆 Champions Crowned:** {champion_count}")
                    st.write(f"**📜 Past Tournaments:** {len(st.session_state.tournament_history)}")
                
                with col2:
                    st.subheader("📌 Station Summary")
                    if not st.session_state.players.empty:
                        # Ensure types before aggregation
                        players_copy = fix_dataframe_types(st.session_state.players)
                        station_summary = players_copy.groupby('Station').agg({
                            'Name': 'count',
                            'Wins': 'sum',
                            'Highlighted': 'sum'
                        }).reset_index()
                        station_summary.columns = ['Station', 'Players', 'Total Wins', 'Highlighted']
                        st.dataframe(station_summary, use_container_width=True)
                    else:
                        st.info("No players in system")
                    
                    st.divider()
                    st.subheader("🔄 System Actions")
                    
                    confirm_clear = st.checkbox("I understand this permanently erases ALL players, matches, scores and history", key="confirm_clear_all")
                    if st.button("🗑️ Clear All Data", use_container_width=True, disabled=not confirm_clear):
                        st.session_state.players = pd.DataFrame(columns=[
                            'Name', 'Age', 'Age Group', 'Game', 'Station', 
                            'Wins', 'Losses', 'Status', 'Potential', 'Highlighted', 
                            'Recruiter Notes', 'Highlight Reason'
                        ])
                        st.session_state.bracket = empty_bracket()
                        st.session_state.live_scores = pd.DataFrame(columns=[
                            'Timestamp', 'Station', 'Match ID', 'Player 1', 'Player 2', 
                            'Score', 'Winner', 'Recorded By', 'Age Group', 'Game'
                        ])
                        st.session_state.help_requests = pd.DataFrame(columns=[
                            'Request ID', 'Timestamp', 'Station', 'Requested By', 
                            'Issue Type', 'Message', 'Status', 'Admin Response', 
                            'Resolved By', 'Resolved At'
                        ])
                        st.session_state.notifications = pd.DataFrame(columns=[
                            'Notification ID', 'Timestamp', 'Type', 'Message', 
                            'Related Request', 'Read', 'Target Role'
                        ])
                        st.session_state.tournament_active = False
                        del st.session_state['tournament_champions']   # init_champions() is a no-op while the key exists
                        init_champions()
                        st.session_state.highlight_overrides = []
                        st.session_state.tournament_balloons_shown = False
                        st.session_state.tournament_history = []
                        st.session_state.past_tournaments = {}
                        
                        for station in st.session_state.station_config.keys():
                            st.session_state.station_config[station]['current'] = 0
                        
                        st.success("✅ All data cleared!")
                        st.rerun()
            
            # User Management Tab
            with admin_tabs[1]:
                st.subheader("👥 User Management")
                
                st.info("""
                **User Management:**
                - Add new users with specific roles
                - Delete users (except admin)
                - Passwords are hashed for security
                - Users can change their own passwords
                """)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("➕ Add New User")
                    new_username = st.text_input("Username")
                    new_password = st.text_input("Password", type="password")
                    new_name = st.text_input("Full Name")
                    new_email = st.text_input("Email")
                    new_role = st.selectbox("Role", ["admin", "station_manager", "recruiter"])
                    
                    if new_role == "station_manager":
                        new_stations = st.multiselect("Stations", list(st.session_state.station_config.keys()))
                    else:
                        new_stations = []
                    
                    if st.button("➕ Create User", use_container_width=True):
                        if new_username and new_password and new_name:
                            success, message = add_user(
                                new_username, 
                                new_password, 
                                new_role, 
                                new_name, 
                                new_email,
                                new_stations
                            )
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                        else:
                            st.warning("Please fill in all required fields")
                
                with col2:
                    st.subheader("👥 Existing Users")
                    
                    users_data = []
                    for username, data in USERS.items():
                        users_data.append({
                            "Username": username,
                            "Name": data["name"],
                            "Role": data["role"],
                            "Email": data.get("email", ""),
                            "Stations": ", ".join(data.get("stations", [])) if data.get("stations") else "All"
                        })
                    
                    if users_data:
                        users_df = pd.DataFrame(users_data)
                        st.dataframe(users_df, use_container_width=True, hide_index=True)
                    
                    st.subheader("🗑️ Delete User")
                    delete_username = st.selectbox("Select User to Delete", [u for u in USERS.keys() if u != "admin"])
                    
                    if st.button("🗑️ Delete User", use_container_width=True):
                        if delete_username:
                            success, message = delete_user(delete_username)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                    
                    st.divider()
                    st.subheader("🔑 Password Change")
                    st.info("Users can change their own passwords from the sidebar")
            
            # Station Management Tab
            with admin_tabs[2]:
                st.subheader("📍 Station Management")
                
                st.info("""
                **Station Management:**
                - Add new gaming stations
                - Remove existing stations (must be empty)
                - Configure station capacities
                """)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("➕ Add Station")
                    new_station_name = st.text_input("Station Name", placeholder="e.g., Station 7")
                    new_station_capacity = st.number_input("Capacity", min_value=2, max_value=20, value=8)
                    
                    if st.button("➕ Add Station", use_container_width=True):
                        if new_station_name:
                            success, message = add_station(new_station_name, new_station_capacity)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                        else:
                            st.warning("Please enter a station name")
                
                with col2:
                    st.subheader("🗑️ Remove Station")
                    
                    # Get stations with players
                    stations_with_players = []
                    for station, config in st.session_state.station_config.items():
                        players = st.session_state.players[st.session_state.players['Station'] == station]
                        if not players.empty:
                            stations_with_players.append(f"{station} ({len(players)} players)")
                    
                    if stations_with_players:
                        st.warning("⚠️ Stations with players cannot be removed. Move players first.")
                        st.write("**Stations with players:**")
                        for s in stations_with_players:
                            st.write(f"- {s}")
                    
                    remove_station_name = st.selectbox("Select Station to Remove", list(st.session_state.station_config.keys()))
                    
                    if st.button("🗑️ Remove Station", use_container_width=True):
                        if remove_station_name:
                            success, message = remove_station(remove_station_name)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                
                st.divider()
                st.subheader("📊 Current Stations")
                
                station_data = []
                for station, config in st.session_state.station_config.items():
                    status, status_text = get_station_status(station)
                    station_data.append({
                        "Station": station,
                        "Capacity": config["capacity"],
                        "Current Players": config["current"],
                        "Status": status_text,
                        "Available": config["capacity"] - config["current"]
                    })
                
                if station_data:
                    station_df = pd.DataFrame(station_data)
                    st.dataframe(station_df, use_container_width=True, hide_index=True)
            
            # Tournament History Tab
            with admin_tabs[3]:
                st.subheader("📜 Tournament History")
                
                st.info("""
                **Tournament History:**
                - View all saved tournaments
                - Load a past tournament
                - Delete tournaments you no longer need
                """)
                
                if st.session_state.tournament_history:
                    # Display tournament list
                    history_data = []
                    for tournament in st.session_state.tournament_history:
                        history_data.append({
                            "ID": tournament.get("id", "N/A"),
                            "Date": tournament.get("date", "N/A"),
                            "Total Matches": tournament.get("total_matches", 0),
                            "Completed": tournament.get("completed_matches", 0),
                            "Players": len(tournament.get("players", []))
                        })
                    
                    if history_data:
                        history_df = pd.DataFrame(history_data)
                        st.dataframe(history_df, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    st.subheader("📤 Load Tournament")
                    
                    if st.session_state.tournament_history:
                        tournament_ids = [t.get("id", f"T{i:04d}") for i, t in enumerate(st.session_state.tournament_history, 1)]
                        selected_tournament = st.selectbox("Select Tournament to Load", tournament_ids)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("📤 Load Tournament", use_container_width=True):
                                success, message = load_tournament_history(selected_tournament)
                                if success:
                                    st.success(message)
                                    st.info("🔄 Refreshing page to show loaded tournament...")
                                    st.rerun()
                                else:
                                    st.error(message)
                        
                        with col2:
                            if st.button("🗑️ Delete Tournament", use_container_width=True):
                                success, message = delete_tournament_history(selected_tournament)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                else:
                    st.info("No saved tournaments yet. Complete a tournament and save it to history!")
                    
                    # Show current tournament save option
                    if not st.session_state.bracket.empty:
                        st.subheader("💾 Save Current Tournament")
                        
                        total_matches = len(st.session_state.bracket)
                        completed_matches = len(st.session_state.bracket[st.session_state.bracket['Status'] == 'Completed'])
                        
                        st.write(f"**Current Tournament:** {total_matches} matches, {completed_matches} completed")
                        
                        if st.button("💾 Save to History", use_container_width=True):
                            success, message = save_tournament_history()
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)

else:
    # Login screen - removed credentials display
    st.markdown("""
    <div class="press-start-wrap">
        <div class="press-start">PRESS START</div>
        <div class="press-sub">Open the sidebar <b>( &gt; )</b> and log in to enter the arena</div>
        <div class="arcade-row">
            <span>⚽</span><span>🎯</span><span>🥊</span><span>🏎️</span><span>🔫</span><span>🎮</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------- FOOTER ----------
st.divider()
st.caption("🎮 Raw Rhythm Rumble v11.0 - Arcade Arena Edition | Tournaments • Live Scores • Recruiting")

