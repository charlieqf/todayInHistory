import sys
import os
import json
import sqlite3
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Setup relative imports for the DB storage
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(SCRIPT_DIR, "..", "db")
sys.path.append(DB_DIR)
from storage import get_db_connection

# Load API key from .env (never hardcode keys!)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(SCRIPT_DIR, "..", "..", ".env"))
except ImportError:
    pass

# Default review prompt used when a channel doesn't define its own
DEFAULT_REVIEW_PROMPT = """
You are a ruthless senior content director reviewing a short video script.
Score this script on a scale of 1-10 based on these criteria:
1. **Hook Strength** (Scene 1): Does it immediately grab attention? Would a viewer stop scrolling?
2. **Dramatic Arc**: Does the story have rising tension and a satisfying payoff?
3. **Visual Richness**: Are the image prompts specific enough to generate compelling visuals?
4. **Pacing**: Does each scene flow naturally into the next? Is the narration too dense or too thin?
5. **Ending Impact**: Does the final scene leave the viewer thinking or wanting to share?

If the overall score is 7 or above, approve. If below 7, provide specific, actionable improvement suggestions.
"""

# ----------------- PYDANTIC SCHEMA DEFINITIONS -----------------
class Scene(BaseModel):
    durationInFrames: int = Field(description="Duration of this scene in frames. Assume 30 FPS. Standard is 120-240 frames (4-8 seconds).")
    text: str = Field(description="The narrator's script in Chinese for this scene. (e.g., '1984年，苹果用这个广告向全人类宣告...')")
    imagePrompt: str = Field(description="Highly detailed English prompt for an AI Image Generator. Must specify camera angle, lighting, subject action, and era style. E.g. 'A cinematic wide shot of a 1980s computer hacker working in a dimly lit garage, glowing CRT monitor, neon reflections, highly detailed, 8k resolution.'")
    animationUrl: str = Field(description="Optional. A Lottie animation URL. Leave as empty string if not needed.")

class VideoScript(BaseModel):
    audioUrl: str = Field(description="Leave this as an empty string. The pipeline will fill this in Node 3.")
    scenes: list[Scene] = Field(description="Exactly 8 scenes that make up the video.")

class ReviewResult(BaseModel):
    overall_score: int = Field(description="Overall quality score from 1 to 10.")
    hook_score: int = Field(description="Hook strength score from 1 to 10.")
    arc_score: int = Field(description="Dramatic arc score from 1 to 10.")
    visual_score: int = Field(description="Visual richness score from 1 to 10.")
    pacing_score: int = Field(description="Pacing score from 1 to 10.")
    ending_score: int = Field(description="Ending impact score from 1 to 10.")
    approved: bool = Field(description="True if overall_score >= 7, False otherwise.")
    improvement_suggestions: str = Field(description="Specific actionable suggestions for improvement. Empty if approved.")

# Maximum number of self-revision rounds to prevent infinite loops
MAX_REVISIONS = 2
QUALITY_THRESHOLD = 7

# -------------------------------------------------------------

def _get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found. Set it in .env or your environment.")
    return genai.Client(api_key=api_key)

def _generate_script(client, system_prompt: str, prompt: str) -> str:
    """Call Gemini to generate the structured video script JSON."""
    response = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents=[system_prompt, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VideoScript,
            temperature=0.7,
        ),
    )
    return response.text

def _review_script(client, review_prompt: str, script_json_str: str, event_title: str) -> ReviewResult:
    """Call Gemini to review the generated script quality."""
    review_input = f"Event: {event_title}\n\nScript to review:\n{script_json_str}"
    response = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents=[review_prompt, review_input],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ReviewResult,
            temperature=0.3,  # Low temperature for consistent evaluation
        ),
    )
    return ReviewResult.model_validate_json(response.text)

def _revise_script(client, system_prompt: str, original_script: str, suggestions: str, prompt: str) -> str:
    """Call Gemini to revise the script based on review feedback."""
    revision_prompt = f"""
The following video script was reviewed and needs improvement.

Original Script:
{original_script}

Review Feedback:
{suggestions}

Original Event Context:
{prompt}

Please rewrite the script addressing ALL the feedback above. Keep the same JSON structure with exactly 8 scenes.
Make the hook MORE attention-grabbing, the narrative MORE dramatic, and the image prompts MORE visually specific.
"""
    response = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents=[system_prompt, revision_prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VideoScript,
            temperature=0.8,  # Slightly higher for creative revision
        ),
    )
    return response.text

