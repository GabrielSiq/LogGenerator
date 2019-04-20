from activity import Activity
import xml.etree.ElementTree as ET


class ModelBuilder:

    @classmethod
    def create_activities(cls):
        source = ET.parse('activities.xml')
        root = source.getroot()
        for child in root:
            if child.tag == 'Activity':
                cls._parse_activity(child)

    def _parse_activity(activity):
        id = activity.get('id')

        try:
            name = activity.find('Name').text
        except AttributeError:
            print('No name was informed.')

        try:
            distributionChild = activity.find('Duration/Distribution')
            distribution = distributionChild.attrib
        except AttributeError:
            print('Poorly formatted duration.')







