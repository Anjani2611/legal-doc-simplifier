import csv
import json
import statistics
import time
from datetime import datetime
from pathlib import Path

import httpx

BACKEND_URL = "http://127.0.0.1:8000"
STRESS_DOCS = [
    "This is a short test document.",
    "Payment terms: Customer shall pay invoice within 30 days of receipt. Late payments incur 1.5% monthly interest.",
    "AGREEMENT: Party A agrees to provide services. Party B agrees to pay $5000. Either party may terminate with 30 days notice. Disputes resolved in court.",
    "Lorem ipsum dolor sit amet. " * 50,  # ~2500 chars
    "Terms and conditions for service usage. User agrees to follow all rules. Service provider not liable for damages. User data is private. " * 20,  # ~5000 chars
]


def run_stress_test(num_requests: int = 20):
    """Run stress test and measure latency."""
    results = {
        "latencies": [],
        "errors": [],
        "success_count": 0,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    client = httpx.Client(timeout=180)
    
    for i in range(num_requests):
        doc_text = STRESS_DOCS[i % len(STRESS_DOCS)]
        payload = {
            "text": doc_text,
            "document_type": "contract",
            "target_level": "simple",
            "language": "en",
        }
        
        try:
            start = time.time()
            resp = client.post(f"{BACKEND_URL}/simplify/text", json=payload)
            elapsed = time.time() - start
            
            if resp.status_code == 200:
                results["latencies"].append(elapsed)
                results["success_count"] += 1
                print(f"✓ Request {i+1}: {elapsed:.2f}s")
            else:
                error_data = resp.json()
                results["errors"].append({
                    "request": i + 1,
                    "status": resp.status_code,
                    "code": error_data.get("code"),
                })
                print(f"✗ Request {i+1}: {error_data.get('code')} ({resp.status_code})")
                
        except httpx.TimeoutException:
            results["errors"].append({"request": i + 1, "error": "TIMEOUT"})
            print(f"✗ Request {i+1}: TIMEOUT")
        except Exception as e:
            results["errors"].append({"request": i + 1, "error": str(e)})
            print(f"✗ Request {i+1}: {str(e)}")
    
    client.close()
    return results


def calculate_metrics(results):
    """Calculate p50, p95, p99 latencies."""
    if not results["latencies"]:
        return {}
    
    latencies = sorted(results["latencies"])
    return {
        "p50": statistics.median(latencies),
        "p95": latencies[int(len(latencies) * 0.95)] if len(latencies) >= 20 else latencies[-1],
        "p99": latencies[int(len(latencies) * 0.99)] if len(latencies) >= 100 else latencies[-1],
        "mean": statistics.mean(latencies),
        "min": min(latencies),
        "max": max(latencies),
    }


def save_metrics(results, metrics):
    """Save metrics to CSV."""
    Path("metrics").mkdir(exist_ok=True)
    csv_path = Path("metrics") / f"stress_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["timestamp", results["timestamp"]])
        writer.writerow(["success_count", results["success_count"]])
        writer.writerow(["total_requests", len(results["latencies"]) + len(results["errors"])])
        writer.writerow(["error_count", len(results["errors"])])
        
        for metric_name, metric_value in metrics.items():
            writer.writerow([metric_name, f"{metric_value:.3f}"])
    
    print(f"\nMetrics saved to: {csv_path}")
    return csv_path


if __name__ == "__main__":
    print("Running stress test (20 requests)...")
    results = run_stress_test(20)
    metrics = calculate_metrics(results)
    
    print(f"\nResults:")
    print(f"Success: {results['success_count']}/20")
    print(f"Errors: {len(results['errors'])}")
    print(f"Metrics: {metrics}")
    
    save_metrics(results, metrics)
