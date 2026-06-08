import pandas as pd

df = pd.read_excel('VehiclesData (1).xlsx')
df = df.fillna('')
queries = []
for _, row in df.iterrows():
    van_id = str(row['vehicleName']).replace("'", "''")
    vin = str(row['vin']).replace("'", "''")
    make = str(row['make']).replace("'", "''")
    
    if not van_id: continue
    
    queries.append(f"('{van_id}', '{vin}', '{make}')")

sql = "INSERT INTO vehicles (van_id, vin, make_model) VALUES\n" + ",\n".join(queries) + "\nON CONFLICT (van_id) DO NOTHING;"

with open('seed.sql', 'w') as f:
    f.write(sql)
