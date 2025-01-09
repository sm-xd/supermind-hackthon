import requests
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request

# from astrapy import DataAPIClient
# from collections import defaultdict
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

# import pandas as pd
import json
from statistics import mean
from pydantic import BaseModel


load_dotenv()

BASE_API_URL = "https://api.langflow.astra.datastax.com"
LANGFLOW_ID = "b9ad0c0e-c8f6-4eb4-b7fc-30a1440aa858"
FLOW_ID = "50f02306-32c7-46f4-aa51-10af913d0a7b"
APPLICATION_TOKEN = os.environ.get("APP_TOKEN")
token = os.environ.get("APP_TOKEN")
api_endpoint = os.environ.get("API_ENDPOINT")
ENDPOINT = "socialchat"  # You can set a specific endpoint name in the flow settings


def run_flow(
    message: str,
    output_type: str = "chat",
    input_type: str = "chat",
) -> dict:
    api_url = f"{BASE_API_URL}/lf/{LANGFLOW_ID}/api/v1/run/{ENDPOINT}"

    payload = {
        "input_value": message,
        "output_type": output_type,
        "input_type": input_type,
    }
    headers = None
    headers = {
        "Authorization": "Bearer " + APPLICATION_TOKEN,
        "Content-Type": "application/json",
    }
    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()


# Create a FastAPI application
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Origins allowed
    allow_credentials=True,  # Allow credentials like cookies
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


class PostStats(BaseModel):
    post_type: str
    count: int
    avg_likes: float
    avg_comments: float
    avg_shares: float
    avg_views: float


cloud_config = {"secure_connect_bundle": "secure-connect-social-data.zip"}

with open("social_data-token.json") as f:
    secrets = json.load(f)

CLIENT_ID = secrets["clientId"]
CLIENT_SECRET = secrets["secret"]

auth_provider = PlainTextAuthProvider(CLIENT_ID, CLIENT_SECRET)
cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
session = cluster.connect()

session.set_keyspace("test")
# df = pd.read_csv("mock_social_media_data.csv")

# insert_query = """
# INSERT INTO test.social_media_data ("Post_ID", "Comments", "Likes", "Post_Type", "Shares", "Views")
# VALUES (%s, %s, %s, %s, %s, %s);
# """


# # insert_query = "INSERT INTO social_media_data (post_id,post_type,views,likes,shares,comments) VALUES (%s, %s, %s, %s, %s, %s);"
# for _, row in df.iterrows():
#     session.execute(insert_query, tuple(row))


query = """
SELECT "Post_Type", "Likes", "Comments", "Shares", "Views"
FROM test.social_media_data
"""
rows = session.execute(query)

# Group data by post type
post_types = {}
for row in rows:
    post_type = row.Post_Type
    if post_type not in post_types:
        post_types[post_type] = {
            "likes": [],
            "comments": [],
            "shares": [],
            "views": [],
            "count": 0,
        }

    # Add data to the appropriate post type
    post_types[post_type]["likes"].append(row.Likes)
    post_types[post_type]["comments"].append(row.Comments)
    post_types[post_type]["shares"].append(row.Shares)
    post_types[post_type]["views"].append(row.Views)
    post_types[post_type]["count"] += 1

# Prepare the result
result = []
for post_type, stats in post_types.items():
    avg_likes = mean(stats["likes"]) if stats["likes"] else 0
    avg_comments = mean(stats["comments"]) if stats["comments"] else 0
    avg_shares = mean(stats["shares"]) if stats["shares"] else 0
    avg_views = mean(stats["views"]) if stats["views"] else 0

    result.append(
        PostStats(
            post_type=post_type,
            count=stats["count"],
            avg_likes=f"{avg_likes:.2f}",
            avg_comments=f"{avg_comments:.2f}",
            avg_shares=f"{avg_shares:.2f}",
            avg_views=f"{avg_views:.2f}",
        )
    )


# Define a route at the root web address ("/")
@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}


@app.post("/chatbot")
async def chatbot(request: Request):
    try:
        # Parse the JSON request body
        data = await request.json()
        user_message = data.get("message")

        if not user_message:
            raise HTTPException(status_code=400, detail="No message provided")

        # Call Langflow API to get a response
        response = run_flow(message=user_message)
        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])

        # Extract the chatbot reply from the Langflow response
        message_data = (
            response.get("outputs", [])[0]
            .get("outputs", [])[0]
            .get("results", {})
            .get("message", {})
            .get("text", "Sorry, I did not understand that.")
        )
        # print(message_data)
        # Send the chatbot response back to the frontend
        return {"reply": message_data}

    except Exception as e:
        print("Error processing chatbot request:", e)
        raise HTTPException(status_code=400, detail="Invalid request")


@app.get("/average")
def get_average():
    data = {
        "carousel": result[0],
        "reels": result[1],
        "static_post": result[2],
    }
    return data


@app.head("/health")
async def health_check():
    # Returning headers with a successful response
    return JSONResponse(content="working", status_code=200)


# res = run_flow("what insights do you have about reels?")
# print(res)


# def main():
#     parser = argparse.ArgumentParser(description="""Run a flow with a given message and optional tweaks.
# Run it like: python <your file>.py "your message here" --endpoint "your_endpoint" --tweaks '{"key": "value"}'""",
#         formatter_class=RawTextHelpFormatter)
#     parser.add_argument("message", type=str, help="The message to send to the flow")
#     parser.add_argument("--endpoint", type=str, default=ENDPOINT or FLOW_ID, help="The ID or the endpoint name of the flow")
#     parser.add_argument("--tweaks", type=str, help="JSON string representing the tweaks to customize the flow", default=json.dumps(TWEAKS))
#     parser.add_argument("--application_token", type=str, default=APPLICATION_TOKEN, help="Application Token for authentication")
#     parser.add_argument("--output_type", type=str, default="chat", help="The output type")
#     parser.add_argument("--input_type", type=str, default="chat", help="The input type")
#     parser.add_argument("--upload_file", type=str, help="Path to the file to upload", default=None)
#     parser.add_argument("--components", type=str, help="Components to upload the file to", default=None)

#     args = parser.parse_args()
#     try:
#       tweaks = json.loads(args.tweaks)
#     except json.JSONDecodeError:
#       raise ValueError("Invalid tweaks JSON string")

#     if args.upload_file:
#         if not upload_file:
#             raise ImportError("Langflow is not installed. Please install it to use the upload_file function.")
#         elif not args.components:
#             raise ValueError("You need to provide the components to upload the file to.")
#         tweaks = upload_file(file_path=args.upload_file, host=BASE_API_URL, flow_id=ENDPOINT, components=args.components, tweaks=tweaks)

#     response = run_flow(
#         message=args.message,
#         endpoint=args.endpoint,
#         output_type=args.output_type,
#         input_type=args.input_type,
#         tweaks=tweaks,
#         application_token=args.application_token
#     )

#     print(json.dumps(response, indent=2))

# if __name__ == "__main__":
#     main()
