import openai
import json
import pypyodbc as odbc
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
api_key = os.getenv("OPENAI_API_KEY")
db_name = os.getenv("DB_NAME")
user = os.getenv("USER")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
port = os.getenv("PORT")

# OpenAI API configuration
openai.api_key = api_key

# Function to establish a database connection using a trusted connection
def connect():
    try:
        # Database connection parameters
        driver = 'Driver={ODBC Driver 17 for SQL Server};'
        server = f'Server={host},{port};'
        database = f'Database={db_name};'
        trusted_connection = 'Trusted_Connection=yes;'

        # Create the connection string
        conn_str = odbc.connect(
            f'{driver}{server}{database}{trusted_connection}'
        )

        return conn_str  # Return the connection object

    except Exception as e:
        print(f"Error connecting to the database: {e}")

def create_chatbot_prompt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=prompt,
        temperature=0
    )
    return response.choices[0]

# Function to cancel a membership based on membership ID
def cancel_membership(membership_id=1005):
    db = connect()
    cur = db.cursor()
    cur.execute("UPDATE membership SET membership_status = 'Cancelled' WHERE membership_id = ?", (membership_id,))
    db.commit()
    db.close()
    return "Membership Cancelled Successfully"

def cancellation_reason(reason, membership_id=1005):
    db = connect()
    cur = db.cursor()
    cur.execute("UPDATE membership SET cancellation_reason =? WHERE membership_id = ?", (reason, membership_id))
    db.commit()
    db.close()
    return "Reason updated"

def remove_amenitie(membership_id=1005):
    db = connect()
    cur = db.cursor()
    cur.execute("UPDATE membership SET club_amenities = 'Removed' WHERE membership_id = ?", (membership_id,))
    db.commit()
    db.close()
    return "Reason updated"

cancel = 0

def createResults(message):
    global cancel
    message.append({
        "role": "system",
        "content":
        "Create a json summary of the previous discussion. Tell whether the user wants to cancel membership or not, the reason for cancellation and whether to remove club_amenities or not also tell whether the chat is completed or not, The fields should be 1) cancel(boolean) 2) reason 3) club_amenities(boolean) 4) end(boolean), cancel and club_amenities cannot be true at the same time",
    })

    response = create_chatbot_prompt(message)
    result = json.loads(response.message.content)
    if (result['cancel']):
        cancel += 1
        if (cancel >= 2):
            cancel_membership()
            cancellation_reason(result['reason'])
    elif (result['club_amenities']):
        remove_amenitie()
    return result['end']

# Function to update the user's rating in the database
def update_rating(rating, membership_id=1005):
    db = connect()
    cur = db.cursor()
    cur.execute("UPDATE membership SET rating = ? WHERE membership_id = ?", (rating, membership_id))
    db.commit()
    db.close()
    return "Rating updated successfully"

def main():
    prompt = [
        # Initial setup message for the chatbot
        {
            "role": "system",
            "content": """\
                You are a cancellation agent, an automated service focused on handling membership-related inquiries, especially cancellations and freezes, for logged-in members. Your interactions are polite, empathetic, and respectful. When a logged-in member inquires about cancellation, first explore the possibility of freezing their membership, using policy information from 'External_website'. If the member still wishes to cancel, kindly ask for their reason for cancellation. After receiving their reason, you should immediately confirm that their membership has been successfully cancelled and that a confirmation email will be sent to them shortly.
                Begin conversation in English. If a member wishes to freeze their membership, direct them to http://freezingmembershipstatus.com.
                For members moving locations, offer to update their home club membership to a new location. Once the member provides their new zip code, update the club details in the 'membership_table.'
                For requests outside your scope, guide members to email/call Customer Service or visit their local club.
                Be prepared to initiate conversations in different languages and switch to different ones based on user preference. In interactions involving different languages, respond adequately in their language. However, when recording the cancellation reason in the system, convert it to English and update the 'cancellation_reason' column accordingly.
                """
        },

        # Initial greeting from the assistant
        {
            "role": "assistant",
            "content": "Hello! I am the cancellation agent. How can I assist you today?"
        }
    ]

    # Main loop to handle chat
    while True:
        chatbot_response = create_chatbot_prompt(prompt)
        print("Agent:", chatbot_response.message.content)
        prompt.append({"role": "assistant", "content": chatbot_response.message.content})

        message = prompt.copy()
        flag = createResults(message)

        if flag:
            # Ask for a rating after the conversation ends
            user_rating = input("Before we conclude, could you please rate our service on a scale of 1-5, with 5 being excellent? ")
            update_rating(user_rating)  # Update the rating in the database
            print("Thank you for your rating:", user_rating)
            # Process the rating as needed
            break  # End the conversation after getting the rating

        # Get user input for the next round if the conversation has not ended
        user_input = input("Enter your answer: ")
        prompt.append({"role": "user", "content": user_input})

if __name__ == "__main__":
    main()
