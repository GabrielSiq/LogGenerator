from activity import Activity
import xml.etree.ElementTree as ET


class ModelBuilder:

    @classmethod
    def create_activities(cls):
        activities = []
        source = ET.parse('activities.xml')
        root = source.getroot()
        for child in root:
            if child.tag == 'Activity':
                activities.append(cls._parse_activity(child))
        return activities

    @classmethod
    def _parse_activity(cls, activity):
        activity_id = activity.get('id')

        try:
            name = activity.find('Name').text
        except AttributeError:
            print('No name was informed.')

        try:
            distribution_child = activity.find('Duration/Distribution')
            distribution = distribution_child.attrib
            # TODO: Think of case when the duration is fixed and not a distribution.
        except AttributeError:
            print('Poorly formatted duration.')

        data_input = []
        data_input_child = activity.find('DataInput')
        # TODO: Add some checking to verify that the children objects are what we think they are.
        if data_input_child is not None:
            for data_object in data_input_child:
                id = data_object.get('id')
                if id is None:
                    # TODO: better way to handle custom exception
                    print('Missing data object id.')
                    raise AttributeError
                data_input.append(data_object.get('id'))

        data_output = []
        data_output_child = activity.find('DataOutput')

        if data_output_child is not None:
            for data_object in data_output_child:
                id = data_object.get('id')
                if id is None:
                    # TODO: better way to handle custom exception
                    print('Missing data object id.')
                    raise AttributeError
                data_output.append(data_object.get('id'))

        resources = []
        resources_child = activity.find('Resources')

        if resources_child is not None:
            for resource in resources_child:
                # TODO: Change resources to be more flexible. We need to accept subtypes of resources and etc. For now we specify one type of resource.
                try:
                    res = resource.attrib
                    res['qty'] = resource.text
                    resources.append(res)
                except AttributeError:
                    print('Poorly formatted resource')

        failure_rate = None
        retries = None
        failure_child = activity.find('FailureRate')

        if failure_child is not None:
            failure_rate = failure_child.text
            retries = failure_child.get('retries')

        # TODO: implement similar try/except methodology for others.
        try:
            timeout = activity.find('Timeout').text
        except AttributeError:
            timeout = None

        try:
            priority = activity.find('Priority').text
        except AttributeError:
            priority = None

        return Activity(id=activity_id, name=name, distribution=distribution, data_input=data_input, resources=resources, failure_rate=failure_rate, retries=retries, timeout=timeout, priority=priority)

    @classmethod
    def create_resources(cls):
        resources = []
        source = ET.parse('resources.xml')
        root = source.getroot()
        for child in root:
            if child.tag == 'Resource':
                resources.append(cls._parse_resource(child))
        return resources
















