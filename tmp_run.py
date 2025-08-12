import os, json
from fastapi.testclient import TestClient
from services.api.app.main import app
os.environ['APP_ENV']='ci'
with TestClient(app) as c:
    p='2025-06'
    c.post('/verifications', json={'org_id':1,'date':f'{p}-05','total_amount':112.0,'currency':'SEK','vat_code':'SE12','entries':[{'account':'6071','debit':100.0,'credit':0.0},{'account':'2641','debit':6.0,'credit':0.0},{'account':'1910','debit':0.0,'credit':112.0}]})
    c.post('/verifications', json={'org_id':1,'date':f'{p}-10','total_amount':125.0,'currency':'SEK','vat_code':'SE25','entries':[{'account':'5611','debit':100.0,'credit':0.0},{'account':'2641','debit':12.5,'credit':0.0},{'account':'1910','debit':0.0,'credit':125.0}]})
    r=c.get('/reports/vat/declaration', params={'period':p})
    print(r.status_code)
    print(json.dumps(r.json(), ensure_ascii=False, indent=2))
