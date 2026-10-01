# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import uuid
from zoneinfo import ZoneInfo
from google import genai
from google.cloud import firestore
from google.cloud import storage

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors.agent_engine_sandbox_code_executor import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from .a2ui_utils import a2ui_callback


MODEL = "gemini-3.6-flash"
PROJECT_ID = "qwiklabs-gcp-03-c2062bba7c2d"
BUCKET_NAME = "fittrack-assets-qwiklabs-gcp-03-c2062bba7c2d"
SANDBOX_RESOURCE_NAME = "projects/424771485303/locations/us-east1/reasoningEngines/4346393653854339072/sandboxEnvironments/7610458847651561472"
MEMORY_BANK_ID = "4346393653854339072"


async def generate_memories_callback(callback_context: CallbackContext):
    """After each turn, send the session to Vertex AI Memory Bank for extraction."""
    try:
        await callback_context.add_session_to_memory()
    except ValueError as e:
        if "memory service is not available" in str(e):
            invocation_context = getattr(callback_context, "_invocation_context", None)
            session = getattr(invocation_context, "session", None)
            if session and memory_service is not None:
                try:
                    await memory_service.add_session_to_memory(session)
                except Exception:
                    pass
        else:
            raise
    return None


def memory_bank_service_builder() -> VertexAiMemoryBankService:
    """Builds a VertexAiMemoryBankService instance for Agent Runtime deployment."""
    return VertexAiMemoryBankService(
        project=PROJECT_ID,
        location="us-east1",
        agent_engine_id=MEMORY_BANK_ID,
    )


_firestore_client = None


def get_db() -> firestore.Client:
    """Returns a Firestore client instance for the hardcoded project ID."""
    global _firestore_client
    if _firestore_client is None:
        _firestore_client = firestore.Client(project=PROJECT_ID)
    return _firestore_client


def get_workout_routines(target_muscle: str = "") -> list[dict]:
    """Retrieves workout routines from the Firestore database.

    Args:
        target_muscle: Optional filter for target muscle group (e.g. 'full_body', 'upper_body', 'legs', 'core'). If empty, returns all routines.

    Returns:
        A list of workout routine summaries.
    """
    db = get_db()
    collection = db.collection("gym_routines")
    query = collection
    if target_muscle:
        query = query.where(field_path="target_muscle", op_string="==", value=target_muscle.lower().strip())
    docs = query.stream()
    routines = []
    for doc in docs:
        data = doc.to_dict()
        routines.append({
            "routine_id": data.get("routine_id", doc.id),
            "name": data.get("name", ""),
            "target_muscle": data.get("target_muscle", ""),
            "difficulty": data.get("difficulty", ""),
            "duration_minutes": data.get("duration_minutes", 0),
            "calories_burned_est": data.get("calories_burned_est", 0),
            "description": data.get("description", ""),
        })
    return routines


def get_workout_routine_details(routine_id: str) -> dict:
    """Retrieves full details of a specific workout routine including exercise breakdown.

    Args:
        routine_id: The ID of the workout routine (e.g. 'fat-burn-hiit', 'upper-body-blast', 'lower-body-sculpt', 'core-cardio-burn').

    Returns:
        The routine details dictionary including the list of exercises, sets, reps, and rest periods.
    """
    db = get_db()
    doc_ref = db.collection("gym_routines").document(routine_id)
    doc = doc_ref.get()
    if not doc.exists:
        return {"error": f"Routine with ID '{routine_id}' not found."}
    return doc.to_dict()


def log_completed_workout(routine_name: str, duration_minutes: int, calories_burned: int = 0, notes: str = "") -> str:
    """Logs a completed gym workout session to the user's workout log in Firestore.

    Args:
        routine_name: Name of the workout or routine completed.
        duration_minutes: Total minutes spent working out.
        calories_burned: Estimated total calories burned during the workout.
        notes: Optional notes or observations about how the workout felt.

    Returns:
        A confirmation message with the generated log ID.
    """
    db = get_db()
    log_id = str(uuid.uuid4())[:8]
    now = datetime.datetime.now(ZoneInfo("UTC"))
    log_entry = {
        "log_id": log_id,
        "routine_name": routine_name,
        "duration_minutes": duration_minutes,
        "calories_burned": calories_burned,
        "notes": notes,
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
    }
    db.collection("workout_logs").document(log_id).set(log_entry)
    return f"Successfully logged workout '{routine_name}' ({duration_minutes} mins, {calories_burned} kcal) with log ID {log_id}."


