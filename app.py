# from flask import Flask, jsonify, render_template
# import pandas as pd
# import pickle
# import os

# app = Flask(__name__)

# # Path to your pickle file
# MODEL_PATH = "google_sentiment_data.pkl"

# def load_data():
#     if os.path.exists(MODEL_PATH):
#         with open(MODEL_PATH, "rb") as f:
#             return pickle.load(f)
#     else:
#         return pd.DataFrame()

# @app.route('/')
# def home():
#     return render_template("show_dashboard.html")  # serve your HTML page

# @app.route('/dashboard')
# def dashboard():
#     df = load_data()
#     if df.empty:
#         return jsonify({"error": "No data found"}), 404

#     data = df[['date', 'text', 'sentiment', 'sentiment_category', 'engagement']].to_dict(orient='records')
#     return jsonify(data)

# if __name__ == '__main__':
#     app.run(debug=True)


from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import pickle
import os
import shutil

app = FastAPI()

UPLOAD_PATH = "uploaded_data.pkl"

def load_data():
    if os.path.exists(UPLOAD_PATH):
        with open(UPLOAD_PATH, "rb") as f:
            return pickle.load(f)
    return pd.DataFrame()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".pkl"):
        raise HTTPException(status_code=400, detail="Only .pkl files are allowed")
    with open(UPLOAD_PATH, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": "File uploaded successfully"}

@app.get("/dashboard")
def get_dashboard_data():
    df = load_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="No data found")

    df['date'] = df['date'].astype(str)
    data = df[['date', 'text', 'sentiment', 'sentiment_category', 'engagement']].to_dict(orient="records")
    return JSONResponse(content=data)

