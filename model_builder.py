from typing import Tuple, List, Callable, Union, Optional

from activity import Activity
from transition import Transition
from gateway import Gateway
from process import Process
from config import RESOURCE_TYPES, DATA_TYPES, DEFAULT_PATHS, FILE_ROOT, GATEWAY_TYPES
from resource import HumanResource, PhysicalResource, ResourceManager, Resource
from data import Form, DataManager, DataObject
from xml.etree import ElementTree
from collections import OrderedDict
from copy import deepcopy

# TODO: Implement XML validation.


class ModelBuilder:
    # Initialization and instance variables
    def __init__(self, activities_file: str = DEFAULT_PATHS['activities'], resources_file: str = DEFAULT_PATHS['resources'], data_file: str = DEFAULT_PATHS['data'], models_file: str = DEFAULT_PATHS['models']) -> None:
        self.activities_file = activities_file
        self.resources_file = resources_file
        self.data_file = data_file
        self.models_file = models_file
        self.activities = dict()
        activity_list = self.create_activities()
        self.activities = dict((act.id, act) for act in activity_list)

    # Public methods
    def build_all(self, resource_limit=None) -> Tuple[List[Process], ResourceManager, DataManager]:
        models = self.create_process_model()
        process_list = [x.id for x in models]
        rm = ResourceManager(self.create_resources(resource_limit=resource_limit))
        dm = DataManager(self.create_data(), process_list=process_list)
        return models, rm, dm

    def create_activities(self) -> List[Activity]:
        return self._create_from_file(self.activities_file, FILE_ROOT['activities'], self._parse_activity)

    def create_resources(self, resource_limit=None) -> List[Resource]:
        return self._create_from_file(self.resources_file, FILE_ROOT['resources'], self._parse_resource, extra=resource_limit)

    def create_data(self) -> List[DataObject]:
        return self._create_from_file(self.data_file, FILE_ROOT['data'], self._parse_data)

    def create_process_model(self) -> List[Process]:
        return self._create_from_file(self.models_file, FILE_ROOT['models'], self._parse_process_model)

    # Private methods
    @staticmethod
    def _create_from_file(file_name: str, tag_name: str, parser: Callable, extra=None) -> list:
        container = []
        root = ElementTree.parse(file_name).getroot()
        for child in root:
            if child.tag == tag_name:
                if extra is not None:
                    container.append(parser(child, resource_limit=extra))
                else:
                    container.append(parser(child))

        return container

    def _parse_activity(self, activity_child: ElementTree) -> Activity:
        activity_fields = self._parse_activity_fields(activity_child)

        return Activity(id=activity_fields.get('id'), name=activity_fields.get('name'), distribution=activity_fields.get('distribution', 0), data_input=activity_fields.get('data_input'), data_output=activity_fields.get('data_output'), resources=activity_fields.get('resources'), failure_rate=activity_fields.get('failure_rate', 0), retries=activity_fields.get('retries', 0), timeout=activity_fields.get('timeout'), priority=activity_fields.get('priority', 'normal'))

    def _parse_activity_fields(self, activity_child: ElementTree) -> dict:
        fields = dict()
        fields['id'] = activity_child.get('id')

        try:
            fields['name'] = activity_child.find('Name').text
        except AttributeError:
            pass

        duration_child = activity_child.find('Duration/')
        distribution_child = activity_child.find('Duration/Distribution')
        if distribution_child is not None:
            fields['distribution'] = self._parse_distribution(distribution_child)
        elif duration_child is not None:
            fields['distribution'] = int(duration_child.text)

        data_input = []
        data_input_child = activity_child.find('DataInput')

        if data_input_child is not None:
            for data_object in data_input_child:
                data = dict()
                id = data_object.get('id')
                if id is None:
                    raise AttributeError('Missing data object id.')
                data['id'] = id
                if data_object.get('type') == 'form':
                    fields_child = data_object.find('Fields')
                    if fields_child is not None:
                        data['fields'] = list()
                        for field in fields_child:
                            data['fields'].append(field.get('name'))
                data_input.append(data)
            fields['data_input'] = data_input

        data_output = []
        data_output_child = activity_child.find('DataOutput')

        if data_output_child is not None:
            for data_object in data_output_child:
                data = dict()
                id = data_object.get('id')
                if id is None:
                    raise AttributeError('Missing data object id.')
                data['id'] = id
                if data_object.get('type') == 'form':
                    fields_child = data_object.find('Fields')
                    if fields_child is not None:
                        data['fields'] = list()
                        for field in fields_child:
                            data['fields'].append(field.get('name'))
                data_output.append(data)
            fields['data_output'] = data_output

        resources = []
        resources_child = activity_child.find('Resources')

        if resources_child is not None:
            for resource in resources_child:
                # TODO: Adapt for multi-resource.
                try:
                    res = resource.attrib
                    res['qty'] = int(resource.text)
                    resources.append(res)
                except AttributeError:
                    print('Poorly formatted resource')
            fields['resources'] = resources

        failure_child = activity_child.find('FailureRate')

        if failure_child is not None:
            failure_rate = failure_child.text
            retries = failure_child.get('retries')
            fields['failure_rate'] = float(failure_rate)
            fields['retries'] = int(retries)
        try:
            fields['timeout'] = int(activity_child.find('Timeout').text)
        except AttributeError:
            pass

        try:
            fields['priority'] = activity_child.find('Priority').text
        except AttributeError:
            pass

        return fields

    def _parse_resource(self, resource_child: ElementTree, resource_limit=None) -> Resource:
        class_type = resource_child.get('type')
        id = resource_child.get('id')
        if resource_limit is not None and id in resource_limit:
            qty = int(resource_limit[id])
        else:
            qty = int(resource_child.find('Quantity').text)

        if class_type == RESOURCE_TYPES['human']:
            org = resource_child.find('Organization').text
            dept = resource_child.find('Department').text
            role = resource_child.find('Role').text
            availability = self._parse_calendar(resource_child.find('Availability'))
            res = []
            for i in range(qty):
                res.append(HumanResource(id + "_" + str(i), org, dept, role, availability))
        elif class_type == RESOURCE_TYPES['physical']:
            type = resource_child.find('Type').text
            duration_child = resource_child.find('Duration')
            distribution_child = resource_child.find('Duration/Distribution')
            if distribution_child is not None:
                delay = self._parse_distribution(distribution_child)
            else:
                delay = int(duration_child.text) if duration_child is not None else 0
            cons = True if resource_child.get('consumable').lower() == "true" else False
            res = PhysicalResource(id, type, qty, delay, cons)

        else:
            raise AttributeError("Resource type %s not supported." % class_type)
        return res

    @staticmethod
    def _parse_distribution(distribution_child: ElementTree) -> Optional[dict]:
        if distribution_child is None:
            return None
        try:
            attributes = distribution_child.attrib
            [attributes.update({key: int(value)}) for key, value in attributes.items() if key != 'type']
            return attributes
        except AttributeError:
            print('Poorly formatted duration.')

    @staticmethod
    def _parse_calendar(availability_child: ElementTree) -> dict:
        calendar = dict()
        for day in availability_child:
            for block in day:
                for time in range(int(block.get('start')), int(block.get('end'))):
                    calendar.setdefault(day.tag, {})
                    calendar[day.tag][time] = int(block.text) if block.text is not None else True
        return calendar

    def _parse_process_model(self, model_child: ElementTree) -> Process:
        id = model_child.get('id')
        name = model_child.find('Name').text
        arrival_rate = self._parse_calendar(model_child.find('ArrivalRate'))
        deadline = model_child.find('Deadline').text
        gateways = []
        for gateway in model_child.find('Gateways'):
            gateways.append(self._parse_gateway(gateway))
        transitions = []
        activities = dict()
        resources = list()  # currently unused
        data_objects = dict()
        for transition in model_child.find('Transitions'):
            transition_object = self._parse_transition(transition)
            transitions.append(transition_object)
            # parse activity from transitions
            if transition_object.source not in activities:
                source = self._clone_activity(transition_object.source)
                if source is not None:
                    activities[source.id] = source
                    resources, data_objects = self._parse_from_existing(source, resources, data_objects)
            if transition_object.destination not in activities:
                destination = self._clone_activity(transition_object.destination)
                if destination is not None:
                    activities[destination.id] = destination
                    resources, data_objects = self._parse_from_existing(destination, resources, data_objects)
        for act in model_child.find('Activities'):
            fields = self._parse_activity_fields(act)
            activities[fields['id']].update(fields)
        return Process(id=id, name=name, arrival_rate=arrival_rate, deadline=deadline, activities=activities, gateways=gateways, transitions=transitions, data_objects=list(data_objects.values()))

    @staticmethod
    def _parse_from_existing(item: Activity, resources: list, data_objects: dict) -> Tuple[list, dict]:
        for resource in (item.resources or []):
            resources.append(resource)
        for data_object in (item.data_input or []):
            data_objects[data_object.id] = data_object
        for data_object in (item.data_output or []):
            data_objects[data_object.id] = data_object
        return resources, data_objects

    @staticmethod
    def _parse_gateway(gateway_child: ElementTree) -> Gateway:
        id = gateway_child.get('id')
        name = gateway_child.find('Name').text
        type = gateway_child.find('Type').text.lower()
        gates = []
        distribution = None
        rule = None
        if type == GATEWAY_TYPES['choice']:
            distribution_child = gateway_child.find('Distribution')
            rule_child = gateway_child.find('Rule')
            if distribution_child is not None and len(list(distribution_child)):
                distribution = []
                for gate in distribution_child:
                    gates.append(gate.get('id'))
                    distribution.append(float(gate.text))
            elif rule_child is not None and len(list(rule_child)):
                for gate in rule_child:
                    gates.append(gate.get('id'))
                rule = id
            else:
                raise ValueError("For choice gateways, either rule or distribution must be present.")
        elif type == GATEWAY_TYPES['parallel'] or type == GATEWAY_TYPES['merge']:
            gates_child = gateway_child.find('Gates')
            for gate in gates_child:
                gates.append(gate.get('id'))
        return Gateway(id=id, name=name, type=type, gates=gates, distribution=distribution, rule=rule)

    def _parse_transition(self, transition_child: ElementTree) -> Transition:
        source = transition_child.get('source')
        destination = transition_child.get('destination')
        sgate = transition_child.get('source_gate')
        dgate = transition_child.get('destination_gate')
        duration_child = transition_child.find('Duration')
        distribution_child = transition_child.find('Duration/Distribution')
        if distribution_child is not None:
            distribution = self._parse_distribution(distribution_child)
        else:
            distribution = int(duration_child.text) if duration_child is not None else 0

        return Transition(source=source, destination=destination, sgate=sgate, dgate=dgate, distribution=distribution)

    def _parse_data(self, data_child: ElementTree) -> DataObject:
        id = data_child.get('id')
        type = data_child.get('type')

        if type == DATA_TYPES['form']:
            name, fields = self._parse_form(data_child)
            return Form(id, name, fields)
        else:
            raise ValueError('Data type %s not supported.' % type)

    @staticmethod
    def _parse_form(form_child: ElementTree) -> Tuple[str, OrderedDict]:
        name = form_child.find('Name').text
        fields = OrderedDict()
        for field in form_child.find('Fields'):
            fields[field.get('name')] = field.text
        return name, fields

    def _clone_activity(self, id: str) -> Optional[Activity]:
        if id not in self.activities:
            return None
        else:
            return deepcopy(self.activities[id])
        pass

























