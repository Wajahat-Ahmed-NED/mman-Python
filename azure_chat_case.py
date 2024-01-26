import os
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Retrieve API base and API key from environment variables
openai.api_type = "azure"
openai.api_version = "2023-07-01-preview"
openai.api_base = 'https://testopenaisasindu.openai.azure.com'
openai.api_key = 'ea755aab6b114b849d9c461e52897571'

# Initialize the conversation with the system message
system_message = {
    "role": "system",
    "content": (
        "You are a cancellation agent, an automated service focused on handling membership-related inquiries, "
        "especially cancellations and freezes, for logged-in members. Your interactions are polite, empathetic, "
        "and respectful. When a logged-in member inquires about cancellation, first explore the possibility of "
        "freezing their membership, using policy information from 'External_website'. If the member still wishes "
        "to cancel, kindly ask for their reason for cancellation. After receiving their reason, you should immediately "
        "confirm that their membership has been successfully cancelled and that a confirmation email will be sent to them shortly."
        "Begin conversation in English. If a member wishes to freeze their membership, direct them to http://freezingmembershipstatus.com."
        "For members moving locations, offer to update their home club membership to a new location. Once the member provides their "
        "new zip code, update the club details in the 'membership_table.' For requests outside your scope, guide members to email/call "
        "Customer Service or visit their local club. Be prepared to initiate conversations in different languages and switch to different "
        "ones based on user preference. In interactions involving different languages, respond adequately in their language. However, when "
        "recording the cancellation reason in the system, convert it to English and update the 'cancellation_reason' column accordingly."
        "Before we conclude, could you please rate our service on a scale of 1-5, with 5 being excellent? "
    )
}

# Start the conversation with the system message
messages = [system_message]

# Interactive loop
while True:
    # User input
    user_input = input("User: ")
    
    # Check for exit condition
    if user_input.lower() in ['exit', 'quit', 'stop']:
        print("Conversation ended.")
        break

    # Add user message to the conversation
    messages.append({
        "role": "user",
        "content": user_input
    })

    # Generate a response
    completion = openai.ChatCompletion.create(
        engine="test35turbo-01",
        messages=messages,
        temperature=0,
        max_tokens=1000,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )


    # Extract and print the response
    agent_response = completion.choices[0].message["content"]
    print("Agent:", agent_response)

    # Add agent response to the conversation
    messages.append({
        "role": "assistant",
        "content": agent_response
    })
