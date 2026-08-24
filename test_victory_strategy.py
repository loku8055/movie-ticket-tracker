import sys
import os

# Ensure UTF-8 output encoding for Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from strategies.victory_cinema_strategy import VictoryCinemaStrategy
from services.storage import storage_instance

print("🔍 Testing Victory Cinema Strategy against live website...")

target = storage_instance.get_target("target-victory-toxic")
if not target:
    print("Error: Target not found in storage.")
    sys.exit(1)

print(f"Target Movie: {target['movie_title']}")
print(f"Target URL: {target['target_url']}")

strategy = VictoryCinemaStrategy()
result = strategy.inspect(target)

print("\n--- Check Result ---")
print(f"Status: {result['status']}")
print(f"Is Available: {result['is_available']}")
print(f"Booking URL: {result['booking_url']}")
print(f"Details: {result['details']}")
print(f"Timestamp: {result['timestamp']}")

print("\n✅ Test completed successfully!")
