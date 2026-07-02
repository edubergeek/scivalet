import time
import sys

def runScheduler():
    """
    Simulates a cron scheduler running background jobs periodically.
    """
    sleepInterval = 60 # Sleep for 60 seconds between runs in the background
    print("scivalet Cron Scheduler started. Running jobs every 60 seconds...", flush=True)
    
    while True:
        try:
            print("--- Triggering Harvester Daemon ---", flush=True)
            # Future: call harvester script / function
            
            print("--- Triggering Inference Engine ---", flush=True)
            # Future: call inference script / function
            
            print(f"Scheduled tasks completed. Sleeping for {sleepInterval} seconds.", flush=True)
        except Exception as e:
            print(f"Error in scheduler execution loop: {e}", file=sys.stderr, flush=True)
            
        time.sleep(sleepInterval)

if __name__ == "__main__":
    runScheduler()
