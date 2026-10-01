# 🏋️ FitTrack AI — Personal Gym & Nutrition Coach

FitTrack AI is an agentic fitness companion built with the **Google Agent Development Kit (ADK)** and powered by **Gemini 3.6 Flash**. It coaches gym-goers through personalized workout routines, tracks fitness sessions in real time, calculates precise caloric deficits and macronutrient splits, and searches healthy recipes with rich visual cards.

![FitTrack AI Demo](demo.gif)

---

## ⚡ What FitTrack AI Does

FitTrack AI acts as an end-to-end fitness coach that combines structured database records, long-term memory, external recipe lookups, and visual generation:

1. **🏋️ Workout Routines & Exercise Tracking**
   - Accesses a curated catalog of gym routines categorized by target muscle groups (Full Body, Upper Body, Legs, Core & Cardio) stored in **Cloud Firestore**.
   - Retrieves granular exercise breakdowns with set counts, rep ranges, and rest periods.
   - Logs completed workout sessions with duration, estimated calories burned, and subjective exertion notes.

2. **🔥 Caloric Deficit & TDEE Calculations**
   - Computes Basal Metabolic Rate (BMR) via the Mifflin-St Jeor equation and calculates Total Daily Energy Expenditure (TDEE).
   - Projects safe caloric deficits for target weekly weight loss and computes optimal protein, carbohydrate, and fat macro distributions.
   - Executes dynamic computations securely in the **Agent Platform Code Execution Sandbox**.

3. **🥗 Healthy Recipes & Nutrition Search**
   - Integrates with **TheMealDB API** to discover high-protein, calorie-conscious meals and recipes based on user ingredients.
   - Emits rich recipe cards with step-by-step preparation instructions and verified nutrition metrics.

4. **🧠 Long-Term Memory & User Preferences**
   - Uses **Vertex AI Memory Bank** to persist user details across conversations (e.g., injuries, fitness goals, dietary restrictions, favorite exercises).
   - Preloads memories at conversation start and automatically captures new context after every interaction.

5. **🖼️ Fitness Visual Generation & Cloud Storage**
   - Generates fitness milestone visuals and meal representations using **`gemini-3.1-flash-lite-image`**.
   - Persists generated media assets directly into a **Google Cloud Storage (GCS)** bucket.

6. **🪟 Agent-First UI (A2UI)**
   - Emits **A2UI v0.8 Basic Catalog** surfaces (Cards, Columns, Rows, Text, Images) for rich visual responses rather than plain text.

---

## 🏗️ Architecture & Google Cloud Stack

| Layer | Component | Powered By |
|---|---|---|
| 🤖 **Reasoning Core** | Agent Loop & Tool Calling | `gemini-3.6-flash` on ADK |
| 🧠 **Memory** | Cross-Session User Memory | Vertex AI Memory Bank (`PreloadMemoryTool` + auto-extraction) |
| 🗄️ **Database** | Workouts & Logs | Cloud Firestore (`workouts`, `user_workouts`, `user_weight`) |
| 🧪 **Code Sandbox** | Dynamic Calculations | Agent Engine Sandbox Code Executor |
| 🥗 **Nutrition Data** | Healthy Recipe Search | TheMealDB API |
| 🎨 **Media Generation** | Fitness Visuals | `gemini-3.1-flash-lite-image` |
| 📦 **Asset Storage** | Public Image Hosting | Google Cloud Storage (`gs://...`) |
| 🪟 **Display UI** | Rich Visual Cards | A2UI (v0.8 Basic Catalog) |
| 🌐 **Frontend** | Chat UI & A2A Proxy | FastAPI + Glassmorphism Web Interface |

---

## 🚧 Status of Planned Features

- [x] Firestore workout routines and user logging
- [x] TDEE and macro target calculation engine
- [x] Vertex AI Memory Bank long-term profile persistence
- [x] TheMealDB recipe retrieval with nutritional breakdown
- [x] A2UI card renderer for rich display surfaces
- [x] Cloud Storage image generation pipeline
- [ ] *Planned, not yet implemented:* Real-time camera form check using Gemini multimodal video
- [ ] *Planned, not yet implemented:* Wearable device sync (Google Fit / Health Connect API)

---

## 🚀 Local Setup & Run Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+ (for UI recording or frontend tooling)
- Google Cloud SDK (`gcloud`) authenticated to your Google Cloud project

### 1. Clone Repository & Setup Environment

```bash
git clone https://github.com/Trickster7u7/buildwithgemini-fittrack-ai.git
cd buildwithgemini-fittrack-ai
```

### 2. Configure Credentials

Ensure your environment is authenticated with Google Cloud:

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project <YOUR_GCP_PROJECT_ID>
```

### 3. Run the Agent Locally (ADK Web)

```bash
cd simple-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start the ADK local playground
adk web . --port 8080 --reload_agents
```

Navigate to `http://localhost:8080/dev-ui/?app=app` in your browser to interact with the agent in development mode.

### 4. Run the Custom Web Frontend

To launch the standalone web interface with the A2A proxy:

```bash
cd frontend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export AGENT_ENGINE_RESOURCE_NAME="<YOUR_AGENT_RESOURCE_NAME>"
export AGENT_DIRECTORY="app"

python main.py
```

Open `http://localhost:8080` to access the FitTrack AI web application.

---

## 📄 License

This project is created as part of the Build with Gemini workshop. Distributed under the Apache 2.0 License.
