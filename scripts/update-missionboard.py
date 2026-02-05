#!/usr/bin/env python3
"""
Hourly Missionboard Auto-Update Script

This script runs every hour to:
1. Check git commits for completed work
2. Update roadmap data
3. Sync to web app
4. Calculate new stats
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path("/home/ubuntu/.openclaw/workspace/ai-erp")
ROADMAP_FILE = BASE_DIR / "kontali-roadmap-data.json"
WEB_APP_FILE = BASE_DIR / "roadmap" / "kontali-roadmap-data.json"
MEMORY_DIR = Path("/home/ubuntu/.openclaw/workspace/memory")

def get_recent_commits(hours=1):
    """Get git commits from last N hours"""
    try:
        result = subprocess.run(
            ["git", "log", f"--since={hours} hours ago", "--oneline"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        return result.stdout.strip().split('\n') if result.stdout else []
    except Exception as e:
        print(f"Error getting commits: {e}")
        return []

def recalculate_stats(roadmap):
    """Recalculate all statistics"""
    modules = roadmap['modules']
    
    stats = {
        'totalModules': len(modules),
        'completedModules': sum(1 for m in modules if m['status'] == 'done'),
        'inProgressModules': sum(1 for m in modules if m['status'] == 'in-progress'),
        'plannedModules': sum(1 for m in modules if m['status'] == 'planned'),
        'ideasModules': sum(1 for m in modules if m['status'] == 'ideas'),
        'totalFeatures': sum(len(m['features']) for m in modules),
        'completedFeatures': sum(1 for m in modules for f in m['features'] if f['status'] == 'done'),
        'inProgressFeatures': sum(1 for m in modules for f in m['features'] if f['status'] == 'in-progress'),
        'plannedFeatures': sum(1 for m in modules for f in m['features'] if f['status'] == 'planned'),
        'ideasFeatures': sum(1 for m in modules for f in m['features'] if f['status'] == 'ideas'),
    }
    
    # Calculate overall progress
    total_progress = sum(m.get('progress', 0) for m in modules)
    stats['overallProgress'] = int(total_progress / stats['totalModules']) if stats['totalModules'] > 0 else 0
    
    roadmap['stats'] = stats
    return roadmap

def sync_to_webapp():
    """Copy roadmap data to web app"""
    try:
        with open(ROADMAP_FILE, 'r') as f:
            data = f.read()
        with open(WEB_APP_FILE, 'w') as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"Error syncing to webapp: {e}")
        return False

def commit_changes(message):
    """Commit changes to git"""
    try:
        subprocess.run(["git", "add", "kontali-roadmap-data.json"], cwd=BASE_DIR)
        subprocess.run(["git", "commit", "-m", message], cwd=BASE_DIR)
        return True
    except Exception as e:
        print(f"Error committing: {e}")
        return False

def log_update(message):
    """Log update to daily memory file"""
    today = datetime.now().strftime("%Y-%m-%d")
    memory_file = MEMORY_DIR / f"{today}.md"
    
    timestamp = datetime.now().strftime("%H:%M UTC")
    log_entry = f"\n## {timestamp} - Missionboard Auto-Update\n{message}\n"
    
    try:
        with open(memory_file, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Error logging: {e}")

def main():
    print("="*60)
    print(f"Missionboard Auto-Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Check if file exists
    if not ROADMAP_FILE.exists():
        print("❌ Roadmap file not found!")
        sys.exit(1)
    
    # Load current roadmap
    with open(ROADMAP_FILE, 'r') as f:
        roadmap = json.load(f)
    
    old_stats = roadmap['stats'].copy()
    
    # Recalculate stats
    roadmap = recalculate_stats(roadmap)
    new_stats = roadmap['stats']
    
    # Check for changes
    changes = []
    if old_stats['completedFeatures'] != new_stats['completedFeatures']:
        diff = new_stats['completedFeatures'] - old_stats['completedFeatures']
        changes.append(f"✅ {diff} new feature(s) completed")
    
    if old_stats['overallProgress'] != new_stats['overallProgress']:
        diff = new_stats['overallProgress'] - old_stats['overallProgress']
        changes.append(f"📈 Progress: {old_stats['overallProgress']}% → {new_stats['overallProgress']}% (+{diff}%)")
    
    if changes:
        # Save updated data
        with open(ROADMAP_FILE, 'w') as f:
            json.dump(roadmap, f, indent=2, ensure_ascii=False)
        
        # Sync to webapp
        if sync_to_webapp():
            print("✅ Synced to web app")
        
        # Commit changes
        commit_msg = f"Missionboard auto-update: {', '.join(changes)}"
        if commit_changes(commit_msg):
            print("✅ Committed to git")
        
        # Log update
        log_message = "\\n".join(changes)
        log_update(log_message)
        
        print("\n📊 Changes detected:")
        for change in changes:
            print(f"  {change}")
    else:
        print("ℹ️  No changes detected")
    
    # Print current stats
    print(f"\n📊 Current Stats:")
    print(f"  Modules: {new_stats['totalModules']} ({new_stats['completedModules']} done)")
    print(f"  Features: {new_stats['totalFeatures']} ({new_stats['completedFeatures']} done)")
    print(f"  Progress: {new_stats['overallProgress']}%")
    
    print("\n✅ Update complete!")

if __name__ == "__main__":
    main()
