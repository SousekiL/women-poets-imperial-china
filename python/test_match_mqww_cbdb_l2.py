import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path
from match_mqww_cbdb_l2 import load_alias_index, load_people, match_l2, split_aliases

class TestL2(unittest.TestCase):
    def test_split(self):
        self.assertEqual(split_aliases('甲,乙，丙;丁'), ['甲','乙','丙','丁'])
    def test_alias_match_and_status(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'x.db'; c=sqlite3.connect(db)
            c.execute('create table ALTNAME_DATA (c_personid integer,c_alt_name_chn text)')
            c.execute('create table CBDB_NAME_LIST (c_personid integer,name text)')
            c.execute('create table BIOG_MAIN (c_personid integer,c_name_chn text,c_female integer,c_fl_earliest_year integer,c_fl_latest_year integer)')
            c.executemany('insert into ALTNAME_DATA values (?,?)',[(1,'清照')]); c.execute("insert into BIOG_MAIN values (1,'李清照',1,1080,1160)"); c.commit()
            ro=sqlite3.connect(f'file:{db}?mode=ro',uri=True); ro.execute('pragma query_only=on')
            idx=load_alias_index(ro,{'清照'}); people=load_people(ro,{'1'}); ro.close()
            rows=match_l2([{'poetID':'p1','NameHZ':'查无','ZiHZ':'清照','HaoHZ':'','OtherZiHaoHZ':''}],{'p1':{'level':'D'}},idx,people)
            self.assertEqual(rows[0]['status'],'review_unique_female'); self.assertEqual(rows[0]['candidate_personids'],'1')

if __name__ == '__main__': unittest.main()
