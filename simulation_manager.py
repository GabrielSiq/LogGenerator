from model_builder import ModelBuilder


class SimulationManager:
    @staticmethod
    def main():
        model = ModelBuilder()
        model.create_activities()


SimulationManager.main()