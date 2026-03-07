import pandas as pd

data = {
    "Scenario": ["Fixed", "Smart", "Emergency"],
    "Avg_Wait_s": [7.37, 4.13, 3.20],
    "Total_Wait_s": [75709, 35960, 21000],
    "Avg_Speed_mps": [4.27, 5.22, 6.10],
    "Stops": [2921, 1601, 900]
}

df = pd.DataFrame(data)

df.to_csv("simulation_results.csv", index=False)

print("CSV kaydedildi ✅")
