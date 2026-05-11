# 🚀 SwarmBharat AI

**India's First Conversational AI for Government Schemes, Jobs, and Life Advice**

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 🌟 What is SwarmBharat AI?

SwarmBharat AI is a multi-domain conversational AI assistant specifically designed for **Indian users**. Unlike generic AI chatbots, it:

- ✅ **Knows Indian context** - PM-KISAN, tax rules, Canada PR, local jobs
- ✅ **Converses like a friend** - Not robotic, validates emotions, asks questions
- ✅ **Provides real data** - ₹ amounts, scheme names, deadlines, eligibility
- ✅ **Multi-language ready** - Hindi, Telugu, Tamil support

## 🎯 Domains Supported

| Domain | Features |
|--------|----------|
| 🌾 **Farming** | PM-KISAN, KCC, Soil Health Card, FPO schemes |
| 💼 **Career** | Job listings, salary data, resume help, interview prep |
| 💰 **Finance** | Tax saving, mutual funds, gold prices, investment advice |
| 🛫 **Immigration** | Canada PR, Australia PR, CRS scores, visa guidance |
| 🏥 **Health** | Ayushman Bharat, insurance, hospital info |
| 🎓 **Education** | Scholarships, education loans, exam prep |
| ⚖️ **Legal** | Rights guidance, document help |

## 🚀 Quick Start

### Local Development

```bash
# Clone the repo
git clone https://github.com/Bharadwaj9429/SwarmBharat-AI.git
cd SwarmBharat-AI

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (copy from .env.example)
cp .env.example .env
# Edit .env with your API keys

# Run the server
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/api/v1/health` | GET | Health check |
| `/api/v1/auth/signup` | POST | User registration |
| `/api/v1/auth/login` | POST | User login |
| `/api/v1/query` | POST | AI query endpoint |

### Example Query

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user@example.com",
    "query": "How can I get PM-KISAN benefits?",
    "max_tokens": 1500
  }'
```

## 🏗️ Tech Stack

- **Backend:** FastAPI (Python 3.11)
- **AI Engine:** Groq (Llama-3.3-70B) + Ollama fallback
- **Database:** MongoDB Atlas
- **Cache:** Redis Cloud
- **Translation:** Sarvam AI
- **Real-time Data:** RapidAPI + Government APIs

## 📦 Deployment

### Railway (Recommended)

1. Push code to GitHub
2. Go to [Railway](https://railway.app)
3. New Project → Deploy from GitHub repo
4. Add environment variables from `.env.production`
5. Deploy!

### Environment Variables

Required:
- `GROQ_API_KEY` - Get from [Groq](https://console.groq.com)
- `MONGODB_URI` - MongoDB Atlas connection string
- `REDIS_URL` - Redis Cloud connection string
- `RAPIDAPI_KEY` - Get from [RapidAPI](https://rapidapi.com)

Optional:
- `SARVAM_API_KEY` - For regional language translation
- `OPENWEATHERMAP_API_KEY` - For weather data

## 🤝 Contributing

This project was built to help Indians navigate complex government schemes and life decisions. Contributions welcome!

## 📄 License

MIT License - feel free to use for personal or commercial projects.

## 🙏 Acknowledgments

- Built with love for 🇮🇳 India
- Powered by Groq, MongoDB, Redis, and open-source community

---

**Live Demo:** [Your Railway URL Here]  
**Repository:** https://github.com/Bharadwaj9429/SwarmBharat-AI
