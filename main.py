import openai
import json
import pypyodbc as odbc  

# OpenAI API configuration
api_key = "<add your api key>"
openai.api_key = api_key

DB_NAME = "mman_21"
USER = 'sa'
PASSWORD = "Commtel@0133"
HOST = "127.0.0.1"
PORT = "1433"



def create_chatbot_prompt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=prompt,
        temperature=0
    )
    return response.choices[0]



# Function to establish a database connection
def connect():
    try:
        # Database connection parameters
        driver = 'Driver={ODBC Driver 17 for SQL Server};'
        server = f'Server={HOST},{PORT};'
        database = f'Database={DB_NAME};'
        trusted_connection = 'Trusted_Connection=yes;'

        # Create the connection string
        conn_str = odbc.connect(
            f'{driver}{server}{database}{trusted_connection}'
        )
        
        return conn_str  # Return the connection object

    except Exception as e:
        print(f"Error connecting to the database: {e}")
        



# Function to cancel a membership based on membership ID
def cancel_membership(membership_id=1):
    db = connect()
    cur = db.cursor()
    cur.execute("UPDATE membership SET membership_status = 'Cancelled' WHERE membership_id = ?", (membership_id,))
    db.commit()
    db.close()
    return "Membership Cancelled Successfully"


def cancellation_reason(reason,membership_id=1):
    db = connect()
    cur = db.cursor()
    cur.execute("UPDATE membership SET cancellation_reason =? WHERE membership_id = ?", (reason,membership_id))
    db.commit()
    db.close()
    return "Reason updated"


def remove_amenitie(membership_id=1):
    db = connect()
    cur = db.cursor()
    cur.execute("UPDATE membership SET club_amenities = 'Removed' WHERE membership_id = ?", (membership_id,))
    db.commit()
    db.close()
    return "Reason updated"


cancel=0

def createResults(message):
    global cancel
    message.append({
        "role": "system",
        "content":
        "Create a json summary of the previous discussion. Tell whether he wants to cancel membership or not, the reason for cancellation and whether to remove club_amenities or not  also tell whether the chat is completed or not, The fields should be 1) cancel(boolean) 2) reason 3) club_amenities(boolean) 4) end(boolean), cancel and club_amenities cannot be true at same time",
    })

    response = create_chatbot_prompt(message)
        # save_to_database(prompt, chatbot_response)
    result=json.loads(response.message.content)
    if(result['cancel']):
        cancel+=1
        if(cancel>=2):
            cancel_membership()
            cancellation_reason(result['reason'])
    elif(result['club_amenities']):
        remove_amenitie()
    return result['end']



def main():
    
    prompt = [
        {
            "role": "system",
            "content": "You are cancellation agent, an automated service to cancel the membership of the customer. Tell user that you are cancellation agent and ask him if he wants to cancel the membership, and then if he asks for cancellation, ask the reason for cancellation, When he gives the reason, tell him that membership is successfully cancelled. If the user ask to remove only club_amenities, tell him that your club_amenities are removed. You good bye the customer with greetings with hoping to rejoin us soon. You respond in a short, very conversational manner.",
        }
]
    
    while(True):

        
        chatbot_response = create_chatbot_prompt(prompt)
        # save_to_database(prompt, chatbot_response)
        print("Agent ",chatbot_response.message.content)
        prompt.append({"role":"assistant","content":chatbot_response.message.content})
        message = prompt.copy()
        flag=createResults(message)
        if(flag):
            break
        
        ans=input("Enter your answer ")
        prompt.append({
            "role": "user",
            'content': ans,
        })

if __name__ == "__main__":
    main()
