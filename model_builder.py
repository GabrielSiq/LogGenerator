from activity import Activity
from resource import HumanResource, PhysicalResource
from data_object import Form
from xml.etree import ElementTree
from collections import OrderedDict


class ModelBuilder:
    @classmethod
    def create_activities(cls):
        # TODO: Add the file locations to some configuration that the model builder accesses
        return cls._create_from_file('activities.xml', 'Activity', cls._parse_activity)

    @classmethod
    def create_resources(cls):
        # TODO: Add the file locations to some configuration that the model builder accesses
        return cls._create_from_file('resources.xml', 'Resource', cls._parse_resource)

    @classmethod
    def create_data(cls):
        # TODO: Add the file locations to some configuration that the model builder accesses
        return cls._create_from_file('data.xml', 'DataObject', cls._parse_data)

    @classmethod
    def create_process_model(cls):
        # TODO: Add the file locations to some configuration that the model builder accesses
        return cls._create_from_file('models.xml', 'Model', cls._parse_process_model)

    @classmethod
    def _create_from_file(cls, file_name, tag_name, parser):
        container = []
        root = ElementTree.parse(file_name).getroot()
        for child in root:
            if child.tag == tag_name:
                container.append(parser(child))
        return container

    @classmethod
    def _parse_activity(cls, activity):
        activity_id = activity.get('id')

        name = activity.find('Name').text

        distribution = cls._parse_distribution(activity.find('Duration/Distribution'))

        data_input = []
        data_input_child = activity.find('DataInput')
        # TODO: Add some checking to verify that the children objects are what we think they are.
        if data_input_child is not None:
            for data_object in data_input_child:
                id = data_object.get('id')
                if id is None:
                    # TODO: better way to handle custom exception
                    raise AttributeError('Missing data object id.')
                data_input.append(data_object.get('id'))

        data_output = []
        data_output_child = activity.find('DataOutput')

        if data_output_child is not None:
            for data_object in data_output_child:
                id = data_object.get('id')
                if id is None:
                    # TODO: better way to handle custom exception
                    raise AttributeError('Missing data object id.')

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

        return Activity(id=activity_id, name=name, distribution=distribution, data_input=data_input, data_output=data_output, resources=resources, failure_rate=failure_rate, retries=retries, timeout=timeout, priority=priority)

    @classmethod
    def _parse_resource(cls, resource):
        class_type = resource.get('type')
        id = resource.get('id')
        qty = resource.find('Quantity').text

        if class_type == 'human':
            org = resource.find('Organization').text
            dept = resource.find('Department').text
            role = resource.find('Role').text
            availability = cls._parse_availability(resource.find('Availability'))
            res = HumanResource(id, org, dept, role, availability)
        elif class_type == 'physical':
            type = resource.find('Type').text
            delay = cls._parse_distribution(resource.find('Delay/Distribution'))
            res = PhysicalResource(id, type, qty, delay)
        else:
            raise AttributeError('Poorly formatted resource.')
        return res

    @classmethod
    def _parse_distribution(cls, distribution_child):
        try:
            return distribution_child.attrib
            # TODO: Think of case when the duration is fixed and not a distribution.
        except AttributeError:
            print('Poorly formatted duration.')

    @classmethod
    def _parse_availability(cls, availability_child):
        calendar = {}
        for day in availability_child:
            for block in day:
                for time in range(int(block.get('start')), int(block.get('end'))):
                    calendar.setdefault(day.tag, {})
                    calendar[day.tag][time] = True
        return calendar

    @classmethod
    def _parse_process_model(cls, model_child):
        pass

    @classmethod
    def _parse_data(cls, data_child):
        id = data_child.get('id')
        type = data_child.get('type')

        if type == 'form':
            name, fields = cls._parse_form(data_child)
            return Form(id, name, fields)
        else:
            raise ValueError('Data type not supported.')

    @classmethod
    def _parse_form(cls, form_child):
        # TODO: This is the model going forward. Do NO verification on format and do xml validation on initialization.
        name = form_child.find('Name').text
        fields = OrderedDict()
        for field in form_child.find('Fields'):
            fields[field.get('name')] = field.text
        return name, fields

























