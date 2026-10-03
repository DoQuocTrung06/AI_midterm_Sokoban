import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def run_single_player():
    from Task5.ui_single import main
    main()

def run_competitive():
    pass

def run_benchmark():
    from Task3.benchmark import main
    main()

def run_verify_heuristic():
    from Task4.verify_heuristic import main
    main()


if __name__ == "__main__":
    print("================ SOKOBAN AI PROJECT ================\n")
    
    run_single_player()
    
    # run_competitive()
    
    # run_benchmark()
    
    # run_verify_heuristic()

    print("\n==================================================")
