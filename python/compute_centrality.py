#!/usr/bin/env python3
"""Reproducible centrality summaries for typed CBDB networks."""
import argparse,csv,hashlib,json,random,time
from pathlib import Path
import networkx as nx
ROOT=Path(__file__).resolve().parents[1]; NET=ROOT/'data/derived/network'; OUT=ROOT/'data/derived/centrality'
VERSIONS=['kin_typed_directed','kin_typed_undirected','assoc_typed_directed','assoc_typed_undirected']
COLS=['node_id','typed_degree','relation_class_strength','degree','in_degree','out_degree','betweenness','harmonic_closeness','pagerank','k_core','component_id','input_manifest_sha256','network_version']
def read_graph(path,directed):
 G=nx.MultiDiGraph() if directed else nx.MultiGraph()
 with path.open(encoding='utf-8-sig',newline='') as f:
  for r in csv.DictReader(f):
   a,b=str(r['source_id']),str(r['target_id']); c=r.get('relation_class','')
   if a and b and a!=b:G.add_edge(a,b,key=c,relation_class=c)
 return G
def run_one(version,seed=20260822,sample=128):
 directed=version.endswith('_directed'); G=read_graph(NET/(version+'.csv'),directed)
 P=nx.DiGraph() if directed else nx.Graph(); P.add_edges_from((a,b) for a,b in G.edges())
 n=len(P); k=min(sample,max(1,n)); rng=random.Random(seed); sources=rng.sample(sorted(P),k)
 btw=nx.betweenness_centrality(P,k=k,normalized=True,seed=seed); hc={u:0. for u in P}
 for s in sources:
  for u,d in nx.single_source_shortest_path_length(P,s).items():
   if d: hc[u]+=1/d
 for u in hc:hc[u]/=k
 pr=nx.pagerank(P,alpha=.85,tol=1e-8,max_iter=200); core=nx.core_number(P) if not directed else {u:'not_applicable' for u in P}
 comps=(nx.weakly_connected_components(P) if directed else nx.connected_components(P)); comp={u:i for i,c in enumerate(comps) for u in c}
 rows=[]
 for u in sorted(P):
  rows.append({'node_id':u,'typed_degree':G.degree(u),'relation_class_strength':G.degree(u),'degree':P.degree(u),'in_degree':G.in_degree(u) if directed else '','out_degree':G.out_degree(u) if directed else '','betweenness':btw[u],'harmonic_closeness':hc[u],'pagerank':pr[u],'k_core':core[u],'component_id':comp[u],'network_version':version})
 return rows,{'nodes':n,'projected_edges':P.number_of_edges(),'typed_edges':G.number_of_edges(),'directed':directed, 'k_core_coverage':None if directed else 1.0, 'k_core':'not_applicable_for_directed' if directed else 'computed','betweenness':{'method':'Brandes endpoint projection sample','sample_size':k,'seed':seed,'normalized':True},'harmonic_closeness':{'method':'uniform seeded source sample','sample_size':k,'seed':seed},'path_projection':'endpoint simple Graph; typed parallel classes retained only in typed_degree/relation_class_strength','components':len(set(comp.values()))}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--sample',type=int,default=128);ap.add_argument('--seed',type=int,default=20260822);a=ap.parse_args();OUT.mkdir(parents=True,exist_ok=True); m=NET/'manifest.json';mh=hashlib.sha256(m.read_bytes()).hexdigest();run={'schema_version':'centrality-v2','input_manifest_sha256':mh,'versions':{},'command':'python3 python/compute_centrality.py'}; tops={}
 for v in VERSIONS:
  t=time.time();rows,s=run_one(v,a.seed,a.sample)
  for r in rows:r['input_manifest_sha256']=mh
  with (OUT/(v+'.csv')).open('w',encoding='utf-8',newline='') as f: w=csv.DictWriter(f,fieldnames=COLS);w.writeheader();w.writerows(rows)
  metrics=['typed_degree','betweenness','harmonic_closeness','pagerank']+([] if s['directed'] else ['k_core']);top={metric:sorted(rows,key=lambda r:(-float(r[metric] or 0),r['node_id']))[:20] for metric in metrics};tops[v]={k:[x['node_id'] for x in z] for k,z in top.items()};(OUT/(v+'_top20.json')).write_text(json.dumps(top,indent=2),encoding='utf8');s['seconds']=round(time.time()-t,2);run['versions'][v]=s
 run['top20_intersections']={a+'∩'+b:{m:len(set(tops[a].get(m,[]))&set(tops[b].get(m,[]))) for m in set(tops[a])&set(tops[b])} for i,a in enumerate(VERSIONS) for b in VERSIONS[i+1:]};(OUT/'centrality_manifest.json').write_text(json.dumps(run,indent=2),encoding='utf8')
if __name__=='__main__':main()
