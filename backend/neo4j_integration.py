"""
Neo4j Integration for FairMind Knowledge Graph
Handles bias detection through graph relationships and causal chains
"""

from neo4j import GraphDatabase
from typing import Dict, List, Optional
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FairMindKnowledgeGraph:
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """Initialize Neo4j connection for FairMind Knowledge Graph"""
        # Use environment variables if not provided
        self.uri = uri or os.getenv('NEO4J_URI', 'neo4j://localhost:7687')
        self.user = user or os.getenv('NEO4J_USER', 'neo4j')
        self.password = password or os.getenv('NEO4J_PASSWORD', 'password')
        
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            self.logger = logging.getLogger(__name__)
            self.logger.info(f"Successfully connected to Neo4j at {self.uri}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Neo4j: {e}")
            raise
        
    def close(self):
        """Close the database connection"""
        if hasattr(self, 'driver'):
            self.driver.close()
        
    def create_bias_pattern(self, pattern_name: str, nodes: List[Dict], relationships: List[Dict]):
        """Create a bias pattern in the knowledge graph"""
        with self.driver.session() as session:
            # Create nodes
            for node in nodes:
                session.run("""
                    MERGE (n:Node {id: $id, type: $type, bias_score: $bias_score})
                    """, id=node['id'], type=node['type'], bias_score=node['bias_score'])
            
            # Create relationships
            for rel in relationships:
                session.run("""
                    MATCH (a:Node {id: $source_id})
                    MATCH (b:Node {id: $target_id})
                    MERGE (a)-[r:RELATES_TO {type: $rel_type, bias_contribution: $bias_contribution}]->(b)
                    """, source_id=rel['source_id'], target_id=rel['target_id'], 
                    rel_type=rel['type'], bias_contribution=rel['bias_contribution'])
            
            # Create pattern node
            session.run("""
                CREATE (p:BiasPattern {name: $name, confidence: $confidence, impact: $impact})
                """, name=pattern_name, confidence=0.85, impact="HIGH")
    
    def detect_bias_propagation(self, model_id: str) -> List[Dict]:
        """Detect bias propagation patterns for a specific model"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (m:Model {id: $model_id})-[:HAS_FEATURE]->(f:Feature)
                MATCH (f)-[:INFLUENCES]->(d:Decision)
                WHERE f.bias_score > 0.1
                RETURN f.name as feature, f.bias_score as bias_score, 
                       d.name as decision, d.impact as impact
                ORDER BY f.bias_score DESC
                """, model_id=model_id)
            
            return [record.data() for record in result]
    
    def find_causal_chains(self, source_feature: str, max_hops: int = 3) -> List[Dict]:
        """Find causal chains from a source feature"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH path = (s:Feature {name: $source_feature})-[:CAUSES*1..$max_hops]->(t:Target)
                RETURN path, length(path) as chain_length
                ORDER BY chain_length DESC
                """, source_feature=source_feature, max_hops=max_hops)
            
            return [record.data() for record in result]
    
    def get_bias_patterns(self) -> List[Dict]:
        """Get all detected bias patterns"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:BiasPattern)
                OPTIONAL MATCH (p)-[:AFFECTS]->(m:Model)
                RETURN p.name as pattern, p.confidence as confidence, 
                       p.impact as impact, count(m) as affected_models
                ORDER BY p.confidence DESC
                """)
            
            return [record.data() for record in result]
    
    def run_cypher_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """Execute a custom Cypher query"""
        with self.driver.session() as session:
            if parameters is None:
                parameters = {}
            result = session.run(query, parameters)
            return [record.data() for record in result]
    
    def create_model_graph(self, model_data: Dict):
        """Create a graph representation of a model's features and decisions"""
        with self.driver.session() as session:
            # Create model node
            session.run("""
                MERGE (m:Model {id: $model_id, name: $model_name, type: $model_type})
                """, model_id=model_data['id'], model_name=model_data['name'], 
                model_type=model_data['type'])
            
            # Create feature nodes
            for feature in model_data['features']:
                session.run("""
                    MERGE (f:Feature {id: $feature_id, name: $feature_name, 
                           bias_score: $bias_score, importance: $importance})
                    MERGE (m:Model {id: $model_id})
                    MERGE (m)-[:HAS_FEATURE]->(f)
                    """, feature_id=feature['id'], feature_name=feature['name'],
                    bias_score=feature['bias_score'], importance=feature['importance'],
                    model_id=model_data['id'])
            
            # Create decision nodes
            for decision in model_data['decisions']:
                session.run("""
                    MERGE (d:Decision {id: $decision_id, name: $decision_name, 
                           impact: $impact, fairness_score: $fairness_score})
                    MERGE (m:Model {id: $model_id})
                    MERGE (m)-[:MAKES_DECISION]->(d)
                    """, decision_id=decision['id'], decision_name=decision['name'],
                    impact=decision['impact'], fairness_score=decision['fairness_score'],
                    model_id=model_data['id'])
    
    def analyze_bias_cascade(self, model_id: str) -> Dict:
        """Analyze how bias cascades through a model's decision-making process"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (m:Model {id: $model_id})-[:HAS_FEATURE]->(f:Feature)
                MATCH (f)-[:INFLUENCES]->(d:Decision)
                WITH f, d, f.bias_score * f.importance as bias_contribution
                RETURN f.name as feature, f.bias_score as bias_score, 
                       f.importance as importance, bias_contribution,
                       d.name as decision, d.fairness_score as fairness_score
                ORDER BY bias_contribution DESC
                """, model_id=model_id)
            
            cascade_data = [record.data() for record in result]
            
            # Calculate cascade metrics
            total_bias_contribution = sum(item['bias_contribution'] for item in cascade_data)
            avg_fairness_score = sum(item['fairness_score'] for item in cascade_data) / len(cascade_data)
            
            return {
                'cascade_data': cascade_data,
                'total_bias_contribution': total_bias_contribution,
                'average_fairness_score': avg_fairness_score,
                'high_risk_features': [item for item in cascade_data if item['bias_contribution'] > 0.2]
            }
    
    def get_graph_metrics(self) -> Dict:
        """Get overall graph metrics"""
        with self.driver.session() as session:
            # Count nodes by type
            node_counts = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as node_type, count(n) as count
                ORDER BY count DESC
                """)
            
            # Count relationships by type
            rel_counts = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as relationship_type, count(r) as count
                ORDER BY count DESC
                """)
            
            # Get bias pattern statistics
            bias_stats = session.run("""
                MATCH (p:BiasPattern)
                RETURN count(p) as total_patterns,
                       avg(p.confidence) as avg_confidence,
                       count(CASE WHEN p.impact = 'HIGH' THEN p END) as high_impact_patterns
                """).single()
            
            return {
                'node_counts': [record.data() for record in node_counts],
                'relationship_counts': [record.data() for record in rel_counts],
                'bias_statistics': bias_stats.data() if bias_stats else {}
            }

