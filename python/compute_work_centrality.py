#!/usr/bin/env python3
import argparse,csv,hashlib,json,time
from pathlib import Path
import networkx as nx
ROOT=Path(__file__).resolve().parents[1]; NET=ROOT/'data/derived/network'; OUT=ROOT/'data/derived/work-centrality'

def run_layer(layer):
 edges=[]; works=set(); people=set()
 with (NET/'work_person_edges.csv').open(encoding='utf-8-sig',newline='') as f:
  for r in csv.DictReader(f):
   if r['source_layer']!=layer: continue
   w='work:'+r['work_id']; p='person:'+r['person_node_id']; works.add(w); people.add(p); edges.append((w,p,r))
 G=nx.Graph(); G.add_nodes_from(works,bipartite=0); G.add_nodes_from(people,bipartite=1); G.add_edges_from((a,b) for a,b,_ in edges)
 btw=nx.betweenness_centrality(G,normalized=True)
 rows=[]
 for n in sorted(G):
  typ='work' if n.startswith('work:') else 'person'; rows.append({'node_id':n,'node_type':typ,'degree':G.degree(n),'binary_strength':G.degree(n),'betweenness':btw[n],'component_id':next(i for i,c in enumerate(nx.connected_components(G)) if n in c),'layer':layer,'metric_scope':'native_bipartite','weight_definition':'binary edge presence'})
 # person projection weighted by shared work nodes
 P=nx.bipartite.weighted_projected_graph(G,people)
 prow=[{'node_id':n,'node_type':'person','degree':P.degree(n),'weighted_strength':P.degree(n,weight='weight'),'projection_weight':'shared works/poems','layer':layer,'metric_scope':'person_projection'} for n in sorted(P)]
 return rows,prow,{'nodes':G.number_of_nodes(),'works':len(works),'people':len(people),'edges':len(edges),'projected_nodes':P.number_of_nodes(),'projected_edges':P.number_of_edges(),'uncovered_poems':3999 if layer=='mqww_work_via_poem' else None}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--output',default=str(OUT)); a=ap.parse_args(); out=Path(a.output); out.mkdir(parents=True,exist_ok=True); run={'schema_version':'work-centrality-v1','command':'python3 python/compute_work_centrality.py','limitations':['Metrics describe MQWW documentary position, not historical influence.','work_via_poem omits 3,999 poems without author links.'],'layers':{}}
 for layer in ('mqww_work_direct','mqww_work_via_poem'):
  t=time.time(); rows,proj,stats=run_layer(layer); cols=list(rows[0]);
  with (out/(layer+'.csv')).open('w',encoding='utf-8',newline='') as f: w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(rows)
  pcols=list(proj[0]) if proj else ['node_id'];
  with (out/(layer+'_person_projection.csv')).open('w',encoding='utf-8',newline='') as f: w=csv.DictWriter(f,fieldnames=pcols); w.writeheader(); w.writerows(proj)
  for metric in ('degree','binary_strength','betweenness'):
   top=sorted(rows,key=lambda r:(-float(r[metric]),r['node_id']))[:20]; (out/(layer+'_'+metric+'_top20.json')).write_text(json.dumps(top,ensure_ascii=False,indent=2),encoding='utf-8')
  stats['seconds']=round(time.time()-t,2); run['layers'][layer]=stats
 (out/'manifest.json').write_text(json.dumps(run,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__': main()
