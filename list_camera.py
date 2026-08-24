from nonmouse.camera import list_cameras

if __name__ == "__main__":
    cameras = list_cameras()
    if not cameras:
        print("Nenhuma camera encontrada.")
    else:
        print(f"{'Idx':<5} {'Backend':<8} {'Resolucao':<12} {'FPS'}")
        print("-" * 35)
        for c in cameras:
            fps_str = str(int(c["fps"])) if c["fps"] > 0 else "N/A"
            print(f"{c['index']:<5} {c['backend']:<8} {c['res']:<12} {fps_str}")
