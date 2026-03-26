from audioengine import masteranalyzer
import time

if __name__ == "__main__":
        print("Dynamizer starting. Press Ctrl+C to quit.")
        time.sleep(.2)
        masteranalyzer.activate()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")

        print("Dynamizer shutting down, goodbye")
