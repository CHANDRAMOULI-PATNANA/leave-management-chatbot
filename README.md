# 🏖️ Leave Management Chatbot

**Proof-of-Concept** — Mock-based leave request chatbot for interns.

---

## 🧠 Overview
This bot allows employees to:
- ✅ Apply for leave
- ✅ Check leave balance
- ✅ View upcoming leaves
- ✅ Cancel leave requests

**No real database** — Uses mocked JSON-like data persisted in session state.

---

## 🧑‍💻 Tech Stack
- **Language:** Python 3.x
- **UI Framework:** Streamlit (web-based UI)
- **Data Storage:** In-memory (`st.session_state`)
- **Deployment Ready:** Works locally and on Streamlit Cloud

---

## ✨ Features
✅ **Persistent session data** — leave applications and balances persist until the app is stopped.  
✅ **Simple UI** — select options like "Check Balance" or "Apply Leave".  
✅ **Rule-Based** — keyword-driven logic, no NLP.

---

## 🚀 Usage Instructions

### 📂 1. Clone or Download
```bash
git clone https://github.com/YourUsername/leave-management-chatbot.git
cd leave-management-chatbot
