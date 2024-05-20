# Importing Module
from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
from youtube_transcript_api import YouTubeTranscriptApi
import requests
import httpx
import tracemalloc
import re
app = FastAPI()

# Youtube API
youtube_api_key = "AIzaSyBf7Oy_B9JBS1r_wD0gzIRLsrjJ3yBDB0M"
youtube_api_url = f"https://www.googleapis.com/youtube/v3/videos"

# Templates configuration
templates = Jinja2Templates(directory="templates")

# Translate API
Trans_url = "https://aibit-translator.p.rapidapi.com/api/v1/translator/text"
Trans_headers = {
	"content-type": "application/x-www-form-urlencoded",
	"X-RapidAPI-Key": "1657246635msh89203c19aebc795p196e25jsn09b2ad7bb98c",
	"X-RapidAPI-Host": "aibit-translator.p.rapidapi.com"
}

#summarize API
sum_url = "https://chatgpt-42.p.rapidapi.com/geminipro"
sum_headers = {
	"content-type": "application/json",
	"X-RapidAPI-Key": "1c7e5ff66cmsh100e19a34a5fde1p1a0517jsn438a2ba8a522",
	"X-RapidAPI-Host": "chatgpt-42.p.rapidapi.com"
}

@app.get("/")
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/summarize")
async def summarize(request: Request, video_url: str = Form(...),target_language: str = Form(...)):
    video_id = extract_video_id(video_url)
    video_info = await fetch_video_title(video_id)
    transcript = get_video_transcript(video_id)
    toeng = {
	"from": "auto",
	"to": "en",
	"text": transcript}
    response = requests.post(Trans_url, data=toeng, headers=Trans_headers)
    text_for_sum=response.json().get("trans", "")
    sum_payload = {
	"messages": [
		{
			"role": "user",
			"content": f"give a short summary of this text with out summary tag - {text_for_sum}"
		}
	],
	"temperature": 0.9,
	"top_k": 5,
	"top_p": 0.9,
	"max_tokens": 256,
	"web_access": False}
    response = requests.post(sum_url, json=sum_payload, headers=sum_headers)
    summarized_text=response.json().get("result", "")
    fromeng={
	"from": "en",
	"to": target_language,
	"text": summarized_text}
    final_result = requests.post(Trans_url, data=fromeng, headers=Trans_headers)
    final_summary=final_result.json().get("trans", "")
    return templates.TemplateResponse("index.html", {"request": request,"title": video_info,"summary": final_summary})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)

def extract_video_id(url):
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_video_transcript(video_id,max_attempt=3):
    attempt=0
    while attempt<max_attempt:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id,languages=['en','hi'])
            text = ' '.join([entry['text'] for entry in transcript])
            final_transcript = ''.join([i['text'] if isinstance(i, dict) and 'text' in i else str(i) for i in text])
            return final_transcript
        except Exception as e:
            attempt+=1
            print(f"Error getting transcript: {e}")
    return "Error fetching transcript"

async def fetch_video_title(video_id: str):
    params = {
        "part": "snippet",
        "id": video_id,
        "key": youtube_api_key,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(youtube_api_url, params=params)
        data = response.json()

        if "items" in data and data["items"]:
            video_title = data["items"][0]["snippet"]["title"]
            return video_title
        else:
            return None