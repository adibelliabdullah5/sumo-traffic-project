import sumolib

NET = "network_multi.net.xml"

def shortest(from_edge_id, to_edge_id):
    net = sumolib.net.readNet(NET)

    fe = net.getEdge(from_edge_id)
    te = net.getEdge(to_edge_id)

    path, cost = net.getShortestPath(fe, te)
    if not path:
        print("NO PATH")
        return

    ids = [e.getID() for e in path]
    print("PATH EDGES:")
    print(" ".join(ids))
    print("COST:", cost)

if __name__ == "__main__":
    # Ambulansın nereden başlayıp nereye gideceğini buradan seçiyoruz:
    shortest("A_W2A", "B_E2B")
