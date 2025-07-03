"""
CLI commands for feature engineering operations.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from src.feature_engineering.pipeline import FeatureEngineeringPipeline, FeatureConfig
except ImportError:
    # Fallback to relative import
    from .pipeline import FeatureEngineeringPipeline, FeatureConfig

async def run_feature_generation(match_ids: List[int], output_dir: str = "features", start_minute: int = 59):
    """Run feature generation for specified matches."""
    print(f"🔄 Generating features for {len(match_ids)} matches")
    
    config = FeatureConfig()
    pipeline = FeatureEngineeringPipeline(config=config)
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    for match_id in match_ids:
        try:
            training_examples = await pipeline.process_match_for_ml(match_id)
            
            # Filter by start minute
            filtered_examples = [
                ex for ex in training_examples 
                if ex.get('minute', 0) >= start_minute
            ]
            
            result = {
                'match_id': match_id,
                'total_examples': len(filtered_examples),
                'features_per_example': len(filtered_examples[0]) if filtered_examples else 0,
                'training_examples': filtered_examples,
                'generation_time': datetime.now().isoformat()
            }
            
            # Save to file
            output_file = output_path / f"match_{match_id}_features.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"✅ Match {match_id}: {len(filtered_examples)} examples -> {output_file}")
            
        except Exception as e:
            print(f"❌ Match {match_id} failed: {e}")

async def run_training_dataset_creation(match_ids: List[int], output_file: str = "training_dataset.csv"):
    """Create unified training dataset."""
    print(f"🎯 Creating training dataset from {len(match_ids)} matches")
    
    config = FeatureConfig()
    pipeline = FeatureEngineeringPipeline(config=config)
    
    all_examples = []
    for match_id in match_ids:
        try:
            examples = await pipeline.process_match_for_ml(match_id)
            all_examples.extend(examples)
        except Exception as e:
            print(f"⚠️  Skipping match {match_id}: {e}")
    
    if not all_examples:
        print("❌ No training examples generated")
        return
    
    # Save to CSV
    try:
        import pandas as pd
        df = pd.DataFrame(all_examples)
        df.to_csv(output_file, index=False)
        print(f"✅ Training dataset created: {len(all_examples)} examples -> {output_file}")
    except ImportError:
        # Fallback to manual CSV creation
        import csv
        if all_examples:
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=all_examples[0].keys())
                writer.writeheader()
                writer.writerows(all_examples)
            print(f"✅ Training dataset created: {len(all_examples)} examples -> {output_file}")

async def demo_feature_pipeline():
    """Demo the feature engineering pipeline."""
    print("🚀 Feature Engineering Pipeline Demo")
    print("=" * 50)
    
    demo_match_ids = [12345, 12346, 12347]
    
    print("\n1️⃣ Generating features for sample matches...")
    await run_feature_generation(demo_match_ids, "demo_features")
    
    print("\n2️⃣ Creating unified training dataset...")
    await run_training_dataset_creation(demo_match_ids, "demo_training_dataset.csv")
    
    print("\n✅ Demo completed!")
    print("Check generated files:")
    print("   - demo_features/ (individual match features)")
    print("   - demo_training_dataset.csv (unified dataset)")

if __name__ == "__main__":
    asyncio.run(demo_feature_pipeline())
