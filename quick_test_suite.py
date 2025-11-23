import asyncio
import json
from datetime import datetime
from pathlib import Path
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import random

class QuickTestSuite:
    """Lightweight test suite that visualizes existing data in Qdrant"""
    
    def __init__(self):
        self.qdrant_client = AsyncQdrantClient(url="http://localhost:6333")
        self.test_collection = "agent-zero-test-results"
        self.main_collection = "agent-zero-mlcreator"
        
    async def analyze_existing_data(self):
        """Analyze the existing mlcreator collection"""
        print("\n📊 Analyzing Existing Data...")
        print("=" * 60)
        
        try:
            # Get collection info
            info = await self.qdrant_client.get_collection(self.main_collection)
            
            # Scroll through all points
            points, _ = await self.qdrant_client.scroll(
                collection_name=self.main_collection,
                limit=100,
                with_payload=True,
                with_vectors=False
            )
            
            # Analyze metadata
            areas = {}
            tags_count = {}
            categories = {}
            
            for point in points:
                payload = point.payload
                
                # Count areas
                area = payload.get("area", "unknown")
                areas[area] = areas.get(area, 0) + 1
                
                # Count tags
                tags = payload.get("tags", [])
                for tag in tags:
                    tags_count[tag] = tags_count.get(tag, 0) + 1
                
                # Count categories
                category = payload.get("category", "unknown")
                categories[category] = categories.get(category, 0) + 1
            
            analysis = {
                "total_points": len(points),
                "vector_size": info.config.params.vectors.size,
                "areas": areas,
                "top_tags": dict(sorted(tags_count.items(), key=lambda x: x[1], reverse=True)[:10]),
                "categories": categories
            }
            
            print(f"✅ Total Memories: {analysis['total_points']}")
            print(f"✅ Vector Dimensions: {analysis['vector_size']}")
            print(f"\n📂 Areas Distribution:")
            for area, count in analysis['areas'].items():
                print(f"   {area}: {count}")
            
            print(f"\n🏷️ Top Tags:")
            for tag, count in list(analysis['top_tags'].items())[:5]:
                print(f"   {tag}: {count}")
            
            return analysis
            
        except Exception as e:
            print(f"❌ Failed to analyze: {e}")
            return None
    
    async def create_test_visualization(self, analysis):
        """Create a test results collection for visualization"""
        print("\n🎨 Creating Test Visualization...")
        
        try:
            # Delete existing test collection
            try:
                await self.qdrant_client.delete_collection(self.test_collection)
            except:
                pass
            
            # Create new collection
            await self.qdrant_client.create_collection(
                collection_name=self.test_collection,
                vectors_config=VectorParams(size=3, distance=Distance.COSINE)
            )
            
            # Create test result points
            test_results = [
                {
                    "name": "Memory Coverage",
                    "score": min(analysis['total_points'] / 10, 1.0),
                    "status": "EXCELLENT" if analysis['total_points'] >= 10 else "GOOD",
                    "metric": f"{analysis['total_points']} memories"
                },
                {
                    "name": "Vector Quality",
                    "score": 1.0 if analysis['vector_size'] == 768 else 0.5,
                    "status": "EXCELLENT" if analysis['vector_size'] == 768 else "WARNING",
                    "metric": f"{analysis['vector_size']}D vectors"
                },
                {
                    "name": "Metadata Richness",
                    "score": min(len(analysis['top_tags']) / 10, 1.0),
                    "status": "EXCELLENT" if len(analysis['top_tags']) >= 8 else "GOOD",
                    "metric": f"{len(analysis['top_tags'])} unique tags"
                },
                {
                    "name": "Area Distribution",
                    "score": min(len(analysis['areas']) / 3, 1.0),
                    "status": "EXCELLENT" if len(analysis['areas']) >= 2 else "GOOD",
                    "metric": f"{len(analysis['areas'])} areas"
                }
            ]
            
            points = []
            for i, result in enumerate(test_results):
                # Create a 3D vector for visualization
                # [score, random_x, random_y] for nice clustering
                vector = [
                    result['score'],
                    random.uniform(0.3, 0.7),
                    random.uniform(0.3, 0.7)
                ]
                
                point = PointStruct(
                    id=i,
                    vector=vector,
                    payload={
                        "test_name": result['name'],
                        "score": round(result['score'], 2),
                        "status": result['status'],
                        "metric": result['metric'],
                        "timestamp": datetime.now().isoformat(),
                        "color": "green" if result['score'] >= 0.8 else "orange" if result['score'] >= 0.6 else "red"
                    }
                )
                points.append(point)
            
            await self.qdrant_client.upsert(
                collection_name=self.test_collection,
                points=points
            )
            
            print(f"✅ Created {len(points)} test visualizations")
            print(f"\n🎯 View at: http://localhost:6333/dashboard#/collections/{self.test_collection}")
            
            return test_results
            
        except Exception as e:
            print(f"❌ Failed to create visualization: {e}")
            return None
    
    def generate_report(self, analysis, test_results):
        """Generate HTML report"""
        report_dir = Path("test_results")
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON report
        json_report = {
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "test_results": test_results,
            "overall_score": sum(r['score'] for r in test_results) / len(test_results)
        }
        
        json_path = report_dir / f"report_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(json_report, f, indent=2)
        
        # HTML report
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Agent Zero Test Report - {timestamp}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #667eea;
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .timestamp {{
            text-align: center;
            color: #666;
            margin-bottom: 40px;
        }}
        .score-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .score-card h2 {{
            margin: 0;
            font-size: 3em;
        }}
        .score-card p {{
            margin: 10px 0 0 0;
            font-size: 1.2em;
        }}
        .test-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .test-card {{
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            transition: transform 0.3s;
        }}
        .test-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }}
        .test-card.excellent {{
            border-color: #4caf50;
            background: #f1f8f4;
        }}
        .test-card.good {{
            border-color: #ff9800;
            background: #fff8f1;
        }}
        .test-card.warning {{
            border-color: #f44336;
            background: #fff1f1;
        }}
        .test-card h3 {{
            margin-top: 0;
            color: #333;
        }}
        .score {{
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .metric {{
            color: #666;
            font-size: 0.9em;
        }}
        .status {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            margin-top: 10px;
        }}
        .status.excellent {{
            background: #4caf50;
            color: white;
        }}
        .status.good {{
            background: #ff9800;
            color: white;
        }}
        .status.warning {{
            background: #f44336;
            color: white;
        }}
        .analysis {{
            background: #f5f5f5;
            padding: 20px;
            border-radius: 10px;
            margin-top: 30px;
        }}
        .analysis h3 {{
            color: #667eea;
            margin-top: 0;
        }}
        .stat-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #ddd;
        }}
        .stat-row:last-child {{
            border-bottom: none;
        }}
        .link-box {{
            background: #667eea;
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin-top: 30px;
        }}
        .link-box a {{
            color: white;
            text-decoration: none;
            font-size: 1.2em;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Agent Zero Test Report</h1>
        <div class="timestamp">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        
        <div class="score-card">
            <h2>{json_report['overall_score']:.1%}</h2>
            <p>Overall System Health</p>
        </div>
        
        <div class="test-grid">
"""
        
        for result in test_results:
            status_class = result['status'].lower()
            html_content += f"""
            <div class="test-card {status_class}">
                <h3>{result['name']}</h3>
                <div class="score">{result['score']:.1%}</div>
                <div class="metric">{result['metric']}</div>
                <span class="status {status_class}">{result['status']}</span>
            </div>
"""
        
        html_content += f"""
        </div>
        
        <div class="analysis">
            <h3>📊 Detailed Analysis</h3>
            <div class="stat-row">
                <span>Total Memories:</span>
                <strong>{analysis['total_points']}</strong>
            </div>
            <div class="stat-row">
                <span>Vector Dimensions:</span>
                <strong>{analysis['vector_size']}D</strong>
            </div>
            <div class="stat-row">
                <span>Unique Tags:</span>
                <strong>{len(analysis['top_tags'])}</strong>
            </div>
            <div class="stat-row">
                <span>Areas:</span>
                <strong>{', '.join(analysis['areas'].keys())}</strong>
            </div>
        </div>
        
        <div class="link-box">
            <a href="http://localhost:6333/dashboard#/collections/agent-zero-test-results" target="_blank">
                🎨 View Interactive Visualization in Qdrant Dashboard →
            </a>
        </div>
    </div>
</body>
</html>
"""
        
        html_path = report_dir / f"report_{timestamp}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n📄 Reports saved:")
        print(f"   JSON: {json_path}")
        print(f"   HTML: {html_path}")
        
        return html_path
    
    async def run(self):
        """Run the test suite"""
        print("🚀 Agent Zero Quick Test Suite")
        print("=" * 60)
        
        # Analyze existing data
        analysis = await self.analyze_existing_data()
        
        if not analysis:
            print("❌ Failed to analyze data")
            return
        
        # Create visualization
        test_results = await self.create_test_visualization(analysis)
        
        if not test_results:
            print("❌ Failed to create visualization")
            return
        
        # Generate report
        html_path = self.generate_report(analysis, test_results)
        
        # Print summary
        overall_score = sum(r['score'] for r in test_results) / len(test_results)
        
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        print(f"Overall Score: {overall_score:.1%}")
        print(f"Total Memories: {analysis['total_points']}")
        print(f"Vector Quality: {analysis['vector_size']}D ({'✅ EXCELLENT' if analysis['vector_size'] == 768 else '⚠️ CHECK'})")
        print("\n🎯 Next Steps:")
        print(f"   1. Open: {html_path}")
        print(f"   2. View Qdrant: http://localhost:6333/dashboard")
        print("=" * 60)

if __name__ == "__main__":
    suite = QuickTestSuite()
    asyncio.run(suite.run())
