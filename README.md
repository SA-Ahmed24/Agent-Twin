# Agent Twin 🧠

An AI twin, an AI version of you, that learns your writing styles, remembers your experiences, and generates content that sounds exactly like you. Built with Django and powered by Google Gemini AI.

## ✨ Features

### 🎯 Core Features
- **Writing Style Learning**: Automatically extracts and learns your writing style (tone, vocabulary, sentence structure)
- **Experience Memory**: Remembers your internships, projects, roles, and achievements
- **Personal Information Storage**: Stores your background, education, interests, and more
- **Content Generation**: Generates resumes, cover letters, LinkedIn posts, and emails in your voice
- **Multimodal Memory**: Processes text, images, and audio messages
- **Memory Timeline**: Visual timeline showing what the AI remembers about you

### 🗣️ Voice Agent
- **Voice Cloning**: Create a voice clone using ElevenLabs
- **Voice Conversations**: Have natural voice conversations with your AI twin
- **Public Voice Agent**: Shareable voice agent links for recruiters or others
- **Animated Waveform**: Beautiful visual feedback during voice interactions

### 💬 Conversational AI
- **Context-Aware Chat**: Maintains conversation history and context
- **Memory Extraction**: Automatically extracts new memories from conversations
- **Follow-up Questions**: Handles follow-up questions and modifications naturally

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip
- Google Gemini API key
- ElevenLabs API key (for voice features)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd "Agent Twin"
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```bash
   GEMINI_API_KEY=your_gemini_api_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   ```
   
   **Getting API Keys:**
   - **Gemini**: Visit [Google AI Studio](https://aistudio.google.com/) and create an API key
   - **ElevenLabs**: Sign up at [ElevenLabs](https://elevenlabs.io) and create an API key from your profile settings

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Open your browser and navigate to `http://localhost:8000`
   - Sign up for a new account or log in

## 📁 Project Structure

```
Agent Twin/
├── agent_twin/          # Django project settings
├── api/                 # Main application
│   ├── models.py       # Database models
│   ├── views.py        # API endpoints
│   ├── services/       # Business logic
│   │   ├── gemini_service.py      # Gemini AI integration
│   │   ├── memory_extractor.py    # Memory extraction
│   │   ├── memory_retriever.py    # Memory retrieval
│   │   └── voice_service.py       # ElevenLabs integration
│   └── utils/          # Utility functions
├── frontend/           # Frontend files
│   ├── static/        # CSS, JS, images
│   └── *.html        # HTML templates
├── media/             # User uploads (not in git)
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## 🎨 Pages & Features

### Main Pages
- **`/`** - Chat interface for conversations with your AI twin
- **`/login/`** - User login
- **`/signup/`** - User registration
- **`/onboarding/`** - Initial setup wizard for new users
- **`/timeline/`** - Memory timeline visualization
- **`/voice/`** - Private voice agent page
- **`/voice/public/<token>/`** - Public shareable voice agent

### Key Features
- **Chat Interface**: Natural conversation with context awareness
- **Memory Timeline**: Beautiful brain-themed visualization of stored memories
- **Voice Agent**: Voice conversations with cloned voice
- **File Upload**: Upload resumes, essays, documents for analysis
- **Memory Extraction**: Automatic extraction from conversations and uploads

## 🔧 API Endpoints

### Authentication
- `POST /api/auth/signup/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/user/` - Get current user info

### Memory & Content
- `POST /api/upload-sample/` - Upload text/file for analysis
- `POST /api/generate/` - Generate content in user's style
- `GET /api/memory/view/` - View memory timeline
- `POST /api/memory/reset/` - Reset all memories

### Voice Agent
- `POST /api/voice/upload-sample/` - Upload voice sample for cloning
- `POST /api/voice/ask/` - Send voice input, get audio response
- `GET /api/voice/profile/` - Get voice profile status
- `POST /api/voice/share/create/` - Create shareable voice token
- `GET /api/voice/share/list/` - List shareable tokens
- `POST /api/voice/public/<token>/ask/` - Public voice agent endpoint

## 🛠️ Technologies Used

- **Backend**: Django 4.2, Django REST Framework
- **AI**: Google Gemini 2.0 Flash
- **Voice**: ElevenLabs API
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Database**: SQLite (development), PostgreSQL (production ready)

## 📝 Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

## 🚢 Deployment

### Production Checklist
1. Set `DEBUG = False` in `settings.py`
2. Configure `ALLOWED_HOSTS`
3. Set up a production database (PostgreSQL recommended)
4. Configure static files serving
5. Set up HTTPS (required for Web Speech API)
6. Update CORS settings for your domain
7. Set up environment variables securely

### Recommended Hosting
- **Backend**: Heroku, Railway, DigitalOcean, AWS
- **Database**: PostgreSQL (Heroku Postgres, AWS RDS)
- **Static Files**: AWS S3, CloudFront, or CDN

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Google Gemini for AI capabilities
- ElevenLabs for voice cloning technology
- Django community for the excellent framework

## 📧 Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Built with ❤️ for personalized AI experiences**

