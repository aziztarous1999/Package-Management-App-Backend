# 📦 Package Management App – Backend

A simple **package management system** built with **Flask (Python)**, **MongoDB**, and designed to be consumed by a **React Native frontend (Expo)**.

This backend allows senders to:

- Create a package (colis) with recipient details.
- Retrieve all packages of a sender.
- Track a package by its tracking ID.

---

## 🛠 Tech Stack

- **Backend**: Flask (Python 3.11.4)
- **Database**: MongoDB
- **Frontend**: React Native (Expo)
- **Other**: dotenv, flask-cors

---

## ⚙️ Installation & Setup (Windows)

### 1️. Clone the repository

```powershell
git clone https://github.com/<your-username>/package-management-app.git
cd package-management-app/colis-backend
```

### 2. Create virtual environment

```powershell
   python -m venv venv
   .\venv\Scripts\activate
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

### 4. Create .env file

```
MONGO_URI=mongodb://localhost:27017/colisdb (just an example)
PORT=5000
```

### 5. Run app

```
python app.py
```