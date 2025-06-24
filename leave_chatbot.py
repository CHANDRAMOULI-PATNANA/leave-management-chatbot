import streamlit as st
from datetime import datetime
import re
import dateparser

# --- Mock Data Setup ---
if "employees" not in st.session_state:
    st.session_state.employees = {
        "E001": {
            "name": "John Doe",
            "leave_balance": {"casual": 5, "sick": 2},
            "applied_leaves": []
        }
    }
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

employees = st.session_state.employees
current_user_id = "E001"
date_format = "%Y-%m-%d"

def extract_dates(text):
    # Match a wide variety of date formats, with or without year
    date_patterns = re.findall(
        r"\d{1,2}[-/ ](?:[A-Za-z]{3,9})[-/ ]?\d{0,4}|"         # 10-July, 10-July-2025
        r"(?:[A-Za-z]{3,9})[-/ ]\d{1,2}[-/ ]?\d{0,4}|"         # July-10, July-10-2025
        r"\d{4}-\d{2}-\d{2}|"                                  # 2025-07-10
        r"[A-Za-z]{3,9} \d{1,2},? \d{4}|"                      # July 10, 2025
        r"\d{1,2}[a-z]{2} [A-Za-z]{3,9}|"                      # 5th July
        r"[A-Za-z]{3,9} \d{1,2}",                              # July 5
        text,
    )
    dates = []
    for d in date_patterns:
        parsed = dateparser.parse(d)
        if parsed:
            # If year is missing, assume current year
            if parsed.year == 1900:
                parsed = parsed.replace(year=datetime.now().year)
            dates.append(parsed.strftime("%Y-%m-%d"))
    if len(dates) >= 2:
        return dates[0], dates[1]
    elif len(dates) == 1:
        return dates[0], dates[0]  # treat as single-day leave
    return None, None

def detect_intent(text):
    text_lower = text.lower()
    # If message contains a date and "apply" or "leave", treat as apply_leave
    if re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{1,2})", text_lower) and (
        "apply" in text_lower or "leave" in text_lower
    ):
        return "apply_leave"
    if text_lower.strip() == "check":
        return "check_balance"
    if text_lower.strip() == "upcoming":
        return "view_upcoming"
    if any(word in text_lower for word in ["balance", "how many leaves", "leaves left", "remaining leaves", "check", "status"]):
        return "check_balance"
    if any(word in text_lower for word in ["upcoming", "future", "next", "my leaves"]):
        return "view_upcoming"
    if any(word in text_lower for word in ["cancel", "delete", "remove"]):
        return "cancel_leave"
    return "unknown"

def extract_leave_type(text):
    if "casual" in text.lower():
        return "casual"
    if "sick" in text.lower():
        return "sick"
    return None

def check_leave_balance():
    balance = employees[current_user_id]["leave_balance"]
    return f"You have {balance['casual']} casual and {balance['sick']} sick leaves remaining."

def view_upcoming_leaves():
    leaves = employees[current_user_id]["applied_leaves"]
    upcoming = []
    today = datetime.now().date()
    for leave in leaves:
        leave_start = datetime.strptime(leave["from"], date_format).date()
        if leave_start >= today and leave["status"] == "approved":
            upcoming.append(
                f"{leave['from']} to {leave['to']} for {leave['reason']}"
            )
    if upcoming:
        return "Your upcoming leaves:\n" + "\n".join(f"- {leave}" for leave in upcoming)
    else:
        return "No upcoming leaves."

def apply_leave(from_date, to_date, reason, leave_type):
    balance = employees[current_user_id]["leave_balance"]
    for leave in employees[current_user_id]["applied_leaves"]:
        if (
            leave["from"] == from_date
            and leave["type"] == leave_type
            and leave["status"] == "approved"
        ):
            return f"You have already applied for {leave_type} leave on {from_date}."
    if balance[leave_type] <= 0:
        return f"You don't have enough {leave_type} leaves."
    employees[current_user_id]["applied_leaves"].append(
        {
            "from": from_date,
            "to": to_date,
            "type": leave_type,
            "reason": reason,
            "status": "approved",
        }
    )
    balance[leave_type] -= 1
    return f"Leave applied from {from_date} to {to_date} for {reason}."

