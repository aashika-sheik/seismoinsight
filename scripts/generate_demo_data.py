import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import random
from datetime import datetime, timedelta, timezone
import pandas as pd
from src.processor import process_dataframe, save_processed
from config import CSV_PATH

places = [
    "Near Japan, Japan", "Near Chile, Chile", "Near Indonesia, Indonesia",
    "Near Alaska, United States", "Near Mexico, Mexico",
    "Near New Zealand, New Zealand", "Near Philippines, Philippines",
    "Near Turkey, Turkey", "Near Tonga, Tonga"
]

rows=[]
start=datetime.now(timezone.utc)-timedelta(days=365*5)

for i in range(5000):
    t=start+timedelta(days=random.randint(0,1825),hours=random.randint(0,23))
    mag=max(1.5,random.gauss(4.4,1.0))
    rows.append({
        "id":f"demo-{i:06d}",
        "time":int(t.timestamp()*1000),
        "updated":int((t+timedelta(minutes=random.randint(1,1000))).timestamp()*1000),
        "latitude":random.uniform(-55,55),
        "longitude":random.uniform(-180,180),
        "depth_km":max(0,random.gauss(80,100)),
        "mag":min(mag,8.5),
        "magType":random.choice(["mb","ml","mww"]),
        "place":random.choice(places),
        "status":random.choice(["reviewed","automatic"]),
        "tsunami":1 if mag>=6.8 and random.random()<.25 else 0,
        "sig":int(max(0,mag*100+random.gauss(0,30))),
        "net":random.choice(["us","ci","ak","nc","nn"]),
        "nst":random.randint(5,150),
        "dmin":random.random()*2,
        "rms":random.random()*2,
        "gap":random.random()*250,
        "magError":random.random()*.4,
        "depthError":random.random()*5,
        "magNst":random.randint(5,100),
        "locationSource":random.choice(["us","ci","ak"]),
        "magSource":random.choice(["us","mb","mww"]),
        "types":"origin,phase-data",
        "ids":f",demo-{i:06d},",
        "sources":",us,",
        "type":"earthquake",
    })

df=process_dataframe(pd.DataFrame(rows))
save_processed(df,CSV_PATH)
print(f"Demo dataset saved to {CSV_PATH}")
