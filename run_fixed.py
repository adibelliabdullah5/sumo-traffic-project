import traci

CONFIG = "traffic.sumocfg"

def main():
    traci.start(["sumo", "-c", CONFIG])  # GUI yerine hızlı (tez ölçümü için daha iyi)

    tls_id = traci.trafficlight.getIDList()[0]
    sim_end = 500

    total_wait = 0.0
    total_speed = 0.0
    total_stops = 0
    total_veh_samples = 0

    for t in range(sim_end):
        # sabit döngü
        cycle = t % 70
        logic = traci.trafficlight.getAllProgramLogics(tls_id)[0]
        phase_count = len(logic.phases)

        if phase_count >= 4:
            if cycle < 30:
                traci.trafficlight.setPhase(tls_id, 0)
            elif cycle < 35:
                traci.trafficlight.setPhase(tls_id, 1)
            elif cycle < 65:
                traci.trafficlight.setPhase(tls_id, 2)
            else:
                traci.trafficlight.setPhase(tls_id, 3)

        traci.simulationStep()

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

    print("\n=== BASELINE (FIXED) RESULTS ===")
    print(f"sim_end={sim_end}")
    print(f"samples={total_veh_samples}")
    print(f"avg_wait={avg_wait:.2f} s")
    print(f"total_wait={total_wait:.2f} s")
    print(f"avg_speed={avg_speed:.2f} m/s")
    print(f"stop_samples={total_stops}")

if __name__ == "__main__":
    main()