def get_recent_workout_history(limit: int = 5) -> list[dict]:
    """Retrieves recent completed workout logs from Firestore.

    Args:
        limit: Maximum number of recent logs to return (default 5).

    Returns:
        A list of recent workout log entries.
    """
    db = get_db()
    logs_ref = db.collection("workout_logs").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
    docs = logs_ref.stream()
    logs = [doc.to_dict() for doc in docs]
    return logs


def log_weight_entry(weight_kg: float, notes: str = "") -> str:
    """Logs a daily body weight entry to track weight loss progress in Firestore.

    Args:
        weight_kg: The recorded weight in kilograms.
        notes: Optional notes (e.g. 'weighed in morning before breakfast').

    Returns:
        A confirmation message of the logged weight.
    """
    db = get_db()
    log_id = str(uuid.uuid4())[:8]
    now = datetime.datetime.now(ZoneInfo("UTC"))
    entry = {
        "log_id": log_id,
        "weight_kg": weight_kg,
        "notes": notes,
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
    }
    db.collection("weight_logs").document(log_id).set(entry)
    return f"Successfully recorded weight of {weight_kg} kg with log ID {log_id}."


def calculate_caloric_deficit_and_targets(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    activity_level: str = "moderate",
    target_weekly_loss_kg: float = 0.5,
) -> dict:
    """Calculates BMR, TDEE, daily calorie deficit targets, and macro split for weight loss.

    Args:
        weight_kg: Body weight in kilograms.
        height_cm: Height in centimeters.
        age: Age in years.
        gender: 'male' or 'female'.
        activity_level: 'sedentary', 'light', 'moderate', or 'active'.
        target_weekly_loss_kg: Target weight loss in kg/week (default 0.5 kg).

    Returns:
        A dictionary with BMR, TDEE, daily calorie target, daily deficit, and protein/carb/fat macro grams.
    """
    if gender.lower().startswith("m"):
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

    multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
    }
    tdee = bmr * multipliers.get(activity_level.lower(), 1.55)
    daily_deficit = round((target_weekly_loss_kg * 7700) / 7)
    target_calories = max(round(tdee - daily_deficit), 1200)

    protein_grams = round(2.0 * weight_kg)
    fat_grams = round((target_calories * 0.25) / 9)
    carb_calories = target_calories - (protein_grams * 4) - (fat_grams * 9)
    carb_grams = max(round(carb_calories / 4), 50)

    return {
        "bmr_kcal": round(bmr),
        "tdee_kcal": round(tdee),
        "daily_calorie_target": target_calories,
        "daily_deficit_kcal": daily_deficit,
        "macros_grams": {
            "protein": protein_grams,
            "fats": fat_grams,
            "carbs": carb_grams,
        },
    }


