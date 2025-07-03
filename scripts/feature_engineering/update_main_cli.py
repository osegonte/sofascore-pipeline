#!/usr/bin/env python3
"""
Update main.py with Stage 5 CLI commands.
"""

import sys
from pathlib import Path

def update_main_py():
    """Add Stage 5 commands to main.py."""
    main_py_path = Path('src/main.py')
    
    if not main_py_path.exists():
        print("❌ src/main.py not found!")
        return False
    
    # Read existing main.py
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    # Check if Stage 5 commands already added
    if 'generate-features' in content:
        print("✅ Stage 5 commands already present in main.py")
        return True
    
    # Add CLI commands before the main function
    cli_commands = '''

# Stage 5: Feature Engineering CLI Commands

@cli.command()
@click.option('--match-ids', '-m', multiple=True, type=int, help='Match IDs to process')
@click.option('--output-dir', '-o', default='features', help='Output directory')
@click.option('--start-minute', default=59, help='Start generating features from this minute')
def generate_features(match_ids, output_dir, start_minute):
    """Generate ML features for matches."""
    if not match_ids:
        print("Please specify at least one match ID with --match-ids")
        return
    
    from src.feature_engineering.cli_commands import run_feature_generation
    asyncio.run(run_feature_generation(list(match_ids), output_dir, start_minute))


@cli.command()
@click.option('--match-ids', '-m', multiple=True, type=int, help='Match IDs to include')
@click.option('--output', '-o', default='training_dataset.csv', help='Output CSV file')
def create_dataset(match_ids, output):
    """Create training dataset from matches."""
    if not match_ids:
        print("Please specify match IDs with --match-ids")
        return
    
    from src.feature_engineering.cli_commands import run_training_dataset_creation
    asyncio.run(run_training_dataset_creation(list(match_ids), output))


@cli.command()
def demo_features():
    """Run feature engineering demo."""
    from src.feature_engineering.cli_commands import demo_feature_pipeline
    asyncio.run(demo_feature_pipeline())
'''
    
    # Insert before main function
    if 'if __name__ == "__main__":' in content:
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            if line.strip() == 'if __name__ == "__main__":':
                new_lines.append(cli_commands)
            new_lines.append(line)
        
        updated_content = '\n'.join(new_lines)
        
        # Backup original
        backup_path = main_py_path.with_suffix('.py.backup')
        with open(backup_path, 'w') as f:
            f.write(content)
        
        # Write updated content
        with open(main_py_path, 'w') as f:
            f.write(updated_content)
        
        print("✅ Successfully updated main.py with Stage 5 commands")
        print(f"📋 Backed up original to {backup_path}")
        return True
    
    else:
        print("❌ Could not find insertion point in main.py")
        return False

if __name__ == "__main__":
    if update_main_py():
        print("\n🎉 Stage 5 CLI integration complete!")
        print("Test with: python -m src.main demo-features")
    else:
        sys.exit(1)
