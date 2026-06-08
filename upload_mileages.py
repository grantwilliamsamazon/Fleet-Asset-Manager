from backend import get_supabase

data_string = """
1	4691
2	15863
3	14662
4	15537
5	7808
6	15279
7	15775
8	13872
9	16200
10	15246
11	14997
12	14924
13	4294
14	14985
15	14629
16	15402
17	14478
18	12133
19	12429
20	11203
21	9966
22	12095
23	12989
24	15566
25	11545
27	7901
28	6642
29	38531
30	42784
31	74202
35	65250
36	52491
37	54015
38	40518
39	4070
40	3733
41	3846
42	3448
43	3492
44	65991
"""

def map_van_id(num_str):
    num = int(num_str)
    # Based on the earlier query:
    if num <= 17 or 22 <= num <= 26 or num == 1:
        return f"Van {num:02d} Promaster(Hertz)"
    elif 18 <= num <= 21 or num == 27 or num == 28:
        return f"Van {num:02d} Promaster(Enterprise)"
    elif 29 <= num <= 43:
        return f"Van {num:02d}"
    elif num == 44:
        return "Van 44"
    return f"Van {num:02d}"

supabase = get_supabase()

lines = data_string.strip().split('\n')
for line in lines:
    parts = line.split()
    if len(parts) == 2:
        van_num = parts[0]
        mileage = int(parts[1])
        
        target_van_id = map_van_id(van_num)
        
        # update DB
        try:
            res = supabase.table("vehicles").update({
                "last_mileage": mileage,
                "last_oil_change_mileage": mileage,
                "last_tire_rotation_mileage": mileage
            }).eq("van_id", target_van_id).execute()
            print(f"Updated {target_van_id} to {mileage}")
        except Exception as e:
            print(f"Failed to update {target_van_id}: {e}")

print("Upload complete.")
