import sys
import subprocess

def main():
    print("=" * 60)
    print("⚡ AgentFlow: Conversational Enterprise Workflow Orchestrator")
    print("=" * 60)
    print("Launching Streamlit UI...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "ui/app.py"], check=True)
    except KeyboardInterrupt:
        print("\nAgentFlow server stopped gracefully.")

if __name__ == "__main__":
    main()
