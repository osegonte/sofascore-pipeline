"""
Main.py ML Integration Patch

Add these imports and commands to your existing src/main.py file.
"""

# Add these imports after your existing imports
try:
    from src.ml_models.cli_commands import (
        run_ml_training, run_ml_evaluation, run_ml_prediction,
        run_ml_demo, run_ml_api_server
    )
    ML_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  ML models not available: {e}")
    ML_AVAILABLE = False

# Add these CLI commands to your existing click group

@cli.command()
@click.option('--data', '-d', default='demo_training_dataset.csv', help='Path to training data CSV file')
@click.option('--target', '-t', help='Specific target column to train')
@click.option('--models', '-m', multiple=True, help='Specific models to train (xgboost, random_forest, logistic_regression)')
def train_ml(data, target, models):
    """Train ML models for goal prediction."""
    if not ML_AVAILABLE:
        click.echo("❌ ML models not available. Install requirements:")
        click.echo("   pip install -r requirements_ml.txt")
        return
    
    models_list = list(models) if models else None
    success = asyncio.run(run_ml_training(data, target, models_list))
    
    if success:
        click.echo("✅ ML training completed successfully!")
    else:
        click.echo("❌ ML training failed. Check logs for details.")

@cli.command()
@click.option('--data', '-d', default='demo_training_dataset.csv', help='Path to test data CSV file')
@click.option('--models-dir', '-m', help='Directory containing saved models')
@click.option('--no-plots', is_flag=True, help='Skip plot generation')
def evaluate_ml(data, models_dir, no_plots):
    """Evaluate trained ML models."""
    if not ML_AVAILABLE:
        click.echo("❌ ML models not available.")
        return
    
    success = asyncio.run(run_ml_evaluation(data, models_dir, not no_plots))
    
    if success:
        click.echo("✅ ML evaluation completed successfully!")
    else:
        click.echo("❌ ML evaluation failed. Check logs for details.")

@cli.command()
@click.option('--match-id', '-i', type=int, required=True, help='Match ID')
@click.option('--minute', '-min', type=int, required=True, help='Current minute')
@click.option('--home-score', '-hs', type=int, required=True, help='Home team score')
@click.option('--away-score', '-as', type=int, required=True, help='Away team score')
@click.option('--home-team-id', type=int, default=1, help='Home team ID')
@click.option('--away-team-id', type=int, default=2, help='Away team ID')
def predict_ml(match_id, minute, home_score, away_score, home_team_id, away_team_id):
    """Make goal prediction for current match state."""
    if not ML_AVAILABLE:
        click.echo("❌ ML models not available.")
        return
    
    success = asyncio.run(run_ml_prediction(
        match_id, minute, home_score, away_score, home_team_id, away_team_id
    ))
    
    if not success:
        click.echo("❌ Prediction failed. Check logs for details.")

@cli.command()
def predict_ml_demo():
    """Run goal prediction demo with sample scenarios."""
    if not ML_AVAILABLE:
        click.echo("❌ ML models not available.")
        return
    
    success = asyncio.run(run_ml_demo())
    
    if success:
        click.echo("✅ ML demo completed successfully!")
    else:
        click.echo("❌ ML demo failed. Check logs for details.")

@cli.command()
@click.option('--host', '-h', default='0.0.0.0', help='API server host')
@click.option('--port', '-p', type=int, default=8001, help='API server port')
def serve_ml(host, port):
    """Start the prediction API server."""
    if not ML_AVAILABLE:
        click.echo("❌ ML models not available.")
        return
    
    click.echo(f"🚀 Starting ML API server on {host}:{port}")
    click.echo(f"📚 Documentation: http://{host}:{port}/docs")
    
    try:
        asyncio.run(run_ml_api_server(host, port))
    except KeyboardInterrupt:
        click.echo("\n👋 API server stopped")

@cli.command()
def ml_status():
    """Show ML pipeline status and information."""
    click.echo("📊 Stage 6 ML Pipeline Status")
    click.echo("=" * 40)
    
    # Check training data
    training_data_exists = Path("demo_training_dataset.csv").exists()
    click.echo(f"Training Data: {'✅' if training_data_exists else '❌'} demo_training_dataset.csv")
    
    if training_data_exists:
        try:
            import pandas as pd
            df = pd.read_csv("demo_training_dataset.csv")
            click.echo(f"  Samples: {len(df)}")
            click.echo(f"  Features: {len(df.columns)}")
            
            # Check target distributions
            targets = ['goal_next_1min_any', 'goal_next_5min_any', 'goal_next_15min_any']
            for target in targets:
                if target in df.columns:
                    positive = df[target].sum()
                    total = len(df)
                    click.echo(f"  {target}: {positive}/{total} ({positive/total*100:.1f}%)")
        except Exception as e:
            click.echo(f"  Error reading data: {e}")
    
    # Check models directory
    models_dir = Path("data/models/saved_models")
    models_exist = models_dir.exists()
    click.echo(f"Models Directory: {'✅' if models_exist else '❌'} {models_dir}")
    
    if models_exist:
        model_files = list(models_dir.glob("*.joblib"))
        click.echo(f"  Saved Models: {len(model_files)}")
        
        # Group by target
        targets_found = set()
        for model_file in model_files:
            for target in ['goal_next_1min_any', 'goal_next_5min_any', 'goal_next_15min_any']:
                if target in model_file.name:
                    targets_found.add(target)
        
        for target in targets_found:
            target_models = [f for f in model_files if target in f.name]
            click.echo(f"  {target}: {len(target_models)} models")
    
    # Check ML availability
    click.echo(f"ML Available: {'✅' if ML_AVAILABLE else '❌'}")
    
    if not ML_AVAILABLE:
        click.echo("To enable ML features:")
        click.echo("  pip install -r requirements_ml.txt")
    
    # Usage examples
    if training_data_exists and ML_AVAILABLE:
        click.echo("\n🎯 Quick Start Commands:")
        click.echo("  python -m src.main train-ml")
        click.echo("  python -m src.main evaluate-ml") 
        click.echo("  python -m src.main predict-ml --match-id 12345 --minute 75 --home-score 1 --away-score 0")
        click.echo("  python -m src.main serve-ml")
