"""Full-fidelity CBDB multiplex network export."""
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path
import os

KIN_COLS = ["raw_id","recorded_ego","recorded_alter","recorded_code","recorded_source","recorded_pages","recorded_notes","kin_class","is_self_loop","is_sentinel"]
ASSOC_COLS = ["raw_id","recorded_ego","recorded_alter","recorded_code","canonical_code","role_type","canonical_type_rel","recorded_source","text_title","year","sequence","is_self_loop","is_sentinel"]
NORM_COLS = ["edge_id","source_id","target_id","relation_class","canonical_code","raw_ids","n_raw_rows","recorded_codes","merge_rule","direction_status","source_ids","year_values","year_precision","unknown_source","match_level","derivation_rule"]
def kin_class(code, kin):
    """Canonicalize only mutually declared reciprocal codes; preserve variants."""
    if code == 0:
        return "unknown"
    meta = kin.get(code)
    if not meta:
        return str(code)
    candidates = [int(x) for x in meta[1:3] if x is not None and int(x) >= 0 and int(x) != code]
    mutual = [c for c in candidates if c in kin and code in {kin[c][1], kin[c][2]}]
    return str(min([code] + mutual[:1])) if mutual else str(code)



def _csv(path, rows, cols):
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(rows)

def _hash(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def export(conn, out: Path, a_ids=None, codebook_paths=()):
    out.mkdir(parents=True,exist_ok=True)
    kin={int(r[0]):r for r in conn.execute("SELECT c_kincode,c_kin_pair1,c_kin_pair2,c_upstep,c_dwnstep,c_marstep,c_kinrel_chn FROM KINSHIP_CODES")}
    assoc={int(r[0]):r for r in conn.execute("SELECT c_assoc_code,c_assoc_pair,c_assoc_desc_chn,c_assoc_role_type FROM ASSOC_CODES")}
    typ={int(r[0]):str(r[1]) for r in conn.execute("SELECT c_assoc_code,GROUP_CONCAT(c_assoc_type_id) FROM ASSOC_CODE_TYPE_REL GROUP BY c_assoc_code")}
    # Canonical A code and inherited type for untyped P codes (e.g. 633 -> 632).
    def acode(c):
        role=assoc.get(c,(None,None,None,""))[3] or ""
        return int(assoc[c][1]) if role=="P" and assoc[c][1] is not None else c
    def atype(c):
        cc=acode(c); return typ.get(cc,"unknown")
    manifest={"schema_version":"normalized-network-v2","command":"python3 python/build_network_derived.py","database":"cbdb202409.db","rules":"multiplex-typed-v2","versions":{},"limitations":["KIN semantic direction follows step metadata; unresolved codes retain recorded status.","A-only filtering is a separate view; raw tables are full database exports.","Address sequence is not selected by this export."]}
    for kind in ("kin","assoc"):
        raw=[]; reject=[]
        if kind=="kin":
            q="SELECT c_personid,c_kin_id,c_kin_code,c_source,c_pages,c_notes FROM KIN_DATA"
            for i,(ego,alter,code,source,pages,notes) in enumerate(conn.execute(q)):
                ego,alter,code=int(ego),int(alter),int(code); loop=ego==alter; sent=code==-10000
                rid=f"kin:{i}:{ego}:{alter}:{code}"
                r={"raw_id":rid,"recorded_ego":ego,"recorded_alter":alter,"recorded_code":code,"recorded_source":source or "","recorded_pages":pages or "","recorded_notes":notes or "","kin_class":"unknown" if code==0 else str(code),"is_self_loop":int(loop),"is_sentinel":int(sent)}
                (reject if loop or sent else raw).append(r)
            _csv(out/"raw_kin.csv",raw + reject,KIN_COLS); _csv(out/"reject_kin.csv",reject,KIN_COLS)
            groups={}
            for r in raw:
                code=r["recorded_code"]; pair=kin.get(code,(None,None,None,None,None,None,None));
                # Reciprocal mirror codes (F/S, H/W) share one class; retain distinct
                # variants such as S1 by anchoring only this code's declared pair.
                cl = kin_class(code, kin)
                r["kin_class"] = "unknown" if code==0 else cl
                key=(min(r["recorded_ego"],r["recorded_alter"]),max(r["recorded_ego"],r["recorded_alter"]),r["kin_class"])
                groups.setdefault(key,[]).append(r)
            def norm(key,rs,n):
                a,b,cl=key; codes=sorted({str(x["recorded_code"]) for x in rs});
                return {"edge_id":f"kin_{n}","source_id":a,"target_id":b,"relation_class":cl,"canonical_code":cl,"raw_ids":";".join(x["raw_id"] for x in rs),"n_raw_rows":len(rs),"recorded_codes":";".join(codes),"merge_rule":"undirected_pair+canonical_reciprocal_class","direction_status":"kin_recorded","source_ids":";".join(sorted({str(x["recorded_source"]) for x in rs if x["recorded_source"]})),"year_values":"","year_precision":"none","unknown_source":int(any(not x["recorded_source"] for x in rs)),"match_level":"A-only" if a_ids and any(x["recorded_ego"] in a_ids for x in rs) else "full","derivation_rule":"mirror_collapsed"}
            typed=list(norm(k,v,i) for i,(k,v) in enumerate(groups.items()))
        else:
            q="SELECT c_personid,c_assoc_id,c_assoc_code,c_source,c_text_title,c_assoc_year,c_sequence FROM ASSOC_DATA"
            for i,(ego,alter,code,source,title,year,seq) in enumerate(conn.execute(q)):
                ego,alter,code=int(ego),int(alter),int(code); loop=ego==alter; sent=code==0; cc=acode(code) if code in assoc else code
                r={"raw_id":f"assoc:{i}:{ego}:{alter}:{code}:{source or ''}:{title or ''}:{year or ''}:{seq or ''}","recorded_ego":ego,"recorded_alter":alter,"recorded_code":code,"canonical_code":cc,"role_type":assoc.get(code,(None,None,None,""))[3] or "unknown","canonical_type_rel":atype(code),"recorded_source":source or "","text_title":title or "","year":year or "","sequence":seq or "","is_self_loop":int(loop),"is_sentinel":int(sent)}
                (reject if loop or sent else raw).append(r)
            _csv(out/"raw_assoc.csv",raw + reject,ASSOC_COLS); _csv(out/"reject_assoc.csv",reject,ASSOC_COLS)
            groups={}
            for r in raw:
                role=r["role_type"]; a,b=r["recorded_ego"],r["recorded_alter"]; cc=r["canonical_code"]
                if role=="P": a,b=b,a
                if role=="M": a,b=min(a,b),max(a,b)
                key=(a,b,cc,"undirected" if role=="M" else "directed")
                groups.setdefault(key,[]).append(r)
            typed=[]
            for i,(key,rs) in enumerate(groups.items()):
                a,b,cc,status=key; typed.append({"edge_id":f"assoc_{i}","source_id":a,"target_id":b,"relation_class":str(cc),"canonical_code":cc,"raw_ids":";".join(x["raw_id"] for x in rs),"n_raw_rows":len(rs),"recorded_codes":";".join(sorted({str(x["recorded_code"]) for x in rs})),"merge_rule":"pair+canonical_code+direction","direction_status":"mutual" if status=="undirected" else "directed_from_A_or_P","source_ids":";".join(sorted({str(x["recorded_source"]) for x in rs if x["recorded_source"]})),"year_values":";".join(sorted({str(x["year"]) for x in rs if x["year"]})),"year_precision":"exact" if any(x["year"] not in ("",0,"0",-1,"-1") for x in rs) else "unknown","unknown_source":int(any(not x["recorded_source"] for x in rs)),"match_level":"A-only" if a_ids and any(x["recorded_ego"] in a_ids or x["recorded_alter"] in a_ids for x in rs) else "full","derivation_rule":"canonical_A_P_merge"})
        # Directed preserves semantic endpoint; undirected always folds endpoint reversals by pair/class.
        und_groups={}
        for x in typed:
            key=(min(x["source_id"],x["target_id"]),max(x["source_id"],x["target_id"]),x["relation_class"])
            und_groups.setdefault(key,[]).append(x)
        undirected=[]
        for i,(key,members) in enumerate(und_groups.items()):
            x=dict(members[0]); x.update({"edge_id":f"{kind}_undirected_{i}","source_id":key[0],"target_id":key[1],"raw_ids":";".join(sorted({rid for m in members for rid in m["raw_ids"].split(';') if rid})),"n_raw_rows":sum(int(m["n_raw_rows"]) for m in members),"recorded_codes":";".join(sorted({c for m in members for c in m["recorded_codes"].split(';') if c})),"source_ids":";".join(sorted({s for m in members for s in m["source_ids"].split(';') if s})),"year_values":";".join(sorted({y for m in members for y in m["year_values"].split(';') if y})),"merge_rule":"undirected_pair+canonical_relation_class","direction_status":"mutual"})
            undirected.append(x)
        directed_rows=[x for x in typed if x["direction_status"]!="mutual"]
        _csv(out/f"{kind}_typed_directed.csv",directed_rows,NORM_COLS)
        _csv(out/f"{kind}_typed_undirected.csv",undirected,NORM_COLS)
        simple={}
        for x in undirected: simple.setdefault((min(x["source_id"],x["target_id"]),max(x["source_id"],x["target_id"])),x)
        _csv(out/f"{kind}_simple_undirected.csv",list(simple.values()),NORM_COLS)
        manifest["versions"][kind]={"raw":len(raw)+len(reject),"analysis_eligible":len(raw),"reject":len(reject),"typed_directed":len(directed_rows),"typed_undirected":len(undirected),"simple_undirected":len(simple),"unknown":sum(x.get("kin_class")=="unknown" or x.get("canonical_type_rel")=="unknown" for x in raw)}
    manifest["input_hashes"]={"database_size":conn.execute("SELECT page_count*page_size FROM pragma_page_count(),pragma_page_size()").fetchone()[0],"database_mtime_ns":os.stat("/Users/sousekilyu/Documents/Data/biography_literature_CBDB_china_historical/cbdb202409.db").st_mtime_ns}
    def count_rows(p):
        with p.open(encoding="utf-8-sig", newline="") as f: return sum(1 for _ in csv.reader(f))-1
    manifest["output_files"]={p.name:{"rows":count_rows(p),"sha256":_hash(p)} for p in out.glob("*.csv")}
    manifest["codebook_hashes"]={str(p):_hash(Path(p)) for p in codebook_paths if Path(p).exists()}
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    return manifest
