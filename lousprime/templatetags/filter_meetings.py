from django import template

register = template.Library()

def filter_meetings(value):
    """Convert meeting string to a list of meeting times and locations"""
    # example meetings string: TuTh, 12:00PM - 1:50PM, Olsson 204; Tu, 6:30PM - 8:30PM, Thornton D208
    meetings = value.split(";")
    separated_meetings = [tuple(m.split(",")) for m in meetings]
    return separated_meetings

register.filter('filter_meetings', filter_meetings)