from model_builder import ModelBuilder


class SimulationManager:
    @staticmethod
    def main():
        model = ModelBuilder()
        list_of_activities = model.create_activities()
        for activity in list_of_activities:
            print(activity)

        list_of_resources = model.create_resources()
        for resource in list_of_resources:
            print(resource)


SimulationManager.main()
