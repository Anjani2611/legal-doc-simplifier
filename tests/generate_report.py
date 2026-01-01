import json
import asyncio
from httpx import AsyncClient
from src.main import app


async def generate_evaluation_report():
    """Generate a comprehensive evaluation report."""
    
    with open("tests/evaluation_dataset.json") as f:
        eval_data = json.load(f)
    
    results = []
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        for case in eval_data["evaluation_cases"]:
            payload = {
                "text": case["original"],
                "target_level": "simple",
                "language": "en",
                "options": {"keep_bullets": False, "max_summary_sentences": 4}
            }
            
            response = await client.post("/simplify/text", json=payload)
            data = response.json()
            
            results.append({
                "case_id": case["id"],
                "category": case["category"],
                "difficulty": case["difficulty"],
                "original_length": len(case["original"]),
                "simplified_length": len(data["simplified"]),
                "reduction_percent": data["reduction"],
                "original": case["original"][:100] + "...",
                "simplified": data["simplified"]
            })
    
    # Generate summary
    report = {
        "timestamp": "2025-12-28",
        "total_cases": len(results),
        "average_reduction": sum(r["reduction_percent"] for r in results) / len(results),
        "cases_by_difficulty": {
            "easy": len([r for r in results if r["difficulty"] == "easy"]),
            "medium": len([r for r in results if r["difficulty"] == "medium"]),
            "hard": len([r for r in results if r["difficulty"] == "hard"])
        },
        "results": results
    }
    
    with open("tests/evaluation_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("\n=== EVALUATION REPORT SUMMARY ===")
    print(f"Total Cases: {report['total_cases']}")
    print(f"Average Reduction: {report['average_reduction']:.1f}%")
    print(f"Difficulty Distribution: {report['cases_by_difficulty']}")
    print(f"\nReport saved to: tests/evaluation_report.json")


if __name__ == "__main__":
    asyncio.run(generate_evaluation_report())
