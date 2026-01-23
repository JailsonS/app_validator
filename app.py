import streamlit as st
import ee
import geemap.foliumap as geemap
import os
import json
import streamlit.components.v1 as components
from helpers.gee_functions import get_mapbiomas_image, get_sentinel_2_image
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

MAPBIOMAS_PALETTE = [
    "#ffffff",
    "#32a65e",
    "#32a65e",
    "#1f8d49",
    "#7dc975",
    "#04381d",
    "#026975",
    "#000000",
    "#000000",
    "#7a6c00",
    "#ad975a",
    "#519799",
    "#d6bc74",
    "#d89f5c",
    "#FFFFB2",
    "#edde8e",
    "#000000",
    "#000000",
    "#f5b3c8",
    "#C27BA0",
    "#db7093",
    "#ffefc3",
    "#db4d4f",
    "#ffa07a",
    "#d4271e",
    "#db4d4f",
    "#0000FF",
    "#000000",
    "#000000",
    "#ffaa5f",
    "#9c0027",
    "#091077",
    "#fc8114",
    "#2532e4",
    "#93dfe6",
    "#9065d0",
    "#d082de",
    "#000000",
    "#000000",
    "#f5b3c8",
    "#c71585",
    "#f54ca9",
    "#cca0d4",
    "#dbd26b",
    "#807a40",
    "#e04cfa",
    "#d68fe2",
    "#9932cc",
    "#e6ccff",
    "#02d659",
    "#ad5100",
    "#000000",
    "#000000",
    "#000000",
    "#000000",
    "#000000",
    "#000000",
    "#CC66FF",
    "#FF6666",
    "#006400",
    "#8d9e8b",
    "#f5d5d5",
    "#ff69b4",
    "#ebf8b5",
    "#000000",
    "#000000",
    "#91ff36",
    "#7dc975",
    "#e97a7a",
    "#0fffe3"
]

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

if 'obs_field' not in st.session_state:
    st.session_state.obs_field = ''

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

    # Automatically move to next index after saving
    next_index()

def next_index():
    if st.session_state.current_index < len(st.session_state.facility_list) - 1:
        st.session_state.current_index += 1
        #st.session_state.obs_input = ''
        #st.session_state.obs_field = ''

def prev_index():
    if st.session_state.current_index > 0:
        st.session_state.current_index -= 1
        st.session_state.obs_input = ''
        st.session_state.obs_field = ''

def load_samples(asset_id):
    fc = ee.FeatureCollection(asset_id)
    ids = fc.aggregate_array('system:index').getInfo()

    st.session_state.samples_fc = fc
    st.session_state.facility_list = ids
    st.session_state.current_index = 0
    st.session_state.start_index = '0'
    # st.session_state.round_number = '1'
    st.session_state.obs_field = ''

def set_index():
    st.session_state.current_index = int(st.session_state.start_index)

def set_round():
    st.session_state.round_number = int(st.session_state.round)

def set_obs():
    st.session_state.obs_input = st.session_state.obs_field

