from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# ── APP ──
app = FastAPI(
    title="Deepthi Moulya Portfolio API",
    description="Backend API for portfolio reviews, blogs and contact",
    version="2.0.0"
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Replace "*" with your Netlify URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── MONGODB CONNECTION ──
MONGO_URL = os.getenv("MONGO_URL", "your_mongodb_atlas_url_here")
client = AsyncIOMotorClient(MONGO_URL)
db           = client.portfolio_db
reviews_col  = db.reviews
blogs_col    = db.blogs
contacts_col = db.contacts


# ───────────────────────────────────────────
#  HELPERS
# ───────────────────────────────────────────
def fix_id(doc) -> dict:
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc


# ───────────────────────────────────────────
#  SCHEMAS
# ───────────────────────────────────────────
class ReviewIn(BaseModel):
    name:   str          = Field(..., min_length=1, max_length=80)
    role:   Optional[str]= Field(default="Visitor", max_length=100)
    text:   str          = Field(..., min_length=5, max_length=1000)
    rating: int          = Field(..., ge=1, le=5)

class ReviewOut(ReviewIn):
    id:         str
    created_at: datetime

class BlogIn(BaseModel):
    title:   str          = Field(..., min_length=1, max_length=150)
    excerpt: str          = Field(..., min_length=1, max_length=1000)
    date:    Optional[str]= Field(default="", max_length=50)

class BlogOut(BlogIn):
    id:         str
    created_at: datetime

class ContactIn(BaseModel):
    name:    str = Field(..., min_length=1, max_length=80)
    email:   str = Field(..., max_length=120)
    message: str = Field(..., min_length=5, max_length=2000)

class ContactOut(ContactIn):
    id:         str
    created_at: datetime


# ───────────────────────────────────────────
#  ROOT
# ───────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "message": "✦ Deepthi Moulya Portfolio API is live 🤍",
        "docs": "/docs"
    }


# ───────────────────────────────────────────
#  REVIEWS
# ───────────────────────────────────────────
@app.get("/reviews", response_model=list[ReviewOut])
async def get_reviews():
    """Fetch all reviews, newest first."""
    cursor = reviews_col.find().sort("created_at", -1)
    reviews = []
    async for doc in cursor:
        reviews.append(fix_id(doc))
    return reviews


@app.post("/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def add_review(review: ReviewIn):
    """Anyone can submit a review."""
    doc = review.dict()
    doc["created_at"] = datetime.utcnow()
    result = await reviews_col.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    doc.pop("_id", None)
    return doc


@app.delete("/reviews/{review_id}")
async def delete_review(review_id: str):
    """Delete a review by ID (admin only)."""
    result = await reviews_col.delete_one({"_id": ObjectId(review_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"message": "Review deleted 🤍"}


# ───────────────────────────────────────────
#  BLOGS
# ───────────────────────────────────────────
@app.get("/blogs", response_model=list[BlogOut])
async def get_blogs():
    """Fetch all blog posts, newest first."""
    cursor = blogs_col.find().sort("created_at", -1)
    blogs = []
    async for doc in cursor:
        blogs.append(fix_id(doc))
    return blogs


@app.post("/blogs", response_model=BlogOut, status_code=status.HTTP_201_CREATED)
async def add_blog(blog: BlogIn):
    """Publish a new blog post (admin only)."""
    doc = blog.dict()
    doc["created_at"] = datetime.utcnow()
    result = await blogs_col.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    doc.pop("_id", None)
    return doc


@app.delete("/blogs/{blog_id}")
async def delete_blog(blog_id: str):
    """Delete a blog post by ID (admin only)."""
    result = await blogs_col.delete_one({"_id": ObjectId(blog_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return {"message": "Blog post deleted 🤍"}


# ───────────────────────────────────────────
#  CONTACT
# ───────────────────────────────────────────
@app.post("/contact", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
async def send_contact(contact: ContactIn):
    """Save a contact message."""
    doc = contact.dict()
    doc["created_at"] = datetime.utcnow()
    result = await contacts_col.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    doc.pop("_id", None)
    return doc


@app.get("/contact", response_model=list[ContactOut])
async def get_contacts():
    """Get all contact messages (admin only)."""
    cursor = contacts_col.find().sort("created_at", -1)
    contacts = []
    async for doc in cursor:
        contacts.append(fix_id(doc))
    return contacts