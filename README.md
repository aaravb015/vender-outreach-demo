# Vendor Outreach Tracker Demo

A lightweight Streamlit demo for managing vendor outreach, follow-ups, qualification, and onboarding.

## What the demo includes

- Vendor master list
- Outreach status tracking
- Follow-up queue with overdue / due-today flags
- Vendor detail view
- Pipeline summary
- Basic vendor comparison
- CSV upload and export
- Add-vendor form
- Synthetic sample data

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes

- The demo uses synthetic data only.
- Data entered in the app is stored only in the current Streamlit session.
- A production version could connect to Google Sheets, a database, or a CRM and add authentication, reminders, roles, and audit history.
