import csv,tempfile,unittest
from pathlib import Path
from compute_centrality import read_graph
import networkx as nx
class CentralityFixture(unittest.TestCase):
 def test_parallel_and_kcore(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x.csv';p.write_text('source_id,target_id,relation_class\na,b,F\na,b,S\nb,c,F\nc,a,F\nd,a,F\n')
   g=read_graph(p,False);self.assertEqual(g.degree('a'),4);self.assertEqual(g.__class__.__name__,'MultiGraph')
   core=nx.core_number(nx.Graph(g));self.assertEqual(core['b'],2);self.assertEqual(core['d'],1)
 def test_directed(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x.csv';p.write_text('source_id,target_id,relation_class\na,b,A\n');g=read_graph(p,True);self.assertEqual(g.__class__.__name__,'MultiDiGraph');self.assertEqual(g.out_degree('a'),1)
if __name__=='__main__':unittest.main()
