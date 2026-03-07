import traci
import time

CONFIG = "traffic.sumocfg"

NS_EDGES = ["N2C", "S2C"]
EW_EDGES = ["E2C", "W2C"]

def edge_vehicle_count(edges):
    return sum(traci.edge.getLastStepVehicleNumber(e) for e in edges)

def main():
    traci.start(["sumo-gui", "-c", CONFIG, "--start"])
    tls_id = traci.trafficlight.getIDList()[0]

    sim_end = 200
    decision_every = 10
    threshold = 2
    emergency_mode = False

    for t in range(sim_end):
        traci.simulationStep()
        time.sleep(0.2)   # simülasyonu yavaşlat

        veh_ids = traci.vehicle.getIDList()

        # 🚑 Ambulans var mı?
        ambulance_here = "ambulance_1" in veh_ids

        if ambulance_here:
            # Ambulansı kırmızı boya (garanti)
            traci.vehicle.setColor("ambulance_1", (255, 0, 0, 255))

            # Işığı anında YEŞİL yap (NS yönü)
            traci.trafficlight.setPhase(tls_id, 0)

            if not emergency_mode:
                print("🚑 AMBULANS ALGILANDI → YEŞİL IŞIK")
                emergency_mode = True

            continue

        # Ambulans geçtiyse normale dön
        if emergency_mode and not ambulance_here:
            print("✅ AmbulANS GEÇTİ → NORMAL MOD")
            emergency_mode = False

        # 🧠 YOĞUNLUK TABANLI AI KARAR
        if t % decision_every == 0:
            ns_count = edge_vehicle_count(NS_EDGES)
            ew_count = edge_vehicle_count(EW_EDGES)

            if ns_count > ew_count + threshold:
                traci.trafficlight.setPhase(tls_id, 0)  # NS GREEN
                print("🟢 NS GREEN")
            elif ew_count > ns_count + threshold:
                traci.trafficlight.setPhase(tls_id, 2)  # EW GREEN
                print("🟢 EW GREEN")

    traci.close()

if __name__ == "__main__":
    main()