# Example usage
if __name__ == "__main__":
    try:
        # Initialize the knowledge graph
        print("🔗 Connecting to Neo4j...")
        kg = FairMindKnowledgeGraph()
        
        # Example model data
        model_data = {
            'id': 'loan_model_v1',
            'name': 'Loan Approval Model V1',
            'type': 'GRADIENT_BOOSTING',
            'features': [
                {'id': 'credit_score', 'name': 'Credit Score', 'bias_score': 0.15, 'importance': 0.8},
                {'id': 'income', 'name': 'Income', 'bias_score': 0.25, 'importance': 0.7},
                {'id': 'zip_code', 'name': 'Zip Code', 'bias_score': 0.32, 'importance': 0.6},
                {'id': 'education', 'name': 'Education Level', 'bias_score': 0.18, 'importance': 0.5}
            ],
            'decisions': [
                {'id': 'loan_approval', 'name': 'Loan Approval', 'impact': 'HIGH', 'fairness_score': 0.75},
                {'id': 'interest_rate', 'name': 'Interest Rate', 'impact': 'MEDIUM', 'fairness_score': 0.68}
            ]
        }
        
        print("📊 Creating model graph...")
        kg.create_model_graph(model_data)
        
        print("🔍 Analyzing bias cascade...")
        cascade_analysis = kg.analyze_bias_cascade('loan_model_v1')
        print("✅ Bias Cascade Analysis:", cascade_analysis)
        
        print("📈 Getting graph metrics...")
        metrics = kg.get_graph_metrics()
        print("✅ Graph Metrics:", metrics)
        
        print("🎉 Neo4j integration successful!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure to:")
        print("1. Set up Neo4j (see NEO4J_SETUP_GUIDE.md)")
        print("2. Update your .env file with Neo4j credentials")
        print("3. Install dependencies: pip install -r requirements_neo4j.txt")
    
    finally:
        if 'kg' in locals():
            kg.close()
