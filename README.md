# AutoGen System Monitor

A full-stack autonomous agent system for AI-driven software development, featuring real-time monitoring and progress tracking via a web dashboard.

## Features
- Autonomous planning, validation, and execution of software projects using LLM agents
- Real-time dashboard for monitoring agent status, progress, and logs
- Modular teams: Frontend, Backend, Database, QA/Testing, DevOps
- Progress bar and log panels for each team and task
- Hybrid progress tracking (explicit and heuristic)
- FastAPI backend with Socket.IO for live updates
- React + TypeScript frontend with Tailwind CSS for dark/light mode

## Project Structure
```
AIAgentSystem/
├── backend/
│   ├── main.py            # Main backend logic, agent orchestration, event emitters
│   ├── dashboard.py       # Socket.IO dashboard server
│   ├── requirements.txt   # Python dependencies
│   └── ...
├── client/
│   ├── src/               # React frontend source code
│   ├── public/
│   ├── package.json       # Frontend dependencies
│   └── ...
├── README.md              # Project documentation (this file)
└── sample_tech_spec.md    # Example technical specification
```

## How It Works
1. **Planning Phase:**
   - LLM agents analyze the technical spec and generate a detailed development plan (JSON).
   - QA agent reviews and approves the plan.
2. **Execution Phase:**
   - Each team (Frontend, Backend, etc.) executes its tasks using agent tools (file creation, code writing).
   - Agents report task completion using explicit markers (e.g., `TASK_COMPLETED: FE-SDEV-001`).
   - Heuristic logic also detects task completion from file/directory creation.
3. **Monitoring:**
   - The dashboard displays agent status, progress, logs, and team panels in real time.
   - Progress bar updates as tasks are completed.

## Getting Started
### Backend
1. Create and activate a Python virtual environment:
   ```sh
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```
2. Install dependencies:
   ```sh
   pip install -r backend/requirements.txt
   ```
3. Start the backend:
   ```sh
   python backend/main.py --spec sample_tech_spec.md
   ```

### Frontend
1. Navigate to the client folder:
   ```sh
   cd client
   ```
2. Install dependencies:
   ```sh
   npm install
   ```
3. Start the frontend:
   ```sh
   npm run dev
   ```
4. Open your browser to `http://localhost:5173` (or the port shown in the terminal).

## Customization
- Update `sample_tech_spec.md` to change the project requirements.
- Add new agent roles or tools in `backend/main.py`.
- Modify frontend UI in `client/src/`.

## Technologies Used
- Python, FastAPI, Socket.IO
- React, TypeScript, Tailwind CSS
- AutoGen agent framework
- Azure OpenAI (configurable via `OAI_CONFIG_LIST`)

## License
MIT

## Authors
- Your Name (Aishwarya)
- Contributors: See commit history
