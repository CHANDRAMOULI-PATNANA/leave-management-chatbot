import json
import streamlit as st
from datetime import datetime
# Mock data
if "employees" not in st.session_state:
    st.session_state.employees = {
        "E001": {
            "name": "John Doe",
            "leave_balance": {"casual": 5, "sick": 2},
            "applied_leaves": [
                {
                    "from": "2025-07-05",
                    "to": "2025-07-07",
                    "type": "casual",
                    "reason": "Vacation",
                    "status": "approved",
                }
                ],
                }
                }
employees = st.session_state.employees
current_user_id = "E001"
date_format = "%Y-%m-%d"


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

    return upcoming


def apply_leave(from_date, to_date, reason, leave_type):
    balance = employees[current_user_id]["leave_balance"]
    # Prevent duplicate leave for same date and type
    for leave in employees[current_user_id]["applied_leaves"]:
        if (
            leave["from"] == from_date
            and leave["type"] == leave_type
            and leave["status"] == "approved"
        ):
            return f"You have already applied for {leave_type} leave on {from_date}."
    if balance[leave_type] <= 0:
        return f"You don't have enough {leave_type} leaves."
    # Save the leave
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

# 🎨 Streamlit UI
st.title("🏖️ Leave Management Chatbot")

action = st.selectbox(
    "What would you like to do?",
    ("Check Balance", "View Upcoming Leaves", "Apply Leave", "Cancel Leave"),
)

if action == "Check Balance":
    st.write(check_leave_balance())

elif action == "View Upcoming Leaves":
    upcoming = view_upcoming_leaves()
    if upcoming:
        st.write("Your upcoming leaves:")
        for leave in upcoming:
            st.write(f"- {leave}")
    else:
        st.info("No upcoming leaves.")

elif action == "Apply Leave":
    from_date = st.text_input("From Date (YYYY-MM-DD)")
    to_date = st.text_input("To Date (YYYY-MM-DD)")
    reason = st.text_input("Reason")
    leave_type = st.selectbox("Type of leave", ("casual", "sick"))
    if st.button("Apply"):
        if from_date and to_date and reason:
            st.success(apply_leave(from_date, to_date, reason, leave_type))
        else:
            st.warning("Please fill all the details.")

elif action == "Cancel Leave":
    cancel_date = st.text_input("Enter the From-Date to cancel (YYYY-MM-DD)")
    if st.button("Cancel"):
        if cancel_date:
            st.success(cancel_leave(cancel_date))
        else:
            st.warning("Please enter a date.")