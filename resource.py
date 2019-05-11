from __future__ import annotations
from datetime import timedelta, datetime
from heapq import heappush, heappop
from typing import List, Union, Tuple, Dict, Optional
from config import RESOURCE_TYPES, DAYS
from duration import Duration


class ResourceManager:
    # Initialization and instance variables
    def __init__(self, resources: List[Resource]) -> None:
        self.human_resources = dict()
        self.physical_resources = dict()
        for resource in resources:
            if isinstance(resource, HumanResource):
                self.human_resources[resource.id] = resource
            elif isinstance(resource, PhysicalResource):
                self.physical_resources[resource.id] = resource

    # Public methods

    def assign_resources(self, requirement_list: List[ResourceRequirement], process_id: str, process_instance_id: int, activity_id: str, activity_instance_id: int, start_time: datetime = None, duration: int = None) -> Tuple[datetime, Dict[str, int]]:
        # TODO: Implement the case when there are more than one requirement. Does it mean one or another or does it mean multiple? This is a modeling question that needs to be answered. (2h)
        for requirement in requirement_list:
            return self.assign_resource(requirement, process_id, process_instance_id, activity_id, activity_instance_id, start_time, duration)

    def assign_resource(self, requirement: ResourceRequirement, process_id: str, process_instance_id: int, activity_id: str, activity_instance_id: int, start_time: datetime = None, duration: int = None) -> Tuple[datetime, Dict[str, int]]:
        if duration is None:
            return self._assign_physical(requirement, start_time=start_time, duration=duration)
        else:
            return self._assign_human(requirement, process_id, process_instance_id, activity_id, activity_instance_id, start_time, duration)

    def check_availability(self, requirement: ResourceRequirement, start_time: datetime, end_time: datetime) -> bool:
        available = self.get_available(requirement, start_time, end_time)
        if requirement.class_type == RESOURCE_TYPES['physical']:
            return sum(x.get_quantity() for x in available) >= requirement.quantity
        elif requirement.class_type == RESOURCE_TYPES['human']:
            return len(available) >= requirement.quantity
        else:
            raise ValueError("Resource type %s not supported." % requirement.class_type)

    def get_available(self, requirement: ResourceRequirement, start_time: datetime = None, end_time: datetime = None) -> List[Resource]:
        return self._search(requirement.class_type, org=requirement.org, dept=requirement.dept, role=requirement.role, physical_type=requirement.physical_type, available=True, start_time=start_time, end_time=end_time, amount=requirement.quantity)

    def when_available(self, requirement_list: List[ResourceRequirement], start_time: datetime = None, end_time: datetime = None) -> List[datetime]:
        # TODO: What about physical resources? The same logic doesn't apply... (2h)
        requirement = requirement_list[0]
        # TODO: Handle more than one resource here as well... (2h)
        resources = self._search(requirement.class_type, org=requirement.org, dept=requirement.dept, role=requirement.role, physical_type=requirement.physical_type, available=False, start_time=start_time, end_time=end_time, amount=requirement.quantity)
        return sorted(resources, key=lambda x: x.when_available(start_time))[0].when_available(start_time)

    # Private methods
    def _assign_human(self, requirement: ResourceRequirement, process_id: str, process_instance_id: int, activity_id: str, activity_instance_id: int, start_time: datetime, duration: int) -> Tuple[datetime, Dict[str, int]]:
        # Assigns any necessary number of human resources to a process based on the given requirement. If resources are not available durint the full duration of the activity, assigns them anyway but returns the expiration date.
        result = {}
        max_date = datetime.min
        if self.check_availability(requirement, start_time, end_time=start_time + timedelta(seconds=duration)) is True:
            available = self.get_available(requirement, start_time=start_time, end_time=start_time + timedelta(seconds=duration))
            max_date = available[requirement.quantity - 1].available_until(start_time, start_time + timedelta(seconds=duration))
            for i in range(requirement.quantity):
                result.update(self._assign_individual_human(available[i].id, start_time, (max_date - start_time).total_seconds(), process_id, process_instance_id, activity_id, activity_instance_id))
        return max_date, result

    def _assign_physical(self, requirement: ResourceRequirement, start_time: datetime = None, duration: int = None) -> Tuple[datetime, Dict[str, int]]:
        # Assigns any necessary number of physical resources to a process. Resources can be consumable or not.
        available = self.get_available(requirement, start_time=start_time, end_time=start_time + timedelta(seconds=duration))
        result = {}
        left = requirement.quantity
        while left > 0:
            resource = next(available)
            a_quantity = min(left, resource.get_quantity())
            result.update(self._assign_individual_physical(resource.id, a_quantity, start_time=start_time, end_time=start_time + timedelta(seconds=duration)))
            left -= a_quantity
        return start_time+timedelta(seconds=duration), result

    def _assign_individual_physical(self, resource_id: str, quantity: int, start_time: datetime = None, end_time: datetime = None) -> Dict[str, int]:
        self.physical_resources[resource_id].use(quantity, start_time=start_time, end_time=end_time)
        return {resource_id: quantity}

    def _assign_individual_human(self, resource_id: str, start_time: datetime, duration: int, process_id: str, process_instance_id: int, activity_id: str, activity_instance_id: int) -> Dict[str, int]:
        self.human_resources[resource_id].use(start_time=start_time, duration=duration, process_id=process_id, process_instance_id=process_instance_id, activity_id=activity_id, activity_instance_id=activity_instance_id)
        return {resource_id: 1}

    def _search(self, type: str, org: str = None, dept: str = None, role: str = None, physical_type: str = None, available: bool = None, start_time: datetime = None, end_time: datetime = None, amount: int = 0) -> List[Resource]:
        if type == RESOURCE_TYPES['physical']:
            return self._search_physical(type=physical_type, available=available, start_time=start_time, amount=amount)
        elif type == RESOURCE_TYPES['human']:
            return self._search_human(org=org, dept=dept, role=role, available=available, start_time=start_time, end_time=end_time)
        else:
            raise ValueError("Resource type %s not supported." % type)

    def _search_physical(self, type: str, start_time: datetime, amount: int, available: bool = None) -> List[Resource]:
        result = []
        for id, resource in self.physical_resources.items():
            if resource.type == type and (available is None or (available is True and resource.check_free(start_time, amount) > 0) or (available is False and resource.check_free(start_time, amount) == 0)):
                result.append(resource)
        return sorted(result, key=lambda x: x.check_free(start_time, amount), reverse=True)

    def _search_human(self, org: str, dept: str, role: str, available: bool = None, start_time: datetime = None, end_time: datetime = None) -> List[Resource]:
        result = []
        for id, resource in self.human_resources.items():
            if (role is None or resource.role == role) and (dept is None or resource.dept == dept) and org is not None and resource.org == org and (available is None or resource.is_available(start_time) == available):
                result.append(resource)
        return sorted(result, key=lambda x: x.available_until(start_time, end_time), reverse=True)


