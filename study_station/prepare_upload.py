import os
import shutil
import sys
import glob

def main():
    print("Preparing Upload Directory...")
    
    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dest_root = os.path.join(script_dir, "study_station_upload")
    
    # 1. Clean previous destination directory if exists
    if os.path.exists(dest_root):
        print(f"Clearing existing directory: {dest_root}")
        shutil.rmtree(dest_root)
        
    os.makedirs(dest_root, exist_ok=True)
    
    # =============================================
    # 2. Copy website/ folder (entirely)
    # =============================================
    source_website = os.path.join(script_dir, "website")
    dest_website = os.path.join(dest_root, "website")
    if os.path.exists(source_website):
        print("Copying 'website' directory...")
        shutil.copytree(source_website, dest_website)
        print("  Done: website/")
    else:
        print("WARNING: 'website' directory not found!")
        
    # =============================================
    # 3. Copy backend-server/ (excluding venv, __pycache__)
    # =============================================
    source_backend = os.path.join(script_dir, "backend-server")
    dest_backend = os.path.join(dest_root, "backend-server")
    if os.path.exists(source_backend):
        print("Copying 'backend-server' directory (excluding venv, __pycache__)...")
        ignore_pattern = shutil.ignore_patterns('venv', '__pycache__', '*.pyc', '.git', '.vscode')
        shutil.copytree(source_backend, dest_backend, ignore=ignore_pattern)
        print("  Done: backend-server/")
    else:
        print("WARNING: 'backend-server' directory not found!")
    
    # =============================================
    # 4. Copy books/ folder (excluding chrome/edge profiles and lock files)
    # =============================================
    source_books = os.path.join(script_dir, "books")
    dest_books = os.path.join(dest_root, "books")
    if os.path.exists(source_books):
        print("Copying 'books' directory (excluding browser profiles, locks)...")
        ignore_books = shutil.ignore_patterns(
            'chrome_profile', 'chrome_profile_*', 
            'edge_profile_*', '.chapter_locks',
            '__pycache__', '*.pyc'
        )
        shutil.copytree(source_books, dest_books, ignore=ignore_books)
        print("  Done: books/")
    else:
        print("WARNING: 'books' directory not found!")
    
    # =============================================
    # 5. Copy android/ folder (excluding build artifacts)
    # =============================================
    source_android = os.path.join(script_dir, "android")
    dest_android = os.path.join(dest_root, "android")
    if os.path.exists(source_android):
        print("Copying 'android' directory (excluding build artifacts)...")
        ignore_android = shutil.ignore_patterns(
            '.gradle', 'build', '.idea', 'local.properties',
            '*.apk', '*.aab', 'captures', '.cxx',
            '__pycache__', '*.pyc', '.DS_Store'
        )
        shutil.copytree(source_android, dest_android, ignore=ignore_android)
        print("  Done: android/")
    else:
        print("WARNING: 'android' directory not found!")
    
    # =============================================
    # 6. Copy Level folders (10th_Level, 12th_Level, Graduation_Level)
    # =============================================
    for level_folder in ['10th_Level', '12th_Level', 'Graduation_Level']:
        source_level = os.path.join(script_dir, level_folder)
        dest_level = os.path.join(dest_root, level_folder)
        if os.path.exists(source_level):
            print(f"Copying '{level_folder}' directory...")
            ignore_pattern = shutil.ignore_patterns('__pycache__', '*.pyc')
            shutil.copytree(source_level, dest_level, ignore=ignore_pattern)
            print(f"  Done: {level_folder}/")
        else:
            print(f"SKIP: '{level_folder}' not found (optional)")
    
    # =============================================
    # 6. Copy root-level .py files
    # =============================================
    print("Copying root-level .py files...")
    py_files = [f for f in os.listdir(script_dir) if f.endswith('.py') and f != 'prepare_upload.py']
    for py_file in py_files:
        src = os.path.join(script_dir, py_file)
        dst = os.path.join(dest_root, py_file)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            print(f"  Copied: {py_file}")
    
    # =============================================
    # 7. Copy other important files (agents.md, docs/, etc.)
    # =============================================
    for extra_file in ['agents.md', 'implementation_plan.md']:
        src = os.path.join(script_dir, extra_file)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(dest_root, extra_file))
            print(f"  Copied: {extra_file}")
    
    source_docs = os.path.join(script_dir, "docs")
    dest_docs = os.path.join(dest_root, "docs")
    if os.path.exists(source_docs):
        print("Copying 'docs' directory...")
        shutil.copytree(source_docs, dest_docs)
        print("  Done: docs/")
    
    # =============================================
    # Summary
    # =============================================
    print("\n" + "=" * 55)
    print("  Upload preparation complete!")
    print("=" * 55)
    print(f"  Location: {dest_root}")
    print("")
    print("  Contents:")
    for item in sorted(os.listdir(dest_root)):
        item_path = os.path.join(dest_root, item)
        if os.path.isdir(item_path):
            count = sum(1 for _ in os.walk(item_path))
            print(f"    [DIR]  {item}/ ({count} subdirs)")
        else:
            size_kb = os.path.getsize(item_path) / 1024
            print(f"    [FILE] {item} ({size_kb:.1f} KB)")
    print("")
    print("  Aap is folder ko zip karke server par upload kar sakte hain.")

if __name__ == "__main__":
    main()
