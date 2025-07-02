# SofaScore Pipeline - Project Structure

## 📁 Core Application
```
src/
├── main.py                    # Main CLI application
├── models/
│   ├── raw_models.py         # Raw data models
│   └── curated_models.py     # Normalized data models
├── scrapers/
│   ├── base.py               # Base scraper classes
│   └── sofascore.py          # SofaScore API scraper
├── storage/
│   ├── database.py           # PostgreSQL operations
│   ├── hybrid_database.py    # Hybrid storage manager
│   └── memory_storage.py     # Memory storage fallback
├── transformers/
│   └── sofascore_transformer.py  # JSON transformation
├── etl/
│   └── pipeline.py           # ETL processing pipeline
├── cli/
│   └── etl_commands.py       # ETL CLI commands
└── utils/
    ├── logging.py            # Logging utilities
    └── data_validation.py    # Validation & enrichment
```

## 📁 Configuration
```
config/
└── simple_settings.py       # Application settings
```

## 📁 Database
```
sql/
└── migrations/
    ├── 001_create_raw_tables.sql      # Raw data schema
    └── 002_create_curated_tables.sql  # Normalized schema
```

## 📁 Infrastructure
```
docker-compose.yml           # Docker services
docker-compose.override.yml  # Docker overrides
Dockerfile                  # Application container
requirements.txt            # Python dependencies
```

## 📁 Documentation
```
README.md                   # Project overview
STAGE_4_COMPLETION_REPORT.md # Stage 4 documentation
PROJECT_STRUCTURE.md        # This file
```

## 📁 Utilities
```
etl_direct_usage.py         # Direct ETL usage script
```

## 🚀 Usage Commands

### Data Collection
- `python -m src.main live` - Live data collection
- `python -m src.main test` - Test scraping

### ETL Processing
- `python etl_direct_usage.py complete` - Full pipeline
- `python etl_direct_usage.py etl --limit 5` - Process 5 matches
- `python etl_direct_usage.py quality` - Quality checks
- `python etl_direct_usage.py enrich` - Enrichment demo

### Statistics
- `python -m src.main stats` - Pipeline statistics
- `python -m src.main discover` - API discovery
