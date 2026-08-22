import sqlite3
import unittest
import tempfile
from pathlib import Path
from network_normalized import export

class NormalizedNetworkTest(unittest.TestCase):
    def test_fixture_mirror_and_self_loop(self):
        with tempfile.TemporaryDirectory() as d:
            tmp_path=Path(d)
            c=sqlite3.connect(':memory:'); c.executescript('''create table KINSHIP_CODES(c_kincode int,c_kin_pair1 int,c_kin_pair2 int,c_upstep int,c_dwnstep int,c_marstep int,c_kinrel_chn text); create table KIN_DATA(c_personid int,c_kin_id int,c_kin_code int,c_source int,c_pages text,c_notes text); create table ASSOC_CODES(c_assoc_code int,c_assoc_pair int,c_assoc_pair2 int,c_assoc_desc_chn text,c_assoc_role_type text); create table ASSOC_CODE_TYPE_REL(c_assoc_code int,c_assoc_type_id text); create table ASSOC_DATA(c_personid int,c_assoc_id int,c_assoc_code int,c_source int,c_text_title text,c_assoc_year int,c_sequence int);''')
            c.executemany('insert into KINSHIP_CODES values(?,?,?,?,?,?,?)',[(75,180,176,1,0,0,'F'),(180,75,111,0,1,0,'S')])
            c.executemany('insert into KIN_DATA values(?,?,?,?,?,?)',[(1,2,75,4,'',''),(2,1,180,4,'',''),(3,3,75,4,'','')])
            c.executemany('insert into ASSOC_CODES values(?,?,?,?,?)',[(437,438,437,'gift','A'),(438,437,438,'gift','P'),(9,9,9,'friend','M')])
            c.executemany('insert into ASSOC_DATA values(?,?,?,?,?,?,?)',[(1,2,437,4,'x',1,0),(2,1,438,4,'x',1,0),(1,2,9,4,'y',1,0),(1,2,438,4,'z',2,1),(1,2,437,5,'w',3,2)])
            export(c,tmp_path)
            import csv
            with open(tmp_path/'kin_typed_undirected.csv',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),1); self.assertEqual(rows[0]['recorded_codes'],'180;75')
            with open(tmp_path/'reject_kin.csv',encoding='utf-8-sig') as f: rejected=list(csv.DictReader(f))
            self.assertEqual(len(rejected),1)
            with open(tmp_path/'assoc_typed_undirected.csv',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),2)
            self.assertEqual(sum(int(r['n_raw_rows']) for r in rows if r['canonical_code']=='437'),4)
            with open(tmp_path/'assoc_typed_directed.csv',encoding='utf-8-sig') as f: directed=list(csv.DictReader(f))
            self.assertEqual(len([r for r in directed if r['canonical_code']=='437']),2)
            c.close()

if __name__ == '__main__': unittest.main()
