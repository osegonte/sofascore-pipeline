# SofaScore Data Pipeline

A modular, end-to-end data pipeline for harvesting, processing, and analyzing football data from SofaScore and other sources.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Development](#development)
- [Data Schema](#data-schema)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)

## ✨ Features

- **Modular Design**: Easily extensible architecture with separate components for scraping, storage, and processing
- **Multiple Storage Backends**: Support for PostgreSQL, MongoDB, and S3-compatible storage
- **Real-time & Batch Processing**: Handle both live match data and historical analysis
- **Data Quality Assurance**: Built-in validation, monitoring, and alerting
- **Scalable Infrastructure**: Docker-based deployment with optional orchestration
- **Feature Engineering**: Ready-to-use features for machine learning models

## 🏗️ Architecture

The pipeline consists of 9 main stages:

1. **Plan & Prep**: Schema definition and infrastructure setup
2. **Discover & Reverse-Engineer**: SofaScore API endpoint mapping
3. **Ingest & Persist**: Raw data collection and storage
4. **Normalize & Curate**: Data transformation and structuring
5. **Feature Engineering**: ML-ready feature generation
6. **External Enrichment**: Additional data source integration
7. **Orchestration & Monitoring**: Job scheduling and health checks
8. **Storage Management**: Data lake and warehouse organization
9. **Documentation & Maintenance**: Comprehensive project documentation

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.9+
- PostgreSQL 15+ (if not using Docker)
- Redis (optional, for caching)

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/sofascore-pipeline.git
cd sofascore-pipeline
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
nano .env
```

### 3. Docker Deployment (Recommended)

```bash
# Start core services
docker-compose up -d postgres redis

# Run database migrations
docker-compose run --rm sofascore_app python scripts/setup_database.py

# Start the full pipeline
docker-compose up -d
```

### 4. Manual Setup (Alternative)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .

# Setup database
python scripts/setup_database.py

# Run the pipeline
python -m src.main
```

## ⚙️ Configuration

### Environment Variables

Key configuration options in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://localhost:5432/sofascore_db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `S3_BUCKET_NAME` | S3 bucket for raw data | `sofascore-raw-data` |
| `SOFASCORE_BASE_URL` | SofaScore API base URL | `https://api.sofascore.com/api/v1` |
| `SCRAPE_INTERVAL_LIVE` | Live match scraping interval (seconds) | `60` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `COMPETITIONS` | Comma-separated list of competitions | `premier-league,champions-league` |

### Database Schema

The pipeline uses a two-layer approach:

#### Raw Layer (JSON Storage)
- `matches_raw`: Raw match data from SofaScore feed endpoint
- `events_raw`: Raw event data (goals, cards, substitutions)
- `stats_raw`: Raw minute-by-minute statistics
- `momentum_raw`: Raw momentum/attack data
- `scrape_jobs`: Metadata for tracking scraping jobs

#### Curated Layer (Normalized Tables)
- `competitions`: Tournament information
- `teams`: Team metadata and details
- `players`: Player profiles and information
- `matches`: Normalized match data
- `lineups`: Starting lineups and substitutions
- `events`: Match events with coordinates and xG values
- `minute_stats`: Minute-by-minute match statistics
- `player_match_stats`: Individual player performance data

## 🛠️ Development

### Project Structure

```
sofascore-pipeline/
├── src/                    # Main application code
│   ├── scrapers/          # Data collection modules
│   ├── storage/           # Database and file storage
│   ├── models/            # Data models and schemas
│   └── utils/             # Utility functions
├── config/                # Configuration files
├── sql/                   # Database migrations and queries
├── scripts/               # Utility scripts
├── tests/                 # Test suite
└── data/                  # Local data storage
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_scrapers.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## 📊 Data Schema

### Key Entities

#### Matches
- Match metadata (teams, competition, date)
- Live status and current minute
- Final scores and statistics
- Venue and referee information

#### Events
- Goals, cards, substitutions
- Minute and coordinates
- Expected Goals (xG) values
- Player involvement

#### Statistics
- Minute-by-minute data
- Possession, shots, passes
- Team and player performance
- Advanced metrics (xG, passing accuracy)

### Sample Queries

```sql
-- Get live matches
SELECT * FROM live_matches;

-- Recent goals with xG values
SELECT 
    m.home_team_name,
    m.away_team_name,
    e.minute,
    e.event_type,
    e.xg_value
FROM events e
JOIN matches m ON e.match_id = m.match_id
WHERE e.event_type = 'goal'
  AND m.match_date >= CURRENT_DATE - INTERVAL '1 day'
ORDER BY m.match_date DESC, e.minute;

-- Team possession by minute
SELECT 
    minute,
    home_possession,
    away_possession
FROM minute_stats
WHERE match_id = 12345
ORDER BY minute;
```

## 🔗 API Endpoints

The pipeline includes optional REST API endpoints:

- `GET /matches/live` - Current live matches
- `GET /matches/{match_id}` - Specific match details
- `GET /matches/{match_id}/events` - Match events timeline
- `GET /matches/{match_id}/stats` - Match statistics
- `POST /scraper/trigger` - Manually trigger scraping job

## 📈 Monitoring & Alerting

### Health Checks

The pipeline includes comprehensive monitoring:

- Database connectivity
- API response times
- Data freshness checks
- Error rate tracking

### Alerting

Configure alerts via:
- Slack webhooks
- Email notifications
- Custom monitoring integrations

### Grafana Dashboards

Pre-built dashboards for:
- Scraping success rates
- Data pipeline latency
- Match coverage metrics
- System resource usage

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check database status
docker-compose logs postgres

# Reset database
docker-compose down
docker volume rm sofascore-pipeline_postgres_data
docker-compose up -d postgres
```

#### Rate Limiting Issues
```bash
# Check Redis for rate limit status
docker-compose exec redis redis-cli
> GET rate_limit:sofascore_api
```

#### Missing Data
```bash
# Run data quality checks
python scripts/data_quality_check.py

# Check scraping logs
tail -f logs/sofascore_pipeline.log
```

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
```bash
export ENVIRONMENT=production
export DEBUG=false
```

2. **Database Migration**
```bash
python scripts/setup_database.py --production
```

3. **Scale Services**
```bash
docker-compose -f docker-compose.prod.yml up -d --scale celery_worker=3
```

### Cloud Deployment Options

- **AWS**: ECS + RDS + ElastiCache + S3
- **GCP**: Cloud Run + Cloud SQL + Memorystore + Cloud Storage
- **Azure**: Container Instances + PostgreSQL + Redis Cache + Blob Storage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation
- Ensure all checks pass

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- SofaScore for providing comprehensive football data
- The open-source community for excellent tools and libraries
- Contributors and maintainers

## 📞 Support

- Create an issue for bug reports
- Join our Discord community
- Check the [Wiki](https://github.com/yourusername/sofascore-pipeline/wiki) for detailed guides

---

**Next Steps**: Proceed to Stage 2 to implement the SofaScore API discovery and scraping modules.