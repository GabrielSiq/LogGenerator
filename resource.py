from datetime import timedelta, datetime
from abc import ABC, abstractmethod
from calendar import day_name

from duration import Duration


class ResourceManager:

    def __init__(self, resources):
        self.human_resources = []
        self.physical_resources = []
        for resource in resources:
            if isinstance(resource, HumanResource):
                self.human_resources.append(resource)
            elif isinstance(resource, PhysicalResource):
                self.physical_resources.append(resource)

    def _assign_physical(self, resource_id, quantity):
        self.physical_resources[resource_id].use(quantity)
        return True

    def _assign_human(self, resource_id, start_time, duration, process_id, activity_id):
        self.human_resources[resource_id].use(start_time=start_time, duration=duration, process_id=process_id, activity_id=activity_id)
        return True

    def check_availability(self, requirement, start_time, quantity):
        available = self.get_available(requirement, start_time)
        if requirement.class_type == 'physical':
            return sum(x.get_quantity() for x in available) >= quantity
        elif requirement.class_type == 'human':
            return len(available >= quantity)
        else:
            raise ValueError("Resource type not supported.")

    def get_available(self, requirement, start_time):
        return self._search(requirement.class_type, org=requirement.org, dept=requirement.dept, role=requirement.role, physical_type=requirement.physical_type, available=True, start_time=start_time)

    # TODO: IMPORTANT! USE RESOURCEREQUIREMENT CLASS.
    def _search(self, type, org=None, dept=None, role=None, physical_type=None, available=None, start_time=None):
        # TODO: Add to master list of types
        if type == 'physical':
            return self._search_physical(type=physical_type, available=available)
        elif type == 'human':
            return self._search_human(org=org, dept=dept, role=role, available=available, start_time=start_time)

    def _search_physical(self, type, available=None):
        result = []
        for resource in self.physical_resources:
            if resource.type == type and (available is None or (available == True and resource.get_quantity() > 0) or (available == True and resource.get_quantity() == 0)):
                result.append(resource)
        return result

    def _search_human(self, org, dept, role, available=None, start_time=None):
        result = []
        for resource in self.human_resources:
            if (role is None or resource.role == role) and (dept is None or resource.dept == dept) and org is not None and resource.org == org and (available is None or resource.is_available(start_time) == available):
                result.append(resource)
        return result


class ResourceRequirement:

    def __init__(self, class_type, physical_type=None, quantity=None, org=None, dept=None, role=None):
        self.class_type = class_type
        self.physical_type = physical_type
        self.quantity = quantity
        self.org = org
        self.dept = dept
        self.role = role

    @classmethod
    def physical(cls, physical_type, quantity):
        return cls('physical', physical_type=physical_type, quantity=quantity)

    @classmethod
    def human(cls, org, quantity=0, dept=None, role=None):
        if org is None:
            raise ValueError("Organization has to be specified for resource.")
        elif dept is None and role is not None:
            raise ValueError("Role can only be specified within an organization and a department.")
        return cls('human', quantity=quantity, org=org, dept=dept, role=role)

    @classmethod
    def from_list(cls, resource_list):
        if not resource_list:
            return None
        class_list = []
        for item in resource_list:
            if item['class_type'] == 'human':
                class_list.append(cls.human(quantity=item['qty'], org=item['org'], dept=item['dept'], role=item['role']))
            elif item['class_type'] == 'physical':
                class_list.append(cls.physical(physical_type=item['type'], quantity=item['qty']))
            else:
                raise TypeError('Resource class not supported.')
        return class_list

    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class Resource(ABC):
    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class HumanResource(Resource):
    def __init__(self, id, org, dept, role, availability):
        Resource.__init__(self, id)
        self.org = org
        self.dept = dept
        self.role = role
        self.availability = availability
        self.busy = False
        self.busy_until = None
        self.current_process_id = None
        self.current_activity_id = None

    def use(self, start_time, duration, process_id, activity_id):
        end_time = start_time + timedelta(seconds=duration)
        if not self.busy and self.availability.is_available(start_time) and self.availability.available_until(start_time, end_time) >= end_time:
            self.busy = True
            self.busy_until = end_time
            self.current_process_id = process_id
            self.current_activity_id = activity_id
        else:
            raise RuntimeError("Can't use a busy resource")

    def is_available(self, start_time):
        return self.availability.is_available(start_time)


class PhysicalResource(Resource):
    def __init__(self, id, type, quantity, delay):
        Resource.__init__(self, id=id)
        self.type = type
        self.quantity = quantity
        self.delay = Duration(delay)

    def get_quantity(self):
        return self.quantity

    def _add_quantity(self, amount):
        self.quantity += amount
        return True

    def replenish(self, amount):
        if amount >= 0:
            self._add_quantity(amount)
            return True
        else:
            raise ValueError('Amount to replenish needs to be a positive integer.')

    def use(self, amount):
        if 0 <= amount <= self.get_quantity():
            self._add_quantity(-amount)
            return True
        else:
            raise AttributeError("Can't use more than the current quantity")


class Availability:
    def __init__(self, availability):
        self.calendar = availability

    def is_available(self, date_and_time):
        weekday = day_name(date_and_time.weekday())
        hour = datetime.hour
        return hour in self.calendar[weekday].keys()

    def available_until(self, start, end):
        current = start
        while self.is_available(current) and current < end:
            current += timedelta(hours=1)
        return min(current, end)




