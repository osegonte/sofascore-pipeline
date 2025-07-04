#!/usr/bin/env python3
"""
Stage 6 ML Model Development - Complete Demo Script

This script demonstrates the complete ML pipeline for football goal prediction.
Run this to test all Stage 6 functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

async def run_complete_ml_demo():
    """Run complete ML pipeline demonstration."""
    print("🚀 Stage 6 ML Model Development - Complete Demo")
    print("=" * 60)
    
    # Check prerequisites
    print("\n1️⃣ Checking Prerequisites...")
    
    # Check training data
    training_data = Path("demo_training_dataset.csv")
    if not training_data.exists():
        print("❌ Training data not found: demo_training_dataset.csv")
        print("   Run Stage 5 feature engineering first:")
        print("   python src/feature_engineering/cli_commands.py")
        return False
    
    try:
        import pandas as pd
        df = pd.read_csv(training_data)
        print(f"✅ Training data: {len(df)} samples, {len(df.columns)} features")
    except ImportError:
        print("❌ pandas not available. Install with: pip install pandas")
        return False
    
    # Check ML dependencies
    try:
        from src.ml_models.cli_commands import MLCommandRunner
        print("✅ ML modules available")
    except ImportError as e:
        print(f"❌ ML modules not available: {e}")
        print("   Install requirements: pip install -r requirements_ml.txt")
        return False
    
    # Initialize ML runner
    runner = MLCommandRunner()
    
    # 2. Training Phase
    print("\n2️⃣ Training ML Models...")
    training_success = await runner.run_training("demo_training_dataset.csv")
    
    if not training_success:
        print("❌ Training failed. Cannot continue demo.")
        return False
    
    # 3. Evaluation Phase
    print("\n3️⃣ Evaluating Models...")
    evaluation_success = await runner.run_evaluation("demo_training_dataset.csv")
    
    if not evaluation_success:
        print("⚠️  Evaluation failed, but continuing demo...")
    
    # 4. Prediction Demo
    print("\n4️⃣ Running Prediction Demo...")
    prediction_success = await runner.run_prediction_demo()
    
    if not prediction_success:
        print("⚠️  Prediction demo had issues, but continuing...")
    
    # 5. Summary
    print("\n5️⃣ Demo Summary")
    print("=" * 30)
    print(f"Training: {'✅' if training_success else '❌'}")
    print(f"Evaluation: {'✅' if evaluation_success else '❌'}")
    print(f"Prediction: {'✅' if prediction_success else '❌'}")
    
    # Show file locations
    print("\n📁 Generated Files:")
    
    models_dir = Path("data/models/saved_models")
    if models_dir.exists():
        model_files = list(models_dir.glob("*.joblib"))
        print(f"   Models: {len(model_files)} files in {models_dir}")
    
    eval_dir = Path("data/models/evaluation")
    if eval_dir.exists():
        reports = list(eval_dir.glob("**/*.json"))
        plots = list(eval_dir.glob("**/*.png"))
        print(f"   Evaluation: {len(reports)} reports, {len(plots)} plots in {eval_dir}")
    
    # Next steps
    print("\n🎯 Next Steps:")
    print("   1. Try individual predictions:")
    print("      python -m src.main predict-ml --match-id 12345 --minute 80 --home-score 2 --away-score 1")
    print("   2. Start prediction API:")
    print("      python -m src.main serve-ml")
    print("   3. Check model performance:")
    print("      python -m src.main ml-status")
    
    return training_success and evaluation_success and prediction_success

if __name__ == "__main__":
    success = asyncio.run(run_complete_ml_demo())
    if success:
        print("\n🎉 Stage 6 ML Demo completed successfully!")
    else:
        print("\n⚠️  Stage 6 ML Demo completed with issues. Check logs above.")
    
    sys.exit(0 if success else 1)