def cancel_leave(from_date):
    for leave in employees[current_user_id]["applied_leaves"]:
        if leave["from"] == from_date and leave["status"] == "approved":
            leave["status"] = "cancelled"
            employees[current_user_id]["leave_balance"][leave["type"]] += 1
            return f"Leave on {from_date} canceled successfully."
    return f"No leave found on {from_date}."

def parse_command(user_input):
    # Multi-turn: If waiting for a date for cancel
    if st.session_state.get("awaiting_cancel_date"):
        from_date, _ = extract_dates(user_input)
        if from_date:
            st.session_state.awaiting_cancel_date = False
            return cancel_leave(from_date)
        else:
            return "Please specify the date of the leave you want to cancel (e.g. 2025-06-24)."

    # Multi-turn: If waiting for reason or type for apply_leave (existing logic)
    if "pending_apply" in st.session_state and st.session_state.pending_apply.get("step") == "reason":
        st.session_state.pending_apply["reason"] = user_input
        st.session_state.pending_apply["step"] = "type"
        return "What type of leave? (casual/sick)"
    if "pending_apply" in st.session_state and st.session_state.pending_apply.get("step") == "type":
        leave_type = extract_leave_type(user_input)
        if not leave_type:
            return "Please enter a valid leave type: casual or sick."
        data = st.session_state.pending_apply
        response = apply_leave(
            data["from_date"], data["to_date"], data["reason"], leave_type
        )
        del st.session_state.pending_apply
        return response

    # Detect intent
    intent = detect_intent(user_input)
    if intent == "check_balance":
        return check_leave_balance()
    if intent == "view_upcoming":
        return view_upcoming_leaves()
    if intent == "cancel_leave":
        from_date, _ = extract_dates(user_input)
        if from_date:
            return cancel_leave(from_date)
        else:
            st.session_state.awaiting_cancel_date = True
            return "Please specify the date of the leave you want to cancel (e.g. 2025-06-24)."
    if intent == "apply_leave":
        from_date, to_date = extract_dates(user_input)
        leave_type = extract_leave_type(user_input)
        if from_date and to_date and leave_type:
            reason = user_input  # You can improve this with more NLP
            return apply_leave(from_date, to_date, reason, leave_type)
        elif from_date and to_date:
            st.session_state.pending_apply = {
                "from_date": from_date,
                "to_date": to_date,
                "step": "reason"
            }
            return "What is the reason for your leave?"
        else:
            # If user just says "I want to apply for leave", start the flow
            st.session_state.awaiting_apply_dates = True
            return "Please specify the leave dates (e.g. from 2025-06-24 to 2025-06-28)."

    # Multi-turn: If waiting for dates for apply_leave
    if st.session_state.get("awaiting_apply_dates"):
        from_date, to_date = extract_dates(user_input)
        if from_date and to_date:
            st.session_state.pending_apply = {
                "from_date": from_date,
                "to_date": to_date,
                "step": "reason"
            }
            st.session_state.awaiting_apply_dates = False
            return "What is the reason for your leave?"
        else:
            return "Please specify both start and end dates (e.g. from 2025-06-24 to 2025-06-28)."

    # Handle greetings and small talk
    if any(word in user_input.lower() for word in ["thank", "thanks", "thank you"]):
        return "You're welcome! 😊 Let me know if you need anything else."
    if any(word in user_input.lower() for word in ["hello", "hi", "hey"]):
        return "Hello! How can I assist you with your leaves today?"
    if any(word in user_input.lower() for word in ["bye", "goodbye", "see you"]):
        return "Goodbye! Have a great day!"

    return (
        "Sorry, I didn't understand that. "
        "You can ask me to apply for leave, check your leave balance, view upcoming leaves, or cancel a leave."
    )

# --- Streamlit Chat UI ---
st.title("🏖️ Leave Management Chatbot")

# Add greeting if chat is empty
if not st.session_state.chat_history:
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": "Hello! 👋 I'm your Leave Management Assistant. You can ask me to apply for leave, check your leave balance, view upcoming leaves, or cancel a leave. How can I help you today?"
    })

for entry in st.session_state.chat_history:
    if entry["role"] == "user":
        st.chat_message("user").write(entry["content"])
    else:
        st.chat_message("assistant").write(entry["content"])

user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    response = parse_command(user_input)
    st.session_state.chat_history.append({"role": "assistant", "content": response})
    st.rerun()