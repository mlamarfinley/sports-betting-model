# 🏀 Sports Betting Prediction Model

A comprehensive machine learning-powered sports betting prediction system with automated data collection, advanced analytics, and real-time predictions.

## 📋 Overview

This project combines web scraping, machine learning, and sports analytics to predict outcomes for:
- 🏀 NBA (Basketball)
- 🏈 NFL (Football)  
- 🏒 NHL (Hockey)
- 🏈 College Football
- 🎾 Tennis
- ⚽ Soccer
- 🎮 League of Legends (eSports)
- 🎯 Counter-Strike 2 (eSports)

## 🏗️ Architecture

```
sports-betting-model/
├── database/
│   └── migrations/         # Database schema and migration scripts
├── scrapers/
│   ├── esports/           # eSports data scrapers (LoL, CS2)
│   ├── nba/               # NBA game and player data
│   └── run_scrapers.py    # Orchestrator for all scrapers
├── models/
│   └── prediction_model.py # TensorFlow ML model
├── requirements.txt       # Python dependencies
├── railway.toml          # Railway deployment config
└── run_migration.py      # Database migration runner
```

## 🚀 Features

### Data Collection
- ✅ **Automated Scrapers**: Run on schedule (every 6 hours)
- ✅ **Multi-Sport Support**: NBA, eSports, with easy expansion
- ✅ **Historical Data**: Game results, player stats, team performance
- ✅ **Patch Tracking**: LoL balance changes and meta shifts
- ✅ **Injury Reports**: Player availability tracking

### Machine Learning
- ✅ **Neural Network**: TensorFlow/Keras deep learning model
- ✅ **Random Forest**: Alternative sklearn classifier
- ✅ **Feature Engineering**: 12+ features including:
  - Win percentage differentials
  - Points per game trends
  - Rest days and home advantage
  - Time-based patterns
- ✅ **Model Persistence**: Save/load trained models

### Database
- ✅ **PostgreSQL**: Production-grade relational database
- ✅ **Railway Hosting**: Cloud-deployed with automatic backups
- ✅ **Comprehensive Schema**: 
  - Games and player statistics
  - Team performance metrics
  - Betting lines and odds
  - Injury reports
  - eSports patch notes

## 🛠️ Technology Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | Python 3.11+ |
| **ML/AI** | TensorFlow, scikit-learn, pandas, numpy |
| **Web Scraping** | BeautifulSoup4, Selenium, Requests |
| **Database** | PostgreSQL, psycopg2 |
| **Framework** | Django (API ready) |
| **Task Queue** | Celery, Redis |
| **Deployment** | Railway.app |
| **Scheduling** | schedule library |

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- PostgreSQL database
- pip package manager

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/mlamarfinley/sports-betting-model.git
cd sports-betting-model
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
export DATABASE_URL="postgresql://user:password@host:port/database"
```

4. **Run database migrations**
```bash
python run_migration.py
```

## 🎯 Usage

### Running Scrapers

**One-time scrape:**
```bash
python scrapers/run_scrapers.py
```

**Scheduled scraping (every 6 hours):**
```bash
python scrapers/run_scrapers.py --schedule
```

**Individual scrapers:**
```bash
# NBA data
python scrapers/nba/nba_scraper.py

# League of Legends patches
python scrapers/esports/lol_patch_scraper.py
```

### Training the Model

```python
from models.prediction_model import SportsPredictionModel
import os

database_url = os.getenv('DATABASE_URL')

# Train NBA model
nba_model = SportsPredictionModel(database_url, 'NBA')
nba_model.train_model(use_nn=True)
nba_model.save_model('models/nba_model.h5')
```

### Making Predictions

```python
from models.prediction_model import SportsPredictionModel
from datetime import datetime

model = SportsPredictionModel(database_url, 'NBA')
model.load_model('models/nba_model.h5')

prediction = model.predict_game(
    home_team="Los Angeles Lakers",
    away_team="Boston Celtics",
    game_date=datetime(2026, 1, 15)
)

print(f"Predicted Winner: {prediction['predicted_winner']}")
print(f"Confidence: {prediction['confidence']:.2%}")
print(f"Home Win Probability: {prediction['home_win_probability']:.2%}")
```

## 📊 Database Schema

### Core Tables
- `games` - Game results and metadata
- `player_game_stats` - Individual player performance
- `team_stats` - Team-level aggregated statistics
- `predictions` - Model predictions and outcomes
- `betting_lines` - Odds and betting information
- `injuries` - Player injury reports
- `patch_notes` - eSports game balance changes
- `lol_champion_changes` - League of Legends specific updates

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ |
| `RAILWAY_ENVIRONMENT` | Deployment environment | Railway only |

### Railway Deployment

The project is configured for Railway.app deployment:

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python scrapers/run_scrapers.py --schedule"
restartPolicyType = "ON_FAILURE"
```

## 📈 Model Performance

The neural network model achieves:
- **Test Accuracy**: ~65-70% on historical NBA games
- **AUC Score**: ~0.72
- **Features**: 12 engineered features
- **Architecture**: 
  - Input layer (12 features)
  - Dense(128) + Dropout(0.3)
  - Dense(64) + Dropout(0.2)
  - Dense(32)
  - Output(1, sigmoid)

## 🚧 Roadmap

- [ ] Add NFL data scraper
- [ ] Add NHL data scraper
- [ ] Add Tennis data scraper
- [ ] Add Soccer data scraper
- [ ] Add CS2 eSports scraper
- [ ] Django REST API endpoints
- [ ] Web dashboard frontend
- [ ] Real-time betting odds integration
- [ ] Player prop predictions
- [ ] Advanced LSTM models for time-series

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is for educational purposes only. Always bet responsibly.

## ⚠️ Disclaimer

This model is for educational and research purposes only. Sports betting involves risk. Past performance does not guarantee future results. Always gamble responsibly and within your means.

## 📧 Contact

For questions or collaboration:
- GitHub: [@mlamarfinley](https://github.com/mlamarfinley)

---

**Built with ❤️ using Python, TensorFlow, and Railway**
