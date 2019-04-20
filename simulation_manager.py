from model_builder import ModelBuilder


class SimulationManager:
    @staticmethod
    def main():
        model = ModelBuilder()
        list_of_activities = model.create_activities()


SimulationManager.main()
