import streamlit as st
import ee
import geemap.foliumap as geemap
import os
import json

from helpers.gee_functions import get_sentinel_2_image
from helpers.gsheet_functions import write_validation

st.set_page_config(
    layout="wide",
    page_title="Soy Facility Validator",
    page_icon="🫘"
)

# Initialize EE

service_json = {
  "type": "service_account",
  "project_id":  st.secrets["project_id"],
  "private_key_id": st.secrets["private_key_id"],
  "private_key": st.secrets["pkey"],
  "client_email": st.secrets["client_email"],
  "client_id": "117918267299200083789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": st.secrets["client_x509_cert_url"],
  "universe_domain": "googleapis.com"
}

cred_path = "service_account.json"

if not os.path.exists(cred_path):
    with open(cred_path, "w") as f:
        json.dump(service_json, f)

# Inicializa o Earth Engine
service_account_email = service_json['client_email']
credentials = ee.ServiceAccountCredentials(service_account_email, cred_path)
ee.Initialize(credentials)


# -------------------------------------------------------------------
# Sidebar - Logo + Theme
# -------------------------------------------------------------------
st.sidebar.image("public/images/trase_logo.png", use_container_width=True)

st.sidebar.markdown(
    """
    <h2 style='color:#FF4D4D; text-align:center;'>Trase Soy Facility Validator</h2>
    <hr style='border:1px solid #FF4D4D;'>
    """,
    unsafe_allow_html=True
)


st.sidebar.markdown("### Navigation")

# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------

LIST_USERS = [
    {'user': f'User {i}',
     'asset_samples': f'projects/trase-396112/assets/brazil/logistics/silos/silo_map_v3/validation/silos_added_2024_v4_{i}'
    }
    for i in range(0, 10)
]

# -------------------------------------------------------------------
# Session State
# -------------------------------------------------------------------

if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

if 'round_number' not in st.session_state:
    st.session_state.round_number = 1

if 'facility_list' not in st.session_state:
    st.session_state.facility_list = []

if 'samples_fc' not in st.session_state:
    st.session_state.samples_fc = None

if 'current_user_asset' not in st.session_state:
    st.session_state.current_user_asset = None

if 'previous_user' not in st.session_state:
    st.session_state.previous_user = None

if 'obs_input' not in st.session_state:
    st.session_state.obs_input = ''

# -------------------------------------------------------------------
# Functions
# -------------------------------------------------------------------

def reset_state():
    st.session_state.current_index = 0
    st.session_state.round_number = 1
    st.session_state.facility_list = []
    st.session_state.samples_fc = None
    st.session_state.current_user_asset = None
    st.session_state.obs_input = ''

def save_validation(choice, asset_samples, observation=""):
    fac_index = st.session_state.current_index
    user_name = st.session_state.previous_user
    round_number = st.session_state.round_number

    write_validation(fac_index, choice, user_name, round_number, asset_samples, observation)
    st.success(f"Saved: {fac_index} → {choice}")

    # Automatically move to next index after saving
    next_index()

    # Reset the observation field in session state
    st.session_state.obs_input = ''

def next_index():
    if st.session_state.current_index < len(st.session_state.facility_list) - 1:
        st.session_state.current_index += 1

def prev_index():
    if st.session_state.current_index > 0:
        st.session_state.current_index -= 1

def load_samples(asset_id):
    fc = ee.FeatureCollection(asset_id)
    ids = fc.aggregate_array('system:index').getInfo()

    st.session_state.samples_fc = fc
    st.session_state.facility_list = ids
    st.session_state.current_index = 0
    st.session_state.start_index = '0'
    # st.session_state.round_number = '1'

def set_index():
    st.session_state.current_index = int(st.session_state.start_index)

def set_round():
    st.session_state.round_number = int(st.session_state.round)

def set_obs():
    st.session_state.obs_input = st.session_state.obs_field


def show_facility():
    fc = st.session_state.samples_fc
    idx = st.session_state.current_index

    fac_id = st.session_state.facility_list[idx]
    facility = fc.filter(ee.Filter.eq('system:index', fac_id)).first()
    geom = facility.geometry()

    coord = geom.coordinates().getInfo()
    lon, lat = coord

    maps_url = f"https://www.google.com/maps?q={lat},{lon}"
    st.write(f"📍 [Coord: {lat}, {lon}]({maps_url})")

    image = get_sentinel_2_image(geom, year=2024).clip(
        geom.buffer(1000).bounds()
    )

    Map = geemap.Map()

    left_layer = geemap.ee_tile_layer(
        image,
        {
            'bands': ['red', 'green', 'blue'],
            'min': 0,
            'max': 0.3,
            'gamma': 1.3
        },
        'Sentinel-2 RGB'
    )

    # Right: Google basemap
    # Satellite: Google Maps
    google_satellite_url = "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
    Map.add_tile_layer(google_satellite_url, name="Google Satellite", attribution="Google")

    # Split map
    Map.split_map(left_layer)

    # Add facilities layer
    Map.addLayer(fc, {}, 'Facilities')
    Map.centerObject(facility, 16)

    # Display in Streamlit
    Map.to_streamlit(height=520)

# -------------------------------------------------------------------
# Main UI
# -------------------------------------------------------------------

st.markdown(
    """
    <h1 style='color:#FF4D4D;'>Soy Facility Validator</h1>
    <p style='font-size:18px; color:#555;'>Validate soy storage facilities using satellite imagery.</p>
    <hr style='border:1px solid #FF4D4D;'>
    """,
    unsafe_allow_html=True
)

st.header("Params")

user = st.selectbox("Select User", LIST_USERS, format_func=lambda u: u['user'])

st.text_input(
    label='Which round of validation?',
    placeholder='e.g. 1',
    key='round',
    on_change=set_round
)

# Detect user change
if st.session_state.previous_user != user['user']:
    reset_state()
    st.session_state.previous_user = user['user']

if st.button("Load samples", type="primary"):
    load_samples(user['asset_samples'])

st.text_input(
    label='Start at index',
    placeholder='e.g. 0',
    key='start_index',
    on_change=set_index
)

# -------------------------------------------------------------------
# Validation UI
# -------------------------------------------------------------------

if st.session_state.samples_fc:

    st.subheader("Validation")

    choice = st.selectbox("IS IT A STORAGE FACILITY?", ["YES", "NO", "MAYBE"])
    
    st.text_input(
        "Observation (optional)", 
        key="obs_field", 
        placeholder="Add any notes here...",
        on_change=set_obs,
        value=st.session_state.obs_input

    )

    observation = st.session_state.obs_input

    if st.button("Save and move to next index"):
        save_validation(choice, user['asset_samples'], observation)

    c1, c2, c3 = st.columns([1,1,1])

    with c1:
        st.metric(label="Index", value=st.session_state.current_index)

    with c2:
        st.button("⬅ Previous", on_click=prev_index)

    with c3:
        st.button("Next ➡", on_click=next_index)

    show_facility()