def run_script_generation(job_id: int):
    """
    Node 2: Extracts the raw material from DB, prompts Gemini, reviews the output,
    and auto-revises if the script doesn't meet quality standards.
    """
    print(f"🎬 [Node 2 - Script Gen] Starting for Job #{job_id}...")
    
    conn = get_db_connection()
    try:
        # Fetch Job & Event Details (now JOINing with channels for dynamic config)
        job = conn.execute('''
            SELECT vj.*, e.title, e.summary, e.rich_context, e.month, e.day, e.year,
                   ch.system_prompt as ch_system_prompt, ch.review_prompt as ch_review_prompt,
                   ch.display_name as ch_display_name
            FROM video_jobs vj 
            JOIN historical_events e ON vj.event_id = e.id 
            LEFT JOIN channels ch ON vj.channel_id = ch.id
            WHERE vj.id = ?
        ''', (job_id,)).fetchone()
        
        if not job:
            print(f"❌ Job {job_id} not found.")
            return False

        # Load channel-specific prompts (fall back to defaults if no channel assigned)
        system_prompt = job['ch_system_prompt'] if job['ch_system_prompt'] else 'You are a short-video scriptwriter. Create an engaging 1-minute script with exactly 8 scenes. Narration in Chinese. Detailed English image prompts.'
        review_prompt = job['ch_review_prompt'] if job['ch_review_prompt'] else DEFAULT_REVIEW_PROMPT
        channel_name = job['ch_display_name'] or 'Unknown Channel'
        print(f"📺 Channel: {channel_name}")

        # Build context from rich_context if available, else fallback to summary
        context = job['rich_context'] if job['rich_context'] else job['summary']
        date_str = ""
        if job['month'] and job['day']:
            date_str = f"Date: {job['year']}年{job['month']}月{job['day']}日\n"
        elif job['year']:
            date_str = f"Time period: {job['year']}年\n"
            
        prompt = f"Event Title: {job['title']}\n{date_str}\nContext Details:\n{context}\n\nCreate the 8-scene script based on this."

        client = _get_gemini_client()

        # === STEP 1: Generate initial script ===
        print(f"🧠 Calling Gemini for intelligent scripting...")
        script_json_str = _generate_script(client, system_prompt, prompt)
        print(f"📝 [Draft] Initial script generated ({len(script_json_str)} chars)")

        # === STEP 2: AI Self-Review Loop ===
        for revision_round in range(MAX_REVISIONS + 1):
            print(f"\n🔍 [Review Round {revision_round + 1}] Evaluating script quality...")
            review = _review_script(client, review_prompt, script_json_str, job['title'])
            
            print(f"   Hook: {review.hook_score}/10 | Arc: {review.arc_score}/10 | "
                  f"Visual: {review.visual_score}/10 | Pacing: {review.pacing_score}/10 | "
                  f"Ending: {review.ending_score}/10")
            print(f"   ⭐ Overall: {review.overall_score}/10 {'✅ APPROVED' if review.approved else '❌ NEEDS REVISION'}")
            
            if review.overall_score >= QUALITY_THRESHOLD:
                print(f"🎉 [Quality Gate] Script passed with score {review.overall_score}/10!")
                break
            
            if revision_round >= MAX_REVISIONS:
                print(f"⚠️ [Quality Gate] Max revisions reached. Using best available script (score: {review.overall_score}/10).")
                break
            
            # Auto-revise
            print(f"✏️ [Revision] Auto-improving based on feedback: {review.improvement_suggestions[:100]}...")
            script_json_str = _revise_script(client, system_prompt, script_json_str, review.improvement_suggestions, prompt)
            print(f"📝 [Revision] Revised script generated ({len(script_json_str)} chars)")

        # Save the result back into the video_jobs table
        conn.execute('''
            UPDATE video_jobs 
            SET script_json = ?, status = 'SCRIPT_GEN', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (script_json_str, job_id))
        conn.commit()
        
        print(f"✅ [Node 2 - Script Gen] Successfully wrote reviewed JSON Script to DB.")
        return True

    except Exception as e:
        print(f"❌ [Node 2 - Script Gen] Error generating script: {e}")
        conn.execute("UPDATE video_jobs SET error_log = ?, status = 'ERROR' WHERE id = ?", (str(e), job_id))
        conn.commit()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        job_id = int(sys.argv[1])
        run_script_generation(job_id)
    else:
        print("Usage: python node_script_gen.py <job_id>")
