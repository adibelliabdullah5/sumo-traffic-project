import traci
import time

CONFIG = "traffic_multi.sumocfg"

# Bizim kurduğumuz düzende:
# A kavşağı ana koridor = DİKEY (güneyden gelen A_S2A + B'den gelen B2A + kuzeyden gelen A_N2A)
A_MAIN_IN = {"A_S2A", "B2A", "A_N2A"}
A_SIDE_IN = {"A_E2A", "A_W2A"}

# B kavşağı ana koridor = DİKEY (A'dan gelen A2B + güneyden gelen B_S2B + kuzeyden gelen B_N2B)
B_MAIN_IN = {"A2B", "B_S2B", "B_N2B"}
B_SIDE_IN = {"B_E2B", "B_W2B"}

MIN_GREEN = 12
MAX_GREEN = 70
YELLOW_TIME = 3
DELAY = 0.03   # çok yüksek yapma, “donuk” gibi görünür
SIM_END = 700

def lane_to_edge(lane_id: str) -> str:
    # "A2B_0" -> "A2B"
    return lane_id.split("_")[0]

def get_phase_states(tls_id):
    logic = traci.trafficlight.getCompleteRedYellowGreenDefinition(tls_id)[0]
    return [p.state for p in logic.phases]

def get_incoming_edges_by_link_index(tls_id):
    """
    SUMO: controlledLinks -> her linkIndex için (incomingLane, outgoingLane, viaLane) listesi verir.
    state string uzunluğu = linkIndex sayısı.
    """
    links = traci.trafficlight.getControlledLinks(tls_id)
    incoming_edges = []
    for link_group in links:
        # link_group: list of tuples (inLane, outLane, viaLane)
        if not link_group:
            incoming_edges.append(None)
        else:
            in_lane = link_group[0][0]
            incoming_edges.append(lane_to_edge(in_lane))
    return incoming_edges

def score_phase_for_in_edges(state: str, incoming_edges, target_in_edges: set):
    """
    state string'te G/g olan linklerde incoming edge hedef set'teyse puan ver.
    """
    s = 0
    for i, ch in enumerate(state):
        if ch in ("G", "g"):
            e = incoming_edges[i] if i < len(incoming_edges) else None
            if e in target_in_edges:
                s += 1
    return s

def find_best_green_phase(tls_id, target_in_edges):
    states = get_phase_states(tls_id)
    incoming_edges = get_incoming_edges_by_link_index(tls_id)

    best_idx = 0
    best_score = -1
    for idx, st in enumerate(states):
        sc = score_phase_for_in_edges(st, incoming_edges, target_in_edges)
        if sc > best_score:
            best_score = sc
            best_idx = idx
    return best_idx

def find_yellow_after(tls_id, green_idx):
    """
    En pratik: green_idx'den sonraki phase'lerde 'y' içeren ilkini yellow kabul et.
    Bulamazsa green_idx+1 kullanır.
    """
    states = get_phase_states(tls_id)
    n = len(states)
    for k in range(1, n+1):
        j = (green_idx + k) % n
        if "y" in states[j] or "Y" in states[j]:
            return j
    return (green_idx + 1) % n

def halting_on_edges(edges):
    # Kuyruk = durmuş araç sayısı
    total = 0
    for e in edges:
        total += traci.edge.getLastStepHaltingNumber(e)
    return total

def set_phase_both(tlsA, tlsB, phaseA, phaseB):
    traci.trafficlight.setPhase(tlsA, phaseA)
    traci.trafficlight.setPhase(tlsB, phaseB)

