import os
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, timedelta, timezone
from database import db, create_document, get_documents

app = FastAPI(title="IMMERZO API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models (request bodies)
class OTPStartRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15)
    purpose: str = Field(..., pattern=r"^(franchise|mall)$")

class OTPVerifyRequest(BaseModel):
    phone: str
    purpose: str
    code: str

class FranchisePayload(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    investment_capacity_lakhs: float
    preferred_cities: str
    city_tier: str
    message: Optional[str] = None
    otp_code: Optional[str] = None

class MallPayload(BaseModel):
    contact_name: str
    email: EmailStr
    phone: str
    mall_name: str
    location_city: str
    available_space_sqft: int
    message: Optional[str] = None
    otp_code: Optional[str] = None


@app.get("/")
def read_root():
    return {"message": "IMMERZO Backend Running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = os.getenv("DATABASE_NAME") or "❌ Not Set"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response


# Simple in-DB OTP storage (expires in 10 minutes)
@app.post("/api/otp/start")
def start_otp(req: OTPStartRequest):
    code = "123456"  # Stub code; replace with SMS gateway integration if needed
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    create_document("otprequest", {
        "phone": req.phone,
        "purpose": req.purpose,
        "code": code,
        "verified": False,
        "expires_at": expires_at,
    })
    # Return code for demo purposes; in production, do not return code
    return {"success": True, "message": "OTP sent", "demo_code": code}


@app.post("/api/otp/verify")
def verify_otp(req: OTPVerifyRequest):
    recs = list(db["otprequest"].find({"phone": req.phone, "purpose": req.purpose}).sort("created_at", -1).limit(1)) if db else []
    if not recs:
        raise HTTPException(status_code=400, detail="OTP not found")
    rec = recs[0]
    if rec.get("code") != req.code:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    if rec.get("expires_at") and datetime.now(timezone.utc) > rec["expires_at"]:
        raise HTTPException(status_code=400, detail="OTP expired")
    db["otprequest"].update_one({"_id": rec["_id"]}, {"$set": {"verified": True, "updated_at": datetime.now(timezone.utc)}})
    return {"success": True}


@app.get("/api/metrics")
def get_metrics():
    # Populate with real data from Bengaluru unit if available
    return {
        "operational_since": "June, 2023",
        "current_location": "Phoenix Marketcity, Bengaluru",
        "avg_daily_footfall": 1800,
        "mom_growth_percent": 18,
        "avg_tickets_per_day": 240,
        "peak_days": "Fri-Sun",
        "corporate_booking_rate_percent": 22,
        "google_rating": 4.7,
        "franchise_slots_2025": 3
    }


@app.post("/api/franchise")
def submit_franchise(payload: FranchisePayload):
    # Optionally verify OTP
    if payload.otp_code:
        try:
            verify_otp(OTPVerifyRequest(phone=payload.phone, purpose="franchise", code=payload.otp_code))
        except HTTPException as e:
            raise e
    doc_id = create_document("franchiseinquiry", payload.model_dump())
    return {"success": True, "id": doc_id}


@app.post("/api/mall")
async def submit_mall(
    contact_name: str = Form(...),
    email: EmailStr = Form(...),
    phone: str = Form(...),
    mall_name: str = Form(...),
    location_city: str = Form(...),
    available_space_sqft: int = Form(...),
    message: Optional[str] = Form(None),
    otp_code: Optional[str] = Form(None),
    floorplan: Optional[UploadFile] = File(None),
):
    if otp_code:
        try:
            verify_otp(OTPVerifyRequest(phone=phone, purpose="mall", code=otp_code))
        except HTTPException as e:
            raise e

    file_meta = None
    if floorplan is not None:
        # Save in local storage under /public/uploads
        upload_dir = os.path.join("public", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{floorplan.filename}"
        path = os.path.join(upload_dir, filename)
        with open(path, "wb") as f:
            content = await floorplan.read()
            f.write(content)
        file_meta = {"filename": filename, "path": f"/uploads/{filename}", "size": len(content)}

    data = {
        "contact_name": contact_name,
        "email": str(email),
        "phone": phone,
        "mall_name": mall_name,
        "location_city": location_city,
        "available_space_sqft": available_space_sqft,
        "message": message,
        "floorplan": file_meta,
    }
    doc_id = create_document("mallinquiry", data)
    return {"success": True, "id": doc_id, "file": file_meta}


# Simple download links and press list
@app.get("/api/resources")
def resources():
    return {
        "franchise_kit_url": "/assets/franchise-kit.pdf",
        "webinar_time": "Saturday 11:00 AM IST",
        "whatsapp_number": "+91-90XXXXXX00"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
