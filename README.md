# PropCert Automate (PCAS)

PropCert Automate is a modern, responsive Python Desktop Application built with PySide6 (Qt) to help property managers effortlessly track, store, and manage property compliance certificates (e.g., Gas Safety Certificates, EICRs, Fire Alarms).

## 🚀 Features

* **Smart PDF Filing System:** Automatically routes uploaded PDFs into a beautifully structured, hierarchical folder system (`C:\Office Workfiles\[Certificate Type]\[Company]\[Property]\[Flat]`).
* **Custom Folder Overrides:** Set custom destination folders for specific Companies, Properties, Flats, or entire Certificate Types.
* **Dynamic Certificate Types:** Add new certificate types on the fly. The dashboard automatically generates a new tab and database relations for every new type.
* **Visual Expiry Tracking:** Certificates are highlighted in yellow if they are expiring within 30 days, and in red if they have already expired.
* **Excel Export:** Instantly export your entire property database and expiry dates into a neatly formatted Excel spreadsheet.
* **Property Hierarchy:** Manage Properties by associating them with a parent Company and splitting them into specific Flats (or tag certificates to the "General" property).

## 🛠️ Technology Stack

* **UI Framework:** PySide6 (Qt for Python)
* **Database:** SQLite with SQLAlchemy ORM
* **Data Processing:** pandas, openpyxl
* **Icons:** QtAwesome

## 📦 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YourUsername/PropCert-Automate-PCAS.git
   cd PropCert-Automate-PCAS
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the Database:**
   *(If you are setting this up for the first time or recently updated the software)*
   ```bash
   python migrate_v2.py
   ```

5. **Run the Application:**
   ```bash
   python main.py
   ```

## 📂 Architecture

- `main.py`: The entry point that boots the application.
- `db.py`: SQLAlchemy schemas (Company, Property, Flat, CertificateType, Certificate).
- `file_manager.py`: The engine responsible for resolving custom folder paths and safely copying PDFs.
- `excel_exporter.py`: Handles generating the `.xlsx` exports using pandas.
- `ui/`: Contains all modular UI components (`main_window.py`, `upload_dialog.py`, `manage_properties.py`, `responsive_button.py`).
- `style.qss`: The global CSS stylesheet that gives the app its slick, modern blue design.

## 📝 License

This project is proprietary and built for internal compliance tracking.