import cProfile
import pstats
import gui  # Импорт твоего основного модуля

def main():
    app = gui.create_app()
    app.exec_()  # Запуск Qt event loop

if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()
    main()
    profiler.disable()
    
    stats = pstats.Stats(profiler).sort_stats('cumulative')
    stats.print_stats(20)  # Топ 20 по времени
