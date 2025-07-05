# SofaScore Data Collection Pipeline

A lean, reliable data collection pipeline for SofaScore football data including live match stats, fixture schedules, and historical records.

## Project Structure

```
sofascore-data-pipeline/
├── src/           # Source code
├── data/          # Raw data storage
├── exports/       # CSV exports
├── tests/         # Test files
├── config/        # Configuration files
├── venv/          # Virtual environment
└── requirements.txt
```

## Setup

Run the setup script:
```bash
chmod +x setup_stage1.sh
./setup_stage1.sh
```

## Usage

Activate the virtual environment:
```bash
source venv/bin/activate
```

Run the main pipeline:
```bash
python src/main.py
```

Run setup tests:
```bash
python tests/test_setup.py
```

## Development Stages

- [x] Stage 1: Initialization
- [ ] Stage 2: Data Collection Development
- [ ] Stage 3: Data Storage and Export
- [ ] Stage 4: Testing and Validation
