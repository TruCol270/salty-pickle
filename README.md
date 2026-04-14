# Salty Pickle 🐟

An AI-powered ultra/trail running training plan scheduler that automatically syncs with Strava and Google Calendar.

## Features

### Core Functionality
- **Strava Integration** - Connect your Strava account to automatically sync completed workouts
- **Google Calendar** - Training plans automatically sync to your calendar
- **Whoop Integration** - Connect Whoop for recovery-based training adjustments
- **AI Plan Generation** - Generate personalized training plans based on your race goals
- **Race URL Analysis** - Paste a race webpage URL to auto-extract race details (distance, elevation, difficulty)
- **Auto-Adjustment** - Missed workouts automatically reschedule to keep you on track
- **Performance-Based Updates** - Plan adjusts based on how well you're performing
- **Recovery-Aware Planning** - Plan adjusts based on Whoop recovery scores

### User Preferences
- Preferred workout days
- Preferred workout time (morning/afternoon/evening)
- Equipment availability
- Injury history for injury-aware planning
- Sleep target for recovery tracking

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│                    (React + Vite)                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐   │
│  │Dashboard │  │CreatePlan│  │     Preferences          │   │
│  └──────────┘  └──────────┘  └──────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  FastAPI    │
                    │   Backend   │
                    └──────┬──────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
┌───▼────┐  ┌─────────────▼┐  ┌────────────────▼──┐
│ Strava │  │   Google     │  │  Whoop API       │
│  API   │  │  Calendar    │  │  (Recovery)      │
└────────┘  └──────────────┘  └────────────────────┘
    │            │                    │
    ▼            ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                   PostgreSQL + Redis                        │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack
- **Backend**: FastAPI (Python 3.11)
- **Database**: PostgreSQL + SQLAlchemy (async)
- **Cache**: Redis
- **Frontend**: React + TypeScript + TailwindCSS
- **LLM**: OpenAI GPT-4o
- **Scheduler**: APScheduler (nightly jobs)

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/strava/authorize` | GET | Connect Strava |
| `/auth/google/authorize` | GET | Connect Google Calendar |
| `/api/v1/workouts/sync` | POST | Sync Strava activities |
| `/api/v1/plans/ai-generate` | POST | Generate AI training plan |
| `/api/v1/calendar/sync?plan_id=X` | POST | Sync plan to Google Calendar |
| `/api/v1/races/analyze?url=X` | POST | Analyze race webpage |
| `/api/v1/user/preferences` | GET/PUT | User preferences |
| `/api/v1/analytics/performance-check` | POST | Cross-reference Strava with plan |

## Getting Started

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Strava API credentials
- Google Cloud project with OAuth
- OpenAI API key

### Environment Variables

Create a `.env` file:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/salty_pickle
REDIS_URL=redis://localhost:6379/0

STRAVA_CLIENT_ID=your_strava_client_id
STRAVA_CLIENT_SECRET=your_strava_client_secret
STRAVA_REDIRECT_URI=http://localhost:8080/auth/strava/callback

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8080/auth/google/callback

OPENAI_API_KEY=your_openai_api_key
SECRET_KEY=your_random_secret_key
ALLOWED_ORIGINS=["http://localhost:3000"]
```

### Running Locally

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f
```

- API: http://localhost:8080
- Frontend: http://localhost:3000
- API Docs: http://localhost:8080/docs

### Connecting Integrations

1. **Strava**: Visit `http://localhost:8080/auth/strava/authorize`
2. **Google Calendar**: Visit `http://localhost:8080/auth/google/authorize`

### Creating a Training Plan

1. Go to http://localhost:3000/create
2. Optionally paste a race URL to auto-fill details
3. Fill in your race info and fitness level
4. Click "Generate Training Plan"
5. Workouts automatically sync to Google Calendar

## Deployment

### Google Cloud Run (Production)

```bash
# Set GCP project
export GCP_PROJECT_ID=your-project

# Deploy
./deploy.sh
```

Requires:
- Google Cloud SQL (PostgreSQL)
- Cloud Run
- Cloud Scheduler (for nightly jobs)

## Project Structure

```
salty-pickle/
├── .worktrees/mvp/
│   ├── app/
│   │   ├── agents/          # AI agents
│   │   │   ├── adjustment_agent.py
│   │   │   └── plan_generator.py
│   │   ├── api/            # FastAPI routes
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   │   ├── strava.py
│   │   │   ├── google_calendar.py
│   │   │   ├── race_analyzer.py
│   │   │   ├── performance_analyzer.py
│   │   │   └── ...
│   │   ├── scheduler/      # Background jobs
│   │   └── main.py          # App entry point
│   ├── frontend/           # React app
│   ├── docker-compose.yml
│   └── requirements.txt
```

## Future Features

- [ ] Whoop integration for recovery data
- [ ] Coros integration
- [ ] Voice interface
- [ ] Mobile app
- [ ] Social features (training partners)
- [ ] Race predictions

## License

MIT

## Contributing

1. Fork the repo
2. Create a feature branch
3. Make changes and test
4. Push to GitHub