def handle_save(choice, asset_samples):
    # Retrieve the observation from the state before clearing it
    observation = st.session_state.obs_field
    
    # Save the data
    save_validation(choice, asset_samples, observation)
    
    # Clear the text area by resetting its key in session_state
    st.session_state.obs_field = ""


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

    mapbiomas_lulc = get_mapbiomas_image(year=2024)

    Map = geemap.Map(
        add_google_map=False
    )

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
    Map.add_tile_layer(google_satellite_url, name="Google Satellite", attribution="Google", base_layer=True)

    # Split map
    Map.split_map(left_layer)

    # Add LULC layer
    Map.addLayer(mapbiomas_lulc, {
        'min': 0, 'max': 69,
        'palette': MAPBIOMAS_PALETTE
    }, 'LULC - 2024', True, 0.5)

    # Add facilities layer
    Map.addLayer(fc, {}, 'Facilities')
    Map.centerObject(facility, 16)

    # Display in Streamlit
    Map.to_streamlit(height=720)

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
    
    # st.text_input(
    #     "Observation (optional)", 
    #     key="obs_field", 
    #     placeholder="Add any notes here...",
    #     on_change=set_obs,
    #     value=st.session_state.obs_input
    # )

    observation = st.text_area(
        "Observation (optional)", 
        key="obs_field",
        placeholder="Add any notes here..." 
    )

    if st.button(
        "Save and move to next index", 
        on_click=handle_save, 
        args=(choice, user['asset_samples'])
    ):
        st.success(f"Saved: {int(st.session_state.current_index) - 1} → {choice}")


    c1, c2, c3 = st.columns([1,1,1])

    with c1:
        st.metric(label="Index", value=st.session_state.current_index)

    with c2:
        st.button("⬅ Previous", on_click=prev_index)

    with c3:
        st.button("Next ➡", on_click=next_index)
    
    show_facility()

    # Add the legend in a horizontal format
    st.markdown("---")

    # Custom CSS for the legend layout
    legend_html = """
    <div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: start; background-color: #f0f2f6; padding: 15px; border-radius: 10px;">
    """
    legend_items = [
        [MAPBIOMAS_PALETTE[0], 'No Data'],
        [MAPBIOMAS_PALETTE[3], 'Forest Formation'],
        [MAPBIOMAS_PALETTE[4], 'Savanna Formation'],
        [MAPBIOMAS_PALETTE[5], 'Mangrove'],
        [MAPBIOMAS_PALETTE[49], 'Wooded Restinga'],
        [MAPBIOMAS_PALETTE[11], 'Natural Wetland'],
        [MAPBIOMAS_PALETTE[12], 'Grassland'],
        [MAPBIOMAS_PALETTE[32], 'Salt Flat'],
        [MAPBIOMAS_PALETTE[29], 'Rocky Outcrop'],
        [MAPBIOMAS_PALETTE[50], 'Herbaceous Restinga'],
        [MAPBIOMAS_PALETTE[13], 'Other non-Forest Formations'],
        [MAPBIOMAS_PALETTE[18], 'Agriculture'],
        [MAPBIOMAS_PALETTE[39], 'Soybean'],
        [MAPBIOMAS_PALETTE[20], 'Sugar Cane'],
        [MAPBIOMAS_PALETTE[40], 'Rice'],
        [MAPBIOMAS_PALETTE[62], 'Cotton'],
        [MAPBIOMAS_PALETTE[41], 'Other Temporary Crops'],
        [MAPBIOMAS_PALETTE[46], 'Coffee'],
        [MAPBIOMAS_PALETTE[47], 'Citrus'],
        [MAPBIOMAS_PALETTE[35], 'Oil Palm'],
        [MAPBIOMAS_PALETTE[48], 'Other Perennial Crops'],
        [MAPBIOMAS_PALETTE[9], 'Forest Plantation'],
        [MAPBIOMAS_PALETTE[15], 'Pasture'],
        [MAPBIOMAS_PALETTE[21], 'Mosaic of Uses'],
        [MAPBIOMAS_PALETTE[22], 'Non-Vegetated Area'],
        [MAPBIOMAS_PALETTE[23], 'Beach and Dune'],
        [MAPBIOMAS_PALETTE[24], 'Urban Infrastructure'],
        [MAPBIOMAS_PALETTE[30], 'Mining'],
        [MAPBIOMAS_PALETTE[25], 'Other Non-Vegetated Areas'],
        [MAPBIOMAS_PALETTE[33], 'Water'],
        [MAPBIOMAS_PALETTE[31], 'Aquaculture'],
        [MAPBIOMAS_PALETTE[69], 'Coral Reefs']
    ]

    # 3. Gerar o HTML
    legend_html = """
    <div style="display: flex; flex-wrap: wrap; gap: 10px; justify-content: start; 
                background-color: #f8f9fb; padding: 15px; border-radius: 10px; 
                border: 1px solid #ddd; margin-top: 20px;">
    """

    for color, label in legend_items:
        legend_html += f"""
        <div style="display: flex; align-items: center; background: #f0f2f6; 
                    padding: 4px 8px; border-radius: 4px; min-width: 140px;">
            <div style="width: 14px; height: 14px; background-color: {color}; 
                        border: 1px solid #333; margin-right: 6px; border-radius: 2px;"></div>
            <span style="font-size: 11px; color: #31333F; white-space: nowrap;">{label}</span>
        </div>
        """

    legend_html += "</div>"

    st.write("### Legend MapBiomas")
    st.write("Land use and land cover map at 30-meter spatial resolution for the year 2024")
    components.html(legend_html, height=200, scrolling=True)