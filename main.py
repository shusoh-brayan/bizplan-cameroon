from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import uvicorn
import os

app = FastAPI()

# Allow your frontend to talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# This defines what data the frontend sends us
class BusinessInput(BaseModel):
    name: str
    sector: str
    region: str
    description: str
    target_market: str
    capital: int
    language: str
    notes: str = ""

def build_system_prompt():
    return """
You are an expert African business consultant and financial advisor specializing in Cameroon's economy.
You generate complete, professional, investor-ready business plans specifically tailored for the Cameroonian market.

CRITICAL CONTEXT YOU MUST ALWAYS APPLY:
- Currency: Central African CFA Franc (XAF). Always use XAF for all financial figures. Never use USD or EUR as primary currency.
- Cameroon is a bilingual country (French and English). Consider both markets.
- Key economic sectors: agriculture (cacao, coffee, palm oil), mobile services, transport, trade, education.
- Payment infrastructure: MTN Mobile Money, Orange Money are dominant. Bank cards are secondary.
- Key local banks for SME loans: Afriland First Bank, UBA Cameroon, SCB Cameroon, BICEC.
- Local funding & grants: MINPMEESA, FOGAPE, GICAM, Youth Employment programs, World Bank IFC Africa programs.
- Regulations: Register with CFCE, OHADA business law applies.
- Startup costs in Cameroon are significantly lower than Western markets. Be realistic.
- Market realities: power outages (factor in generator costs), mobile-first users, strong oral/referral culture.

OUTPUT FORMAT:
Always respond with a complete business plan in clean, structured markdown with these exact sections:
1. Executive Summary
2. Problem Statement
3. Proposed Solution
4. Market Analysis
5. Target Market & Customer Segments
6. Products / Services & Pricing (in XAF)
7. Marketing & Sales Strategy
8. Operational Plan
9. Management Team Structure
10. Financial Projections (Year 1, Year 2, Year 3 in XAF)
11. Startup Cost Breakdown (in XAF)
12. Funding Requirements & Sources
13. Risk Analysis & Mitigation
14. Conclusion & Vision

Be specific, realistic, and grounded in Cameroonian market conditions.
"""

def build_user_prompt(data: BusinessInput):
    return f"""
Generate a complete professional business plan with the following details:

Business Name: {data.name}
Business Sector: {data.sector}
City/Region: {data.region}
Business Description: {data.description}
Target Customers: {data.target_market}
Estimated Startup Capital: {data.capital:,} XAF
Preferred Language: {data.language}
Additional Notes: {data.notes or "None"}

Generate the full business plan now. Be specific to Cameroon's market, use XAF for all figures, and make it investor-ready.
"""

@app.get("/")
def root():
    return {"status": "BizPlan Cameroon API is running ✅"}

@app.post("/generate-plan")
async def generate_plan(data: BusinessInput):
    ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
    API_KEY = os.getenv("ANTHROPIC_API_KEY") # Replace with your actual Claude API key

    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01"
    }

    payload = {
        "model": "claude-sonnet-4-5",
        "max_tokens": 4000,
        "system": build_system_prompt(),
        "messages": [
            {"role": "user", "content": build_user_prompt(data)}
        ]
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(ANTHROPIC_API_URL, json=payload, headers=headers)
        result = response.json()

    if "error" in result:
        return {"error": result["error"]["message"]}

    plan_text = result["content"][0]["text"]
    return {"plan": plan_text}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
  
