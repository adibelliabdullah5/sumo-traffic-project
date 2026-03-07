import traci
import time
import csv

CONFIG = "traffic.sumocfg"

# "Kameranın gördüğü bölgeler" gibi düşün: kavşağa gelen kenarlar
NS_EDGES = ["N2C", "S2C"]
EW_EDGES = ["E2C", "W2C"]

def edge_vehicle_count(edges):
    return sum(traci.edge.getLastStepVehicleNumber(e) for e in edges)

def detect_emergency_vehicle():
    # Görüntü işlemeyle "ambulans tespiti" gibi düşün
    return "ambulance_1" in traci.vehicle.getIDList()

def main():
    traci.start(["sumo-gui", "-c", CONFIG, "--start"])
    tls_id = traci.trafficlight.getIDList()[0]

    sim_end = 200
    decision_every = 5     # daha sık karar (kameradan sık veri geliyor gibi)
    threshold = 2

    # CSV log (tez için süper)
    with open("cv_log.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "ns_count", "ew_count", "emergency", "decision"])

        emergency_mode = False

        for t in range(sim_end):
            traci.simulationStep()
            time.sleep(0.15)  # yavaşlat

            # ✅ "Computer Vision output" (kamera çıktı verisi)
            ns = edge_vehicle_count(NS_EDGES)
            ew = edge_vehicle_count(EW_EDGES)
            emergency = detect_emergency_vehicle()

            decision = "NONE"

            # 🚑 Emergency priority
            if emergency:
                traci.trafficlight.setPhase(tls_id, 0)  # NS green
                decision = "EMERGENCY_NS_GREEN"
                emergency_mode = True

                # görünür olsun diye kırmızı boya
                if "ambulance_1" in traci.vehicle.getIDList():
                    traci.vehicle.setColor("ambulance_1", (255, 0, 0, 255))

            else:
                # Ambulans geçtiyse normale dön
                if emergency_mode:
                    emergency_mode = False

                # 🧠 AI decision using CV counts
                if t % decision_every == 0:
                    if ns > ew + threshold:
                        traci.trafficlight.setPhase(tls_id, 0)
                        decision = "NS_GREEN"
                    elif ew > ns + threshold:
                        traci.trafficlight.setPhase(tls_id, 2)
                        decision = "EW_GREEN"
                    else:
                        decision = "KEEP"

            # logla
            writer.writerow([t, ns, ew, int(emergency), decision])

            # ekranda da gör
            if t % 10 == 0:
                print(f"t={t}  CV(ns={ns}, ew={ew}, emergency={emergency})  -> {decision}")

    traci.close()
    print("Bitti ✅  cv_log.csv oluştu")

if __name__ == "__main__":
    main()
