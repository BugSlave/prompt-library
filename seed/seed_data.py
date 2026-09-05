"""
Seed script: populates the prompts collection with sample data so the app
works immediately after setup.

Run with:
    python seed/seed_data.py

Safe to re-run: it clears existing sample prompts (matched by slug) before
re-inserting them, so it won't create duplicates on repeat runs.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from services.db import get_prompts_collection
from utils.slug import generate_slug

SAMPLE_PROMPTS = [
    {
        "title": "Build a Modern SaaS Website",
        "category": "Web Development",
        "prompt": """You are an expert front-end developer and UI/UX designer.

Build a modern, responsive landing page for a SaaS product called "FlowStack".

Requirements:
- Hero section with a clear headline, subheadline, and CTA button
- Feature grid (3-6 features) with icons
- Pricing section with 3 tiers
- Testimonials section
- Footer with links and social icons
- Fully responsive: desktop, tablet, mobile
- Clean, modern design with good typography and spacing
- Use semantic HTML and accessible markup
- Use CSS (or Tailwind if available) — no unnecessary frameworks

Output complete, working code (HTML/CSS/JS or React), ready to run.""",
    },
    {
        "title": "Create a React Dashboard",
        "category": "React",
        "prompt": """You are a senior React developer.

Build a responsive admin dashboard using React.

Requirements:
- Sidebar navigation with icons and active state
- Top navbar with search and user avatar
- Stat cards showing key metrics (e.g., revenue, users, orders)
- A line chart and a bar chart showing trends over time
- A data table with sorting and pagination
- Dark and light theme support
- Fully responsive layout (sidebar collapses to a drawer on mobile)
- Use functional components and hooks only
- Keep components small and reusable

Output complete, working React code with clear file/component separation.""",
    },
    {
        "title": "Build a Python Flask REST API",
        "category": "Backend",
        "prompt": """You are an expert backend developer specializing in Python and Flask.

Build a REST API for a simple "Task Manager" application.

Requirements:
- Endpoints: GET /tasks, GET /tasks/<id>, POST /tasks, PUT /tasks/<id>, DELETE /tasks/<id>
- Each task has: id, title, description, status (todo/in_progress/done), createdAt
- Use a clean project structure (routes, models, services)
- Validate input data properly (required fields, correct types)
- Return consistent JSON responses with proper HTTP status codes
- Handle errors gracefully (404 for missing tasks, 400 for bad input, 500 for server errors)
- Include a requirements.txt and instructions to run the app

Output complete, working, runnable code — no placeholders.""",
    },
    {
        "title": "Create an AI Chatbot",
        "category": "AI / LLM",
        "prompt": """You are an expert conversational AI engineer.

Design a customer support chatbot for an e-commerce store.

Requirements:
- The chatbot should be able to: answer FAQs, check order status, and escalate to a human when needed
- Define a clear system prompt / persona for the chatbot (friendly, concise, helpful)
- Define how the bot should handle: unclear questions, angry customers, and questions outside its scope
- Provide 5 example conversations showing the bot handling different scenarios well
- Explain what guardrails should be in place to avoid hallucinated policy answers (e.g., refund rules)
- Keep responses short, clear, and on-brand

Output the full system prompt plus the example conversations.""",
    },
    {
        "title": "Build a MongoDB CRUD Application",
        "category": "Database",
        "prompt": """You are an expert backend developer working with MongoDB.

Build a complete CRUD application for managing a "Book Library".

Requirements:
- Each book has: title, author, genre, publishedYear, isAvailable
- Use MongoDB as the database (no SQL)
- Implement Create, Read, Update, Delete operations
- Add basic input validation (no empty titles/authors, publishedYear must be a valid number)
- Add a search/filter feature (by title or genre)
- Use environment variables for the MongoDB connection string — no hardcoded credentials
- Structure the code cleanly (models, services/routes separated)
- Include example requests for each endpoint

Output complete, working code with clear setup instructions.""",
    },
]


def seed():
    collection = get_prompts_collection()
    now = datetime.now(timezone.utc)
    inserted = 0

    for item in SAMPLE_PROMPTS:
        slug = generate_slug(item["title"])
        collection.delete_one({"slug": slug})  # avoid duplicates on re-run
        doc = {
            "title": item["title"],
            "slug": slug,
            "prompt": item["prompt"],
            "category": item["category"],
            "createdAt": now,
            "updatedAt": now,
        }
        collection.insert_one(doc)
        inserted += 1
        print(f"  Seeded: {item['title']}")

    print(f"\nDone. Inserted {inserted} sample prompts.")


if __name__ == "__main__":
    print("Seeding sample prompts into MongoDB...\n")
    seed()
