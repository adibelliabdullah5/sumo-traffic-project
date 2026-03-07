import traci

CONFIG = "traffic.sumocfg"
NS_EDGES = ["N2C", "S2C"]
EW_EDGES = ["E2C", "W2C"]

def edge_vehicle_count(edges):
    return sum(traci.edge.getLastStepVehicleNumber(e) for e in edges)

def main():
    traci.start(["sumo", "-c", CONFIG])  # GUI yok: hızlı ölçüm

    tls_id = traci.trafficlight.getIDList()[0]
    sim_end = 500
    decision_every = 10
    threshold = 2

    total_wait = 0.0
    total_speed = 0.0
    total_stops = 0
    total_veh_samples = 0

    for t in range(sim_end):
        traci.simulationStep()

        # karar
        if t % decision_every == 0:
            ns = edge_vehicle_count(NS_EDGES)
            ew = edge_vehicle_count(EW_EDGES)

            if ns > ew + threshold:
                traci.trafficlight.setPhase(tls_id, 0)  # NS green
            elif ew > ns + threshold:
                traci.trafficlight.setPhase(tls_id, 2)  # EW green

        # METRİK TOPLA
        veh_ids = traci.vehicle.getIDList()
        for vid in veh_ids:
            total_wait += traci.vehicle.getAccumulatedWaitingTime(vid)
            total_speed += traci.vehicle.getSpeed(vid)
            if traci.vehicle.getSpeed(vid) < 0.1:
                total_stops += 1
            total_veh_samples += 1

    traci.close()

    avg_wait = total_wait / total_veh_samples if total_veh_samples else 0
    avg_speed = total_speed / total_veh_samples if total_veh_samples else 0

    print("\n=== SMART (DENSITY) RESULTS ===")
    print(f"sim_end={sim_end}")
    print(f"samples={total_veh_samples}")
    print(f"avg_wait={avg_wait:.2f} s")
    print(f"total_wait={total_wait:.2f} s")
    print(f"avg_speed={avg_speed:.2f} m/s")
    print(f"stop_samples={total_stops}")

if __name__ == "__main__":
    main()
