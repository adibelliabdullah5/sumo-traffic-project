import traci
import time

CONFIG = "traffic_multi.sumocfg"

def set_fixed_phases(tls_id, cyc):
    """
    Basit cycle:
      0-30  : phase 0 (main green)
      30-35 : phase 1 (yellow)
      35-65 : phase 2 (side green)
      65-70 : phase 3 (yellow)
    Not: Bu phase indexleri SUMO'nun varsayılan TL logic'ine göre çalışır.
    """
    if cyc < 30:
        traci.trafficlight.setPhase(tls_id, 0)
    elif cyc < 35:
        traci.trafficlight.setPhase(tls_id, 1)
    elif cyc < 65:
        traci.trafficlight.setPhase(tls_id, 2)
    else:
        traci.trafficlight.setPhase(tls_id, 3)

def main():
    traci.start(["sumo-gui", "-c", CONFIG, "--start"])

    tls_ids = list(traci.trafficlight.getIDList())
    print("TLS:", tls_ids)

    tlsA = "A"
    tlsB = "B"

    # === AUTO GREEN WAVE OFFSET ===
    # A (y=100) -> B (y=300) => 200m
    DIST = 200.0       # metre
    SPEED = 13.9       # m/s (edges_multi.edg.xml içinde speed="13.9")
    OFFSET = int(round(DIST / SPEED))  # ~14
    print("AUTO OFFSET =", OFFSET, "seconds")

    SIM_END = 400
    DELAY = 0.25   # görsel izlemek için yavaşlat
    CYCLE = 70

    for t in range(SIM_END):
        traci.simulationStep()
        time.sleep(DELAY)

        # A kavşağı fazı
        a_cycle = t % CYCLE
        # B kavşağı offsetli faz
        b_cycle = (t - OFFSET) % CYCLE

        # 🚑 Emergency override: Ambulans sahadaysa ana koridoru yeşile zorla
        veh_ids = traci.vehicle.getIDList()
        if "ambulance_1" in veh_ids:
            traci.vehicle.setColor("ambulance_1", (255, 0, 0, 255))
            traci.trafficlight.setPhase(tlsA, 0)  # main green
            traci.trafficlight.setPhase(tlsB, 0)  # main green
        else:
            set_fixed_phases(tlsA, a_cycle)
            set_fixed_phases(tlsB, b_cycle)

        if t % 20 == 0:
            print(f"t={t}  Acyc={a_cycle}  Bcyc={b_cycle}  OFFSET={OFFSET}")

    traci.close()
    print("Bitti ✅")

if __name__ == "__main__":
    main()
