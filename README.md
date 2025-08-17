# Resume Analyzer

A Streamlit-based application for analyzing resumes.

## Setup Instructions

### 1. Create a Virtual Environment
It’s recommended to isolate dependencies in a virtual environment.

python -m venv venv

Activate it:

- Windows (PowerShell)
  venv\Scripts\Activate

- macOS/Linux
  source venv/bin/activate

### 2. Install Dependencies
All required packages are listed in util/requirements.txt.

pip install -r util/requirements.txt

To update dependencies in the future:

pip freeze > util/requirements.txt

### 3. Run the Application
Start the Streamlit app with:

streamlit run resume_main.py

⚠️ Note: The application requires credentials to run. Without them, it will not start successfully. Ensure you have the appropriate credentials configured before running.

## Project Structure

├── resume_main.py<br>
├── util/<br>
│   ├── requirements.txt<br>
    └── ...
└── README.md<br>

## Troubleshooting

- ModuleNotFoundError → Make sure your virtual environment is activated before running Streamlit.
- Credential errors → Ensure your credentials are properly set up and accessible by the app.

## License
This project is for educational and internal use only.
