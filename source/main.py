import sys
import os

# Đảm bảo Python nhận diện các module trong cùng thư mục 'source'
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def run_single_player():
    """Run Task 5: Single Player Sokoban GUI (Using UCS and A*)"""
    from Task5.ui_single import SokobanGUI
    map_file = os.path.join(current_dir, "maps", "example_map.txt")
    print("=> Running Task 5: Single Player Mode...")
    game = SokobanGUI(map_file)
    game.run()

def run_competitive():
    """Run Task 6: Two Player Competitive GUI"""
    # TODO: Dành cho thành viên phụ trách Task 6 tự code và gọi giao diện
    pass

def run_benchmark():
    """Run Task 3: Evaluate and compare time/space performance of UCS vs A*"""
    from Task3.benchmark import main
    main()

def run_verify_heuristic():
    """Run Task 4: Verify Admissible and Consistent properties of Heuristic"""
    from Task4.verify_heuristic import main
    main()


if __name__ == "__main__":
    print("================ SOKOBAN AI PROJECT ================\n")
    
    run_single_player()      # Task 5: Giao diện 1 người (đã hoàn thiện)
    
    # run_competitive()        # Task 6: Giao diện đối kháng 2 người
    
    # run_benchmark()          # Task 3: Script benchmark UCS vs A*
    
    # run_verify_heuristic()   # Task 4: Script kiểm tra Heuristic

    print("\n==================================================")