def search_healthy_meals(query: str, max_results: int = 3) -> list[dict]:
    """Searches for healthy recipes and meals from TheMealDB public API.

    Args:
        query: Ingredient or meal name to search for (e.g. 'chicken', 'salmon', 'egg', 'salad').
        max_results: Maximum number of meal results to return (default 3).

    Returns:
        A list of meal summaries including meal name, category, cuisine origin, key ingredients, instructions snippet, and image URL.
    """
    import json
    import os
    import urllib.parse
    import urllib.request

    api_key = os.environ.get("THEMEALDB_API_KEY", "1")
    encoded_query = urllib.parse.quote(query.strip())
    url = f"https://www.themealdb.com/api/json/v1/{api_key}/search.php?s={encoded_query}"

    req = urllib.request.Request(url, headers={"User-Agent": "FitTrackAI/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            meals = data.get("meals") or []
            results = []
            for m in meals[:max_results]:
                ingredients = []
                for i in range(1, 21):
                    ing = m.get(f"strIngredient{i}")
                    meas = m.get(f"strMeasure{i}")
                    if ing and ing.strip():
                        ingredients.append(f"{meas.strip()} {ing.strip()}" if meas and meas.strip() else ing.strip())
                instructions = (m.get("strInstructions") or "").replace("\r\n", " ")
                if len(instructions) > 200:
                    instructions = instructions[:200] + "..."
                results.append({
                    "meal_id": m.get("idMeal"),
                    "name": m.get("strMeal"),
                    "category": m.get("strCategory"),
                    "cuisine": m.get("strArea"),
                    "ingredients": ingredients[:6],
                    "instructions_summary": instructions,
                    "image_url": m.get("strMealThumb"),
                })
            return results
    except Exception as e:
        return [{"error": f"Failed to fetch meal data: {e}"}]


async def generate_fitness_image(prompt: str, tool_context: ToolContext) -> dict:
    """Generates an image for a fitness item, workout milestone, or healthy meal using gemini-3.1-flash-lite-image.

    Args:
        prompt: Description of the fitness visual, healthy meal plating, or workout progress image to generate.

    Returns:
        A dictionary with the public Cloud Storage image URL and artifact details.
    """
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global",
    )

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=[types.Modality.IMAGE],
        ),
    )

    image_part = None
    image_bytes = None
    mime_type = "image/jpeg"

    for candidate in response.candidates:
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if part.inline_data and part.inline_data.data:
                    image_part = part
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/jpeg"
                    break
        if image_bytes:
            break

    if not image_bytes or not image_part:
        return {"error": "No image data was generated by the model."}

    ext = "png" if "png" in mime_type.lower() else "jpg"
    filename = f"fitness_{uuid.uuid4().hex[:8]}.{ext}"

    # 1. Save artifact for the Playground Artifacts panel
    if tool_context is not None:
        try:
            await tool_context.save_artifact(filename=filename, artifact=image_part)
        except Exception:
            pass

    # 2. Upload same bytes directly to public Cloud Storage bucket in memory
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

    return {
        "status": "success",
        "public_url": public_url,
        "artifact_filename": filename,
    }


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are FitTrack AI, a smart fitness, gym workout, and weight-loss coach assistant. "
        "You help users reach their target weight and fitness goals by calculating personalized caloric deficits, "
        "recommending healthy meals via TheMealDB API, generating motivational or meal images, "
        "finding suitable gym routines, inspecting exercises in Firestore, "
        "logging completed workouts, tracking weight progress, and running Python code in the sandbox when computations, simulations, or data analysis are needed. "
        "ALLERGIES & DIETARY RESTRICTIONS MEMORY: It is critical to track and remember ALL user allergies, food intolerances, sensitivities, "
        "and dietary restrictions (such as peanuts, tree nuts, shellfish, dairy, lactose, gluten, eggs, soy, vegan, vegetarian, etc.) across sessions. "
        "Whenever a user mentions any allergy or food intolerance, immediately acknowledge and store it in memory. "
        "Always cross-reference remembered allergies before recommending recipes or meal plans, and never recommend meals containing any allergens the user is allergic to. "
        "You remember the user's stated allergies, dietary restrictions, fitness goals, preferences, and facts from previous conversations and use them to personalize your responses. "
        "Always use your tools to perform calculations, look up meals, generate images, execute Python code in the sandbox, and interact with Firestore."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        client_kwargs={"location": "global"},
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=AgentEngineSandboxCodeExecutor(
        sandbox_resource_name=SANDBOX_RESOURCE_NAME,
    ),
    tools=[
        PreloadMemoryTool(),
        calculate_caloric_deficit_and_targets,
        search_healthy_meals,
        generate_fitness_image,
        get_workout_routines,
        get_workout_routine_details,
        log_completed_workout,
        get_recent_workout_history,
        log_weight_entry,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)

memory_service = memory_bank_service_builder()