def main():
    traci.start(["sumo-gui", "-c", CONFIG, "--start"])

    tlsA = "A"
    tlsB = "B"

    # ✅ Phase indexlerini OTOMATİK bul
    A_MAIN_GREEN = find_best_green_phase(tlsA, A_MAIN_IN)
    A_SIDE_GREEN = find_best_green_phase(tlsA, A_SIDE_IN)
    A_MAIN_YELLOW = find_yellow_after(tlsA, A_MAIN_GREEN)
    A_SIDE_YELLOW = find_yellow_after(tlsA, A_SIDE_GREEN)

    B_MAIN_GREEN = find_best_green_phase(tlsB, B_MAIN_IN)
    B_SIDE_GREEN = find_best_green_phase(tlsB, B_SIDE_IN)
    B_MAIN_YELLOW = find_yellow_after(tlsB, B_MAIN_GREEN)
    B_SIDE_YELLOW = find_yellow_after(tlsB, B_SIDE_GREEN)

    print("=== AUTO PHASE MAP ===")
    print("A mainG, mainY, sideG, sideY =", A_MAIN_GREEN, A_MAIN_YELLOW, A_SIDE_GREEN, A_SIDE_YELLOW)
    print("B mainG, mainY, sideG, sideY =", B_MAIN_GREEN, B_MAIN_YELLOW, B_SIDE_GREEN, B_SIDE_YELLOW)

    # Başlangıç: ana koridor yeşil
    MODE = "MAIN"
    green_timer = 0
    set_phase_both(tlsA, tlsB, A_MAIN_GREEN, B_MAIN_GREEN)

    # Kuyruk ölçümü için edge listeleri
    MAIN_EDGES = ["A2B", "B2A"]
    SIDE_EDGES = ["A_E2A", "A_W2A", "B_E2B", "B_W2B", "A_N2A", "A_S2A", "B_N2B", "B_S2B"]

    for t in range(SIM_END):
        traci.simulationStep()
        time.sleep(DELAY)

        # 🚑 Ambulans override
        veh_ids = traci.vehicle.getIDList()
        if "ambulance_1" in veh_ids:
            set_phase_both(tlsA, tlsB, A_MAIN_GREEN, B_MAIN_GREEN)
            continue

        main_q = halting_on_edges(MAIN_EDGES)
        side_q = halting_on_edges(SIDE_EDGES)

        green_timer += 1

        if MODE == "MAIN":
            set_phase_both(tlsA, tlsB, A_MAIN_GREEN, B_MAIN_GREEN)

            # side baskınsa geç
            if green_timer >= MIN_GREEN and side_q > main_q + 2:
                set_phase_both(tlsA, tlsB, A_MAIN_YELLOW, B_MAIN_YELLOW)
                for _ in range(YELLOW_TIME):
                    traci.simulationStep()
                    time.sleep(DELAY)
                MODE = "SIDE"
                green_timer = 0
                set_phase_both(tlsA, tlsB, A_SIDE_GREEN, B_SIDE_GREEN)

            elif green_timer >= MAX_GREEN:
                set_phase_both(tlsA, tlsB, A_MAIN_YELLOW, B_MAIN_YELLOW)
                for _ in range(YELLOW_TIME):
                    traci.simulationStep()
                    time.sleep(DELAY)
                MODE = "SIDE"
                green_timer = 0
                set_phase_both(tlsA, tlsB, A_SIDE_GREEN, B_SIDE_GREEN)

        else:
            set_phase_both(tlsA, tlsB, A_SIDE_GREEN, B_SIDE_GREEN)

            if green_timer >= MIN_GREEN and main_q > side_q + 2:
                set_phase_both(tlsA, tlsB, A_SIDE_YELLOW, B_SIDE_YELLOW)
                for _ in range(YELLOW_TIME):
                    traci.simulationStep()
                    time.sleep(DELAY)
                MODE = "MAIN"
                green_timer = 0
                set_phase_both(tlsA, tlsB, A_MAIN_GREEN, B_MAIN_GREEN)

            elif green_timer >= MAX_GREEN:
                set_phase_both(tlsA, tlsB, A_SIDE_YELLOW, B_SIDE_YELLOW)
                for _ in range(YELLOW_TIME):
                    traci.simulationStep()
                    time.sleep(DELAY)
                MODE = "MAIN"
                green_timer = 0
                set_phase_both(tlsA, tlsB, A_MAIN_GREEN, B_MAIN_GREEN)

        if t % 30 == 0:
            print(f"t={t} MODE={MODE} mainQ={main_q} sideQ={side_q}")

    traci.close()
    print("Bitti ✅")

if __name__ == "__main__":
    main()
