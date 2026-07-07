import time
import sys
from backend.harvester import Harvester
from backend.inference import InferenceEngine

def runScheduler():
    """
    Simulates a cron scheduler running background jobs periodically.
    """
    sleepInterval = 300 # Sleep for 5 minutes between runs in the background
    print(f"scivalet Cron Scheduler started. Running jobs every {sleepInterval} seconds...", flush=True)
    
    while True:
        try:
            print("--- Triggering Harvester Daemon ---", flush=True)
            harvesterInstance = Harvester()
            harvesterInstance.runHarvest()
            
            print("--- Triggering Inference Engine ---", flush=True)
            engineInstance = InferenceEngine()
            engineInstance.runInference()
            
            print(f"Scheduled tasks completed. Sleeping for {sleepInterval} seconds.", flush=True)
        except Exception as e:
            print(f"Error in scheduler execution loop: {e}", file=sys.stderr, flush=True)
            
        time.sleep(sleepInterval)

if __name__ == "__main__":
    runScheduler()
