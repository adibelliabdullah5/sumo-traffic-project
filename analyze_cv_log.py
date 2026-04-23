import os
import pandas as pd
import matplotlib.pyplot as plt

INPUT_FILE = "cv_log.csv"
OUTPUT_DIR = "cv_log_analysis"


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Hata: {INPUT_FILE} bulunamadý. Önce run_cv_sim.py çalýþtýrýn.")
        return

    df = pd.read_csv(INPUT_FILE)
    print("=== CV LOG ANALIZI ===")
    print(f"Toplam satýr: {len(df)}")
    print(f"Ortalama NS trafik adedi: {df['ns_count'].mean():.2f}")
    print(f"Ortalama EW trafik adedi: {df['ew_count'].mean():.2f}")
    print(f"Acil durum sayýsý: {df['emergency'].sum()}")
    print("Decision sayýmlarý:")
    print(df['decision'].value_counts().to_string())

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    plt.figure(figsize=(10, 5))
    plt.plot(df['time'], df['ns_count'], label='NS Count', marker='o', markersize=4)
    plt.plot(df['time'], df['ew_count'], label='EW Count', marker='o', markersize=4)
    plt.title('CV Log Traffic Counts')
    plt.xlabel('Time')
    plt.ylabel('Vehicle count')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'traffic_counts.png'))
    plt.close()

    plt.figure(figsize=(8, 4))
    df['decision'].value_counts().plot(kind='bar')
    plt.title('Decision Daðýlýmý')
    plt.xlabel('Decision')
    plt.ylabel('Count')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'decision_counts.png'))
    plt.close()

    print(f"Analiz çýktý dosyalarý kaydedildi: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