class ResourceRequirement:
    # Initialization and instance variables
    def __init__(self, class_type: str, physical_type: str = None, quantity: int = None, org: str = None, dept: str = None, role: str = None) -> None:
        self.class_type = class_type
        self.physical_type = physical_type
        self.quantity = quantity
        self.org = org
        self.dept = dept
        self.role = role

    # Public methods
    @classmethod
    def physical(cls, physical_type: str, quantity: int) -> ResourceRequirement:
        return cls(RESOURCE_TYPES['physical'], physical_type=physical_type, quantity=quantity)

    @classmethod
    def human(cls, org: str, quantity: int = 0, dept: str = None, role: str = None) -> ResourceRequirement:
        if org is None:
            raise ValueError("Organization has to be specified for resource.")
        elif dept is None and role is not None:
            raise ValueError("Role can only be specified within an organization and a department.")
        return cls(RESOURCE_TYPES['human'], quantity=quantity, org=org, dept=dept, role=role)

    @classmethod
    def from_list(cls, resource_list: List[dict]) -> Optional[List[ResourceRequirement]]:
        if not resource_list:
            return None
        class_list = []
        for item in resource_list:
            if item['class_type'] == RESOURCE_TYPES['human']:
                class_list.append(cls.human(quantity=item['qty'], org=item['org'], dept=item['dept'], role=item['role']))
            elif item['class_type'] == RESOURCE_TYPES['physical']:
                class_list.append(cls.physical(physical_type=item['type'], quantity=item['qty']))
            else:
                raise TypeError('Resource class %s not supported.' % item['class_type'])
        return class_list

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class Resource:
    # Initialization and instance variables
    def __init__(self, id: str) -> None:
        self.id = id

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())


