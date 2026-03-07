import traci
import time

CONFIG = "traffic_multi.sumocfg"

MIN_GREEN = 12
MAX_GREEN = 70
YELLOW_TIME = 3
DELAY = 0.03
SIM_END = 700

def get_logic(tls_id):
    return traci.trafficlight.getCompleteRedYellowGreenDefinition(tls_id)[0]

def get_states(tls_id):
    return [p.state for p in get_logic(tls_id).phases]

def incoming_lanes_by_link_index(tls_id):
    links = traci.trafficlight.getControlledLinks(tls_id)
    inc_lanes = []
    for g in links:
        if not g:
            inc_lanes.append(None)
        else:
            inc_lanes.append(g[0][0])
    return inc_lanes

def lane_is_blocked(lane_id: str) -> bool:
    """
    Çıkış dolu mu? Lane'in sonundaki araç çok yavaşsa / kuyruk varsa blok kabul et.
    """
    # duraklayan araç sayısı
    halt = traci.lane.getLastStepHaltingNumber(lane_id)
    if halt >= 2:
        return True

    vehs = traci.lane.getLastStepVehicleIDs(lane_id)
    if not vehs:
        return False

    # lane sonundaki araç (kabaca)
    last = vehs[-1]
    sp = traci.vehicle.getSpeed(last)
    return sp < 0.5

def green_score_with_antiblock(state, tls_id, inc_lanes):
    """
    Skor = giriş kuyruğu (halting) - (çıkış bloke ise büyük ceza)
    """
    score = 0

    for i, ch in enumerate(state):
        if ch not in ("G", "g"):
            continue

        in_lane = inc_lanes[i] if i < len(inc_lanes) else None
        if not in_lane:
            continue

        q = traci.lane.getLastStepHaltingNumber(in_lane)

        # Bu incoming lane'in olası çıkış lane'lerine bak
        blocked = False
        for lnk in traci.lane.getLinks(in_lane):
            out_lane = lnk[0]
            if lane_is_blocked(out_lane):
                blocked = True
                break

        if blocked:
            score -= 30   # 🔥 anti-gridlock cezası
        else:
            score += q

    return score

def best_green_phase(tls_id, candidates):
    states = get_states(tls_id)
    inc = incoming_lanes_by_link_index(tls_id)

    best_i = candidates[0]
    best_s = -10**9
    for i in candidates:
        s = green_score_with_antiblock(states[i], tls_id, inc)
        if s > best_s:
            best_s = s
            best_i = i
    return best_i, best_s

def find_yellow_after(tls_id, from_phase):
    states = get_states(tls_id)
    n = len(states)
    for k in range(1, n + 1):
        j = (from_phase + k) % n
        if "y" in states[j] or "Y" in states[j]:
            return j
    return (from_phase + 1) % n

def set_phase_both(tlsA, tlsB, pA, pB):
    traci.trafficlight.setPhase(tlsA, pA)
    traci.trafficlight.setPhase(tlsB, pB)

def any_ambulance_present():
    return "ambulance_1" in traci.vehicle.getIDList()

def main():
    traci.start(["sumo-gui", "-c", CONFIG, "--start"])

    tlsA, tlsB = "A", "B"

    statesA = get_states(tlsA)
    statesB = get_states(tlsB)

    # Yeşil içeren phase adayları
    candA = [i for i, st in enumerate(statesA) if ("G" in st or "g" in st)]
    candB = [i for i, st in enumerate(statesB) if ("G" in st or "g" in st)]

    print("A candidates:", candA, "totalPhases=", len(statesA))
    print("B candidates:", candB, "totalPhases=", len(statesB))

    # Başlangıç
    pA, sA = best_green_phase(tlsA, candA)
    pB, sB = best_green_phase(tlsB, candB)
    set_phase_both(tlsA, tlsB, pA, pB)
    print("START A=", pA, "score=", sA, "| B=", pB, "score=", sB)

    green_timer = 0

    for t in range(SIM_END):
        traci.simulationStep()
        time.sleep(DELAY)

        # 🚑 Ambulans varsa: en yüksek skorlu phase'i bas (anti-gridlock korumalı)
        if any_ambulance_present():
            pA, _ = best_green_phase(tlsA, candA)
            pB, _ = best_green_phase(tlsB, candB)
            set_phase_both(tlsA, tlsB, pA, pB)
            continue

        green_timer += 1
        if green_timer < MIN_GREEN:
            continue

        # periyodik veya max dolunca yeniden seçim
        if (t % MIN_GREEN == 0) or (green_timer >= MAX_GREEN):
            newA, scA = best_green_phase(tlsA, candA)
            newB, scB = best_green_phase(tlsB, candB)

            curA = traci.trafficlight.getPhase(tlsA)
            curB = traci.trafficlight.getPhase(tlsB)

            # Değişim varsa yellow geç
            if newA != curA:
                yA = find_yellow_after(tlsA, curA)
            else:
                yA = curA

            if newB != curB:
                yB = find_yellow_after(tlsB, curB)
            else:
                yB = curB

            set_phase_both(tlsA, tlsB, yA, yB)
            for _ in range(YELLOW_TIME):
                traci.simulationStep()
                time.sleep(DELAY)

            set_phase_both(tlsA, tlsB, newA, newB)
            green_timer = 0

            if t % 30 == 0:
                print(f"t={t} switch -> A:{newA}(score={scA}) B:{newB}(score={scB})")

    traci.close()
    print("Bitti ✅")

if __name__ == "__main__":
    main()
