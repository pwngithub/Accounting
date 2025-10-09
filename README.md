# Pioneer Broadband Project Performance Dashboard

This Streamlit app visualizes project performance metrics directly from a live Google Sheet.

## 🚀 Features

- Reads from a live Google Sheet (via CSV export link)
- Automatic refresh every 5 minutes
- Interactive filtering by project type
- KPI metrics and completion progress
- Altair bar charts and progress bars

## 🛠️ Setup

1. Ensure your Google Sheet is shared with **Anyone with the link → Viewer**.
2. Clone or unzip the project.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```

## 🔗 Google Sheet Used

[View Sheet](https://docs.google.com/spreadsheets/d/1iiBe4CLYPlr_kpIOuvzxLliwA0ferGtBRhtnMLfhOQg/edit?usp=sharing)
