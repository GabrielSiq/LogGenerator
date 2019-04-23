from model_builder import ModelBuilder


class SimulationManager:
    @staticmethod
    def main():
        model = ModelBuilder()
        print("\nParsing activities:")
        list_of_activities = model.create_activities()
        for activity in list_of_activities:
            print(activity)
        print("\nParsing resources:")
        list_of_resources = model.create_resources()
        for resource in list_of_resources:
            print(resource)
        print("\nParsing data:")
        list_of_data = model.create_data()
        for data in list_of_data:
            print(data)


SimulationManager.main()
