from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base
from fastapi.middleware.cors import CORSMiddleware
import pypyodbc as odbc
import requests
import json
import os
from dotenv import load_dotenv
from fastapi import  Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates




load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
db_name = os.getenv("DB_NAME")
user = os.getenv("USER")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
port = os.getenv("PORT")




app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# Create an instance of the Jinja2Templates class
templates = Jinja2Templates(directory="templates")

# Define a route to serve the index.html file
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    # Render the index.html template and pass the request to include static files
    return templates.TemplateResponse("index.html", {"request": request})


Base = declarative_base()

class ItemCreate(BaseModel):
    user: str
    key: int

# {
#     "role": "system",
#     "content": """
# You are cancellation agent, an automated service to cancel the membership of the customer. Tell user that you are cancellation agent and ask him if he wants to cancel the membership, and then if he asks for cancellation, ask the reason for cancellation, When he gives the reason, tell him that membership is successfully cancelled. If the user ask to remove only club_amenities, just tell him that your club_amenities are removed. You good bye the customer with greetings with hoping to rejoin us soon. You respond in a short, very conversational manner.
# """,
#   },
prompt = [
  
  {
    "role": "system",
    "content": """
                You are a cancellation agent, an automated service focused on handling membership-related inquiries, especially cancellations and freezes, for logged-in members. Your interactions are polite, empathetic, and respectful. When a logged-in member inquires about cancellation, first explore the possibility of freezing their membership, using policy information from 'External_website'. If a member wishes to freeze their membership, direct them to http://freezingmembershipstatus.com. If the member still wishes to cancel, kindly ask for their reason for cancellation. After receiving their reason, you should immediately confirm that their membership has been successfully cancelled and that a confirmation email will be sent to them shortly.
                
                If the user ask to remove only club_amenities, just tell him that your club_amenities are removed. Then immediately you must ask user to give us rating on our service on a scale of 1-5, with 5 being excellent, after he gives the rating, gratitude him with this 'Thank you for your rating: {user rating} ' Then just close the conversation.

                For members moving locations, ask them to provide their new zip code. Once they enter the zipcode ask them that should we provide them the branch, location and details based on the zip code. If they agree tell them about the dummy branch and dummy location details based on zip code. Then you should immediately confirm that their membership has been successfully cancelled and that a confirmation email will be sent to them shortly.Then immediately you must ask user to give us rating on our service on a scale of 1-5, with 5 being excellent, after he gives the rating, gratitude him with this 'Thank you for your rating: {user rating} ' Then just close the conversation.
                Always begin conversation in English.
                However, when recording the cancellation reason in the system, convert it to English and update the 'cancellation_reason' column accordingly. Then immediately you must ask user to give us rating on our service on a scale of 1-5, with 5 being excellent, after he gives the rating, gratitude him with this 'Thank you for your rating: {user rating} ' Then just close the conversation.
                For requests outside your scope, guide members to email/call Customer Service or visit their local club.
                Be prepared to initiate conversations in different languages and switch to different ones based on user preference. In interactions involving different languages, respond adequately in their language.

                
""",
  },
  
  {
    "role": "user",
    "content":
      "",
  },
  {
    "role": "assistant",
    "content":
      "Hello! I am the cancellation agent. How can I assist you today?",
  },
]

count=0
end=False

def checkResult():
    
    try:

        ans=prompt.copy()
        ans.append({
            "role": "system",
            "content":
            "Create a json summary of the previous discussion. Tell whether he wants to cancel membership or not, the reason for cancellation and whether to remove club_amenities or not , only give the rating if rating is provided by the user, The fields should be 1) cancel(boolean) 2) reason 3) club_amenities(boolean) 4) rating (1-5) , cancel and club_amenities cannot be true at same time",
        })
    # {
    #     cancel:true,
    #     reason:'',
    #     club_amenities:false,
    # }
        headers = {'Authorization': f'Bearer {api_key}'}
        data ={'model': "gpt-3.5-turbo",'messages': ans}
        response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)

        if response:
            result=response.json()["choices"][0]["message"]["content"]
            result=json.loads(result)
            print(result)
            if result["cancel"]:                
                updateMembership(0,1,result)        
            
            elif result["club_amenities"] :
                updateMembership(1,1,result)
            
            if result['rating']>0:
                updateMembership(2,1,result)
                
                


    except Exception as e:
        
        print(e)


@app.post("/getResponse/")
def create_item(item: ItemCreate):
    global end
    global prompt
    global count

    ans={'response':'',
             'end':end}
    try:
        
        res=[]
        if item.key==1:
            res=prompt[:3]
            prompt=prompt[:3]
            count=0
            end=False
        else:
            res=prompt
   
        userResponse={"role":"user","content":item.user}
        res.append(userResponse)
        prompt.append(userResponse)
       
        headers = {'Authorization': f'Bearer {api_key}'}
        data ={'model': "gpt-3.5-turbo",'messages': res}
        response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)

        
        if response:
            prompt.append({"role":"assistant","content":response.json()["choices"][0]["message"]["content"]})
            checkResult()
            ans["response"]=response.json()["choices"][0]["message"]["content"]
            ans["end"]=end

        return ans
    
    except Exception as e:
        print(e)
        ans["response"]="Something Went Wrong"
        ans["end"]=False
        return ans




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



def updateMembership(key: int,membership_id:int, item: json ):
    global end
    global count
    try:
        db = connect()
        cur = db.cursor()
    
        if key==0 :
            cur.execute("UPDATE membership SET membership_status = 'Cancelled', cancellation_reason=? WHERE membership_id = ?", (item["reason"],membership_id))
            count+=1

        elif(key==2):
            cur.execute("UPDATE membership SET rating = ? WHERE membership_id = ?", (item['rating'], membership_id))
            end=True

        else:
            cur.execute("UPDATE membership SET club_amenities = 'Removed' WHERE membership_id = ?", (membership_id,))
            print("end")

        db.commit()
        db.close()
        
    except Exception as e:
        print(e)


origins = [
    "http://localhost",
    "http://localhost:3000",  # Example: Allow requests from these origins
    "https://example.com",
    "https://subdomain.example.com",
]

# Add CORS middleware to the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, etc.)
    allow_headers=["*"],  # Allow all headers
)