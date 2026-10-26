import sys
import subprocess

def main():
    print("=" * 65)
    print("🍎 AuraQA: Autonomous Web QA & Accessibility Agent")
    print("=" * 65)
    print("Launching Streamlit Web Dashboard on http://localhost:8501...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "ui/app.py"], check=True)
    except KeyboardInterrupt:
        print("\nAuraQA server terminated.")

if __name__ == "__main__":
    main()
