import requests
import time

BASE = "https://ramratanpadhy59--grand-tribunal-inference-api.modal.run"

# Step 1: Warm up the GPU container via judge (triggers TribunalModel cold start)
print("=== Step 1: Warming up GPU container via /judge ===")
print("(This will trigger cold start - may take 3-5 minutes)...")
t0 = time.time()
try:
    r = requests.post(f"{BASE}/judge", json={"topic": "test", "argument": "test arg"}, timeout=600)
    elapsed = time.time() - t0
    print(f"Judge response in {elapsed:.1f}s: {r.status_code} - {r.text[:200]}")
except Exception as e:
    elapsed = time.time() - t0
    print(f"Judge failed after {elapsed:.1f}s: {e}")

# Step 2: Now try TTS on the warm container
print("\n=== Step 2: Testing /tts on warm container ===")
t0 = time.time()
try:
    r = requests.post(f"{BASE}/tts", json={"text": "The court has reached a verdict."}, timeout=300)
    elapsed = time.time() - t0
    print(f"TTS response in {elapsed:.1f}s: {r.status_code}")
    ct = r.headers.get("content-type", "unknown")
    print(f"Content-Type: {ct}")
    print(f"Content-Length: {len(r.content)}")
    if r.status_code == 200 and "audio" in ct:
        print(f"First 4 bytes: {r.content[:4]}")
        print("SUCCESS: Got audio!")
    else:
        print(f"Body: {r.text[:500]}")
except Exception as e:
    elapsed = time.time() - t0
    print(f"TTS failed after {elapsed:.1f}s: {e}")
