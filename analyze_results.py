import pandas as pd
import matplotlib.pyplot as plt

data = {
    "Scenario": ["Fixed", "Smart", "Emergency"],
    "Avg Wait (s)": [7.37, 4.13, 3.20],
    "Total Wait (s)": [75709, 35960, 21000],
    "Avg Speed (m/s)": [4.27, 5.22, 6.10],
    "Stops": [2921, 1601, 900]
}

df = pd.DataFrame(data)

# 1️⃣ Average Waiting Time
plt.figure()
plt.bar(df["Scenario"], df["Avg Wait (s)"])
plt.title("Average Waiting Time Comparison")
plt.ylabel("Seconds")
plt.savefig("avg_wait.png")

# 2️⃣ Average Speed
plt.figure()
plt.bar(df["Scenario"], df["Avg Speed (m/s)"])
plt.title("Average Speed Comparison")
plt.ylabel("m/s")
plt.savefig("avg_speed.png")

# 3️⃣ Stops
plt.figure()
plt.bar(df["Scenario"], df["Stops"])
plt.title("Vehicle Stops Comparison")
plt.ylabel("Stop Count")
plt.savefig("stops.png")

plt.show()
