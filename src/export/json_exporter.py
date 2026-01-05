import json
from datetime import datetime
from pathlib import Path

class JSONExporter:
    def export(self, filename, simplify_output, upload_timestamp):
        """Export analysis data as JSON"""
        
        data = {
            "metadata": {
                "filename": str(Path(filename).name),
                "upload_time": upload_timestamp,
                "export_time": datetime.now().isoformat(),
                "format_version": "1.0"
            },
            "analysis": {
                "total_clauses": len(simplify_output.get('clauses', [])) if simplify_output else 0,
                "total_entities": len(simplify_output.get('entities', [])) if simplify_output else 0,
                "has_risk_assessment": bool(simplify_output.get('risks')) if simplify_output else False
            },
            "clauses": [],
            "entities": [],
            "risks": []
        }
        
        # Add clauses
        if simplify_output and simplify_output.get('clauses'):
            for clause in simplify_output['clauses']:
                data['clauses'].append({
                    "title": clause.get('title', 'Untitled'),
                    "original": clause.get('original_text', ''),
                    "simplified": clause.get('simplified_text', ''),
                    "complexity_level": clause.get('complexity_level', 'unknown')
                })
        
        # Add entities
        if simplify_output and simplify_output.get('entities'):
            for entity in simplify_output['entities']:
                data['entities'].append({
                    "type": entity.get('type', 'unknown'),
                    "value": entity.get('value', ''),
                    "confidence": entity.get('confidence', 0.0)
                })
        
        # Add risks
        if simplify_output and simplify_output.get('risks'):
            for risk in simplify_output['risks']:
                data['risks'].append({
                    "level": risk.get('level', 'unknown'),
                    "description": risk.get('description', ''),
                    "location": risk.get('location', '')
                })
        
        return json.dumps(data, indent=2).encode('utf-8')
