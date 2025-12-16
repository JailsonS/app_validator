# Trase Soy Facility Validator

A Streamlit application for validating soy facilities using Google Earth Engine and satellite imagery.

## Running Locally

### Prerequisites

- Python 3.8 or higher
- A Google Earth Engine service account with credentials
- Git (for cloning the repository)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/JailsonS/app_validator.git
   cd app_validator
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Streamlit secrets**

   Create a `.streamlit` directory in the project root:
   ```bash
   mkdir -p .streamlit && \
   gcloud iam service-accounts keys create service_account.json \
   --iam-account=gee-app@trase-396112.iam.gserviceaccount.com
   ```

5. **Run the application**
   ```bash
   python -m streamlit run app.py
   ```

6. **Access the app**

   The application will automatically open in your default browser at `http://localhost:8501`

## Project Structure

```
app_validator/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── helpers/
│   ├── gee_functions.py   # Google Earth Engine helper functions
│   └── gsheet_functions.py # Google Sheets helper functions
└── public/
    └── images/            # Static images (logos, etc.)
```
