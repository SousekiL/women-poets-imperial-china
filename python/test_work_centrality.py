import csv, tempfile, unittest
from pathlib import Path
import networkx as nx
class WorkCentralityTest(unittest.TestCase):
 def test_bipartite_metrics(self):
  g=nx.Graph(); g.add_edges_from([('work:1','person:a'),('work:1','person:b'),('work:2','person:b')])
  self.assertEqual(g.degree('work:1'),2); self.assertEqual(g.degree('person:b'),2)
  p=nx.bipartite.weighted_projected_graph(g,{'person:a','person:b'}); self.assertEqual(p['person:a']['person:b']['weight'],1)
if __name__=='__main__': unittest.main()