class HumanResource(Resource):
    # Initialization and instance variables
    def __init__(self, id: str, org: str, dept: str, role: str, availability: dict) -> None:
        Resource.__init__(self, id)
        self.org = org
        self.dept = dept
        self.role = role
        self.availability = Availability(availability)
        self.busy_until = datetime(1, 1, 1, 0, 0)
        self.current_process_id = None
        self.current_process_instance_id = None
        self.current_activity_id = None
        self.current_activity_instance_id = None

    # Public methods
    def use(self, start_time: datetime, duration: int, process_id: str, process_instance_id: int, activity_id: str, activity_instance_id: int) -> None:
        end_time = start_time + timedelta(seconds=duration)
        if self.busy_until <= start_time and self.availability.is_available(start_time) and self.availability.available_until(start_time, end_time) >= end_time:
            self.busy_until = end_time
            self.current_process_id = process_id
            self.current_process_instance_id = process_instance_id
            self.current_activity_id = activity_id
            self.current_activity_instance_id = activity_instance_id
        else:
            raise RuntimeError("Resource %s is busy and cannot be used." % self.id)

    def is_available(self, start_time: datetime) -> bool:
        return self.busy_until < start_time and self.availability.is_available(start_time)

    def available_until(self, start: datetime, end: datetime) -> datetime:
        if self.is_available(start):
            return self.availability.available_until(start, end)
        else:
            return datetime.min

    def when_available(self, start: datetime) -> datetime:
        if self.busy_until > start:
            start = self.busy_until
            if self.is_available(start):
                return start
        current = start.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        while not self.is_available(current):
            current += timedelta(hours=1)
        return current


class PhysicalResource(Resource):
    # Initialization and instance variables
    # TODO: come up with example and also implement in simulation the ordering of new materials. (3h)
    def __init__(self, id: str, type: str, quantity: int, delay: Union[dict, int], consumable: bool) -> None:
        Resource.__init__(self, id=id)
        self.type = type
        self.quantity = quantity
        self.busy = []
        self.delay = Duration(delay)
        self.consumable = consumable

    # Public methods
    def get_quantity(self) -> int:
        return self.quantity

    def replenish(self, amount: int) -> bool:
        if amount >= 0:
            self._add_quantity(amount)
            return True
        else:
            raise ValueError('Amount to replenish needs to be a positive integer.')

    def use(self, amount: int, start_time: datetime = None, end_time: datetime = None) -> int:
        if 0 <= amount <= self.get_quantity() or (self.consumable is False and self.check_free(start_time, amount,
                                                                                               True) == amount):
            self._add_quantity(-amount)
            if self.consumable is False:
                heappush(self.busy, (end_time, amount))
            return amount
        else:
            raise AttributeError("Can't use more than the current quantity")

    def check_free(self, start_time: datetime, amount: int, free: bool = False) -> int:
        # Checks the amount of free resources at a specific time, up to a certain maximum amount desired. If free is True, also free the resources for use.
        next = heappop(self.busy) # Gets the first batch of resources to become free
        refund = 0 # sometimes we don't need to free the entire batch, only a bit
        current = self.get_quantity() # the amount currently in stock
        needed = amount - current # how much we need to free to satisfy the requirement
        used = []
        while next is not None and next[0] <= start_time and needed > 0:
            # Until we're out of resources to free, reach a resource that won't be available at our start time and still need to free more resources, go through resources counting how much we can free.
            used.append(next)
            refund = next[1] - min(next[1], needed)
            needed -= min(next[1], needed)
            next = heappop(self.busy)
        if next is not None:
            # Add the unused item back to the pile.
            heappush(self.busy, next)
        if needed > 0 or free is False:
            # If we aren't able to reach what we need or we don't want to free the resources, push them back into the pile.
            for item in used:
                heappush(self.busy, item)
        elif needed == 0:
            # If we reach the amount we needed to free, add it to our total and add back any unnecessarily free amount.
            self.replenish(amount - current)
            if refund != 0:
                heappush(self.busy, (used.pop()[0], refund))
        return amount - max(needed, 0)

    # Private methods
    def _add_quantity(self, amount: int) -> bool:
        self.quantity += amount
        return True


class Availability:
    # Initialization and instance variables
    def __init__(self, availability: dict) -> None:
        self.calendar = availability

    # Public methods
    def is_available(self, date_and_time: datetime) -> bool:
        weekday = DAYS[date_and_time.weekday()]
        hour = date_and_time.hour
        if weekday in self.calendar:
            return hour in self.calendar[weekday].keys()
        else:
            return False

    def available_until(self, start: datetime, end: datetime) -> datetime:
        if not self.is_available(start):
            return start
        current = start
        while self.is_available(current) and current < end:
            current += timedelta(hours=1)
        current = current.replace(microsecond=0, second=59, minute=59)
        return min(current, end)

    # Private methods
    def __repr__(self):
        return ', '.join("%s: %s" % item for item in vars(self).items())



