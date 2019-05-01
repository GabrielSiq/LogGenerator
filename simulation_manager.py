from data_object import DataManager
from model_builder import ModelBuilder
from resource import ResourceManager
from datetime import datetime, timedelta


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
        print("\nParsing models:")
        list_of_models = model.create_process_model()
        for process in list_of_models:
            print(process)
        print("\nTesting data manager:")
        dm = DataManager(list_of_data)
        rm = ResourceManager(list_of_resources)

        req = model.activities['quality'].resources[0]

        print(rm.get_available(req, datetime.now() - timedelta(hours=3), datetime.now() - timedelta(hours=2)))



SimulationManager.main()
